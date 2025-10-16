"""
Entity Validator for GraphRAG Indexing Output
==============================================

Validates entity descriptions against source text using three methods:
1. Groq API (SelfCheckGPT-Prompt variant) - Fast, accurate, costs ~$1.17 for 1169 entities
2. GPU NLI (SelfCheckGPT-NLI variant) - Free, accurate if GPU available
3. Hybrid (Text matching + Groq spot checks) - Best cost/speed balance at ~$0.23

Usage:
    python entity_validator.py --method groq --limit 100
    python entity_validator.py --method gpu --all
    python entity_validator.py --method hybrid --resume
"""

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from tqdm import tqdm


@dataclass
class ValidationResult:
    """Result of entity validation"""
    entity_id: str
    entity_name: str
    entity_type: str
    description: str
    confidence: float  # 0-1, higher = more likely hallucinated
    is_hallucinated: bool
    method: str
    issues: List[str]
    validation_time: float


class EntityValidator:
    """Base validator class"""
    
    def __init__(self, graphrag_output_dir: str, cache_dir: str = "validation_cache"):
        self.output_dir = Path(graphrag_output_dir)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Load data
        print("Loading GraphRAG data...")
        self.entities_df = pd.read_parquet(self.output_dir / "entities.parquet")
        self.text_units_df = pd.read_parquet(self.output_dir / "text_units.parquet")
        
        print(f"Loaded {len(self.entities_df)} entities and {len(self.text_units_df)} text units")
        
        # Build text unit lookup
        self.text_unit_map = {
            row['id']: row['text'] 
            for _, row in self.text_units_df.iterrows()
        }
        
    def get_source_texts(self, entity_row) -> List[str]:
        """Get source text chunks for an entity"""
        text_unit_ids = entity_row['text_unit_ids']
        if isinstance(text_unit_ids, str):
            text_unit_ids = json.loads(text_unit_ids)
        
        texts = []
        for tid in text_unit_ids:
            if tid in self.text_unit_map:
                texts.append(self.text_unit_map[tid])
        
        return texts
    
    def validate_entity(self, entity_row) -> ValidationResult:
        """Override in subclass"""
        raise NotImplementedError
    
    def validate_batch(self, limit: Optional[int] = None, resume: bool = False) -> List[ValidationResult]:
        """Validate entities with progress tracking and resume capability"""
        results = []
        results_file = self.cache_dir / "validation_results.json"
        
        # Load existing results if resuming
        processed_ids = set()
        if resume and results_file.exists():
            with open(results_file, 'r') as f:
                cached = json.load(f)
                results = [ValidationResult(**r) for r in cached]
                processed_ids = {r.entity_id for r in results}
                print(f"Resuming: {len(processed_ids)} entities already validated")
        
        # Determine which entities to process
        entities_to_process = self.entities_df[
            ~self.entities_df['id'].isin(processed_ids)
        ]
        
        if limit:
            entities_to_process = entities_to_process.head(limit)
        
        print(f"Validating {len(entities_to_process)} entities...")
        
        # Process with progress bar
        for idx, row in tqdm(entities_to_process.iterrows(), 
                            total=len(entities_to_process),
                            desc="Validating entities"):
            try:
                result = self.validate_entity(row)
                results.append(result)
                
                # Save checkpoint every 10 entities
                if len(results) % 10 == 0:
                    self._save_results(results, results_file)
                    
            except Exception as e:
                print(f"\nError validating entity {row['title']}: {e}")
                continue
        
        # Final save
        self._save_results(results, results_file)
        
        return results
    
    def _save_results(self, results: List[ValidationResult], filepath: Path):
        """Save results to JSON"""
        with open(filepath, 'w') as f:
            json.dump([r.__dict__ for r in results], f, indent=2)
    
    def generate_report(self, results: List[ValidationResult], output_file: str = "validation_report.csv"):
        """Generate CSV report from validation results"""
        df = pd.DataFrame([r.__dict__ for r in results])
        df['issues'] = df['issues'].apply(lambda x: '; '.join(x) if x else '')
        df.to_csv(output_file, index=False)
        
        print(f"\n{'='*60}")
        print(f"VALIDATION REPORT")
        print(f"{'='*60}")
        print(f"Total entities validated: {len(results)}")
        print(f"Hallucinated entities: {sum(r.is_hallucinated for r in results)} ({100*sum(r.is_hallucinated for r in results)/len(results):.1f}%)")
        print(f"Average confidence: {sum(r.confidence for r in results)/len(results):.3f}")
        print(f"Total validation time: {sum(r.validation_time for r in results):.1f}s")
        print(f"Average time per entity: {sum(r.validation_time for r in results)/len(results):.2f}s")
        print(f"\nReport saved to: {output_file}")
        print(f"{'='*60}\n")
        
        # Show top hallucinated entities
        hallucinated = [r for r in results if r.is_hallucinated]
        if hallucinated:
            print("\nTop 10 Most Confident Hallucinations:")
            hallucinated.sort(key=lambda x: x.confidence, reverse=True)
            for i, r in enumerate(hallucinated[:10], 1):
                print(f"{i}. {r.entity_name} ({r.entity_type}) - Confidence: {r.confidence:.3f}")
                print(f"   Issues: {', '.join(r.issues)}")


class GroqEntityValidator(EntityValidator):
    """Validator using Groq API (SelfCheckGPT-Prompt variant)"""
    
    def __init__(self, graphrag_output_dir: str, api_key: Optional[str] = None, 
                 cache_dir: str = "validation_cache"):
        super().__init__(graphrag_output_dir, cache_dir)
        
        # Import Groq
        try:
            from groq import Groq
        except ImportError:
            print("ERROR: groq package not installed. Run: pip install groq")
            sys.exit(1)
        
        # Initialize Groq client
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print("ERROR: GROQ_API_KEY not found in environment")
            sys.exit(1)
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"  # Fast and accurate (updated model)
        
    def validate_entity(self, entity_row) -> ValidationResult:
        """Validate entity using Groq API"""
        start_time = time.time()
        
        entity_id = entity_row['id']
        entity_name = entity_row['title']
        entity_type = entity_row['type']
        description = entity_row['description']
        
        # Get source texts
        source_texts = self.get_source_texts(entity_row)
        if not source_texts:
            return ValidationResult(
                entity_id=entity_id,
                entity_name=entity_name,
                entity_type=entity_type,
                description=description,
                confidence=0.0,
                is_hallucinated=False,
                method="groq",
                issues=["No source texts available"],
                validation_time=time.time() - start_time
            )
        
        # Construct prompt (SelfCheckGPT-Prompt variant)
        prompt = self._build_validation_prompt(entity_name, entity_type, description, source_texts)
        
        try:
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a fact-checking assistant that validates entity descriptions against source documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=500
            )
            
            # Parse response
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("API returned empty response")
            answer = content.strip()
            confidence, is_hallucinated, issues = self._parse_api_response(answer)
            
        except Exception as e:
            print(f"\nAPI error for {entity_name}: {e}")
            confidence = 0.0
            is_hallucinated = False
            issues = [f"API error: {str(e)}"]
        
        return ValidationResult(
            entity_id=entity_id,
            entity_name=entity_name,
            entity_type=entity_type,
            description=description,
            confidence=confidence,
            is_hallucinated=is_hallucinated,
            method="groq",
            issues=issues,
            validation_time=time.time() - start_time
        )
    
    def _build_validation_prompt(self, name: str, entity_type: str, description: str, 
                                 source_texts: List[str]) -> str:
        """Build validation prompt"""
        # Take first 3 source texts to stay within context limits
        context = "\n\n---\n\n".join(source_texts[:3])
        
        prompt = f"""You are validating whether an entity description is supported by the source documents.

ENTITY INFORMATION:
- Name: {name}
- Type: {entity_type}
- Description: {description}

SOURCE DOCUMENTS:
{context}

TASK:
Carefully check if the entity description is factually supported by the source documents. Look for:
1. Does the entity name appear in the source documents?
2. Is the entity type correct based on context?
3. Are the claims in the description supported by the source text?
4. Is there any information in the description that contradicts or isn't mentioned in the sources?

Respond in this exact format:
SUPPORTED: [YES/NO]
CONFIDENCE: [0.0-1.0, where 1.0 means definitely hallucinated]
ISSUES: [List specific problems, or "None" if description is accurate]

Be specific about any unsupported claims."""

        return prompt
    
    def _parse_api_response(self, response: str) -> Tuple[float, bool, List[str]]:
        """Parse API response to extract validation results
        
        Note: The prompt asks for confidence where 1.0 = definitely hallucinated,
        but the model sometimes interprets it as confidence in support.
        We use SUPPORTED field as the primary indicator.
        """
        lines = response.strip().split('\n')
        
        supported = True
        raw_confidence = 0.0
        issues = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('SUPPORTED:'):
                supported = 'YES' in line.upper()
            elif line.startswith('CONFIDENCE:'):
                try:
                    conf_str = line.split(':')[1].strip()
                    raw_confidence = float(conf_str.split()[0])  # Handle "0.8 (high)" format
                except:
                    raw_confidence = 0.0
            elif line.startswith('ISSUES:'):
                issues_text = line.split(':', 1)[1].strip()
                if issues_text.lower() not in ['none', 'none.', '']:
                    issues = [issues_text]
        
        # Convert to hallucination confidence based on SUPPORTED field
        if supported:
            # If supported, confidence should be low (not hallucinated)
            # If model gave high confidence, it likely meant "confidence in support"
            confidence = 0.1 if raw_confidence > 0.5 else raw_confidence
        else:
            # Not supported = likely hallucinated
            confidence = 0.8 if raw_confidence < 0.5 else raw_confidence
        
        is_hallucinated = not supported
        
        return confidence, is_hallucinated, issues


class GPUNLIValidator(EntityValidator):
    """Validator using GPU-accelerated NLI model"""
    
    def __init__(self, graphrag_output_dir: str, cache_dir: str = "validation_cache"):
        super().__init__(graphrag_output_dir, cache_dir)
        
        # Check for GPU
        try:
            import torch
            if torch.cuda.is_available():
                self.device = "cuda"
                print(f"GPU detected: {torch.cuda.get_device_name(0)}")
            else:
                print("WARNING: No GPU detected. NLI will be VERY slow on CPU.")
                print("Consider using --method groq or --method hybrid instead.")
                self.device = "cpu"
        except ImportError:
            print("ERROR: PyTorch not installed. Run: pip install torch")
            sys.exit(1)
        
        # Load NLI model
        print("Loading NLI model (this may take a minute)...")
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            
            model_name = "microsoft/deberta-v2-xlarge-mnli"  # High accuracy NLI model
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()
            
            print("NLI model loaded successfully")
            
        except ImportError:
            print("ERROR: transformers not installed. Run: pip install transformers")
            sys.exit(1)
    
    def validate_entity(self, entity_row) -> ValidationResult:
        """Validate entity using NLI model"""
        import torch
        
        start_time = time.time()
        
        entity_id = entity_row['id']
        entity_name = entity_row['title']
        entity_type = entity_row['type']
        description = entity_row['description']
        
        # Get source texts
        source_texts = self.get_source_texts(entity_row)
        if not source_texts:
            return ValidationResult(
                entity_id=entity_id,
                entity_name=entity_name,
                entity_type=entity_type,
                description=description,
                confidence=0.0,
                is_hallucinated=False,
                method="gpu_nli",
                issues=["No source texts available"],
                validation_time=time.time() - start_time
            )
        
        # Break description into sentences
        sentences = [s.strip() for s in description.split('.') if s.strip()]
        
        # Check each sentence against source texts
        contradiction_scores = []
        
        for sentence in sentences:
            if len(sentence) < 10:  # Skip very short fragments
                continue
            
            # Check against each source text
            max_entailment = 0.0
            
            for source_text in source_texts[:3]:  # Limit to first 3 sources
                # Truncate source text to avoid token limits
                source_text = source_text[:1000]
                
                # NLI: does source_text entail the sentence?
                inputs = self.tokenizer(
                    source_text,
                    sentence,
                    return_tensors="pt",
                    truncation=True,
                    max_length=512
                ).to(self.device)
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    probs = torch.softmax(outputs.logits, dim=1)[0]
                    
                    # probs: [contradiction, neutral, entailment]
                    entailment_score = probs[2].item()
                    max_entailment = max(max_entailment, entailment_score)
            
            # If sentence is not entailed by any source, it's likely hallucinated
            contradiction_scores.append(1.0 - max_entailment)
        
        # Average contradiction score
        if contradiction_scores:
            confidence = sum(contradiction_scores) / len(contradiction_scores)
        else:
            confidence = 0.0
        
        is_hallucinated = confidence > 0.5
        issues = []
        if is_hallucinated:
            issues.append(f"Description not well-supported by source texts (avg entailment: {1-confidence:.2f})")
        
        return ValidationResult(
            entity_id=entity_id,
            entity_name=entity_name,
            entity_type=entity_type,
            description=description,
            confidence=confidence,
            is_hallucinated=is_hallucinated,
            method="gpu_nli",
            issues=issues,
            validation_time=time.time() - start_time
        )


class HybridValidator(EntityValidator):
    """Hybrid validator: text matching + Groq spot checks"""
    
    def __init__(self, graphrag_output_dir: str, api_key: Optional[str] = None,
                 cache_dir: str = "validation_cache"):
        super().__init__(graphrag_output_dir, cache_dir)
        
        # Initialize Groq client for spot checks
        try:
            from groq import Groq
            self.api_key = api_key or os.getenv("GROQ_API_KEY")
            if self.api_key:
                self.client = Groq(api_key=self.api_key)
                self.model = "llama-3.3-70b-versatile"
                self.groq_available = True
            else:
                print("WARNING: GROQ_API_KEY not found. Falling back to text matching only.")
                self.groq_available = False
        except ImportError:
            print("WARNING: groq package not installed. Using text matching only.")
            self.groq_available = False
    
    def validate_entity(self, entity_row) -> ValidationResult:
        """Validate using text matching first, then Groq if uncertain"""
        start_time = time.time()
        
        entity_id = entity_row['id']
        entity_name = entity_row['title']
        entity_type = entity_row['type']
        description = entity_row['description']
        
        # Get source texts
        source_texts = self.get_source_texts(entity_row)
        if not source_texts:
            return ValidationResult(
                entity_id=entity_id,
                entity_name=entity_name,
                entity_type=entity_type,
                description=description,
                confidence=0.0,
                is_hallucinated=False,
                method="hybrid",
                issues=["No source texts available"],
                validation_time=time.time() - start_time
            )
        
        # Step 1: Fast text matching
        combined_source = " ".join(source_texts).lower()
        description_lower = description.lower()
        
        # Extract key terms from description (words 4+ chars)
        key_terms = [
            word.strip('.,;:!?()"\'')
            for word in description_lower.split()
            if len(word) > 3 and word.isalpha()
        ]
        
        # Calculate term coverage
        found_terms = sum(1 for term in key_terms if term in combined_source)
        coverage = found_terms / len(key_terms) if key_terms else 0.0
        
        # Check if entity name appears
        name_found = entity_name.lower() in combined_source
        
        # Fast path decisions
        if coverage > 0.7 and name_found:
            # High confidence: NOT hallucinated
            return ValidationResult(
                entity_id=entity_id,
                entity_name=entity_name,
                entity_type=entity_type,
                description=description,
                confidence=0.1,
                is_hallucinated=False,
                method="hybrid_text",
                issues=[],
                validation_time=time.time() - start_time
            )
        
        if coverage < 0.3 or not name_found:
            # High confidence: LIKELY hallucinated
            issues = []
            if not name_found:
                issues.append(f"Entity name '{entity_name}' not found in source texts")
            if coverage < 0.3:
                issues.append(f"Low term coverage ({coverage:.1%})")
            
            return ValidationResult(
                entity_id=entity_id,
                entity_name=entity_name,
                entity_type=entity_type,
                description=description,
                confidence=0.8,
                is_hallucinated=True,
                method="hybrid_text",
                issues=issues,
                validation_time=time.time() - start_time
            )
        
        # Step 2: Uncertain case - use Groq spot check
        if self.groq_available:
            groq_result = self._groq_spot_check(entity_name, entity_type, description, source_texts)
            groq_result.validation_time = time.time() - start_time
            groq_result.method = "hybrid_groq"
            return groq_result
        else:
            # No Groq available, make conservative guess
            return ValidationResult(
                entity_id=entity_id,
                entity_name=entity_name,
                entity_type=entity_type,
                description=description,
                confidence=0.5,
                is_hallucinated=coverage < 0.5,
                method="hybrid_text",
                issues=[f"Uncertain (coverage: {coverage:.1%})"],
                validation_time=time.time() - start_time
            )
    
    def _groq_spot_check(self, name: str, entity_type: str, description: str,
                        source_texts: List[str]) -> ValidationResult:
        """Use Groq API for uncertain cases"""
        context = "\n\n---\n\n".join(source_texts[:3])
        
        prompt = f"""Quickly validate if this entity description is accurate:

ENTITY: {name} ({entity_type})
DESCRIPTION: {description}

SOURCE TEXT:
{context}

Is the description supported? Reply with ONLY:
VERDICT: [ACCURATE/HALLUCINATED]
CONFIDENCE: [0.0-1.0]
REASON: [one sentence]"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a fast fact-checker."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=150
            )
            
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("API returned empty response")
            answer = content.strip()
            
            # Parse response
            is_hallucinated = "HALLUCINATED" in answer.upper()
            confidence = 0.7 if is_hallucinated else 0.3
            
            # Extract reason
            issues = []
            for line in answer.split('\n'):
                if line.startswith('REASON:'):
                    issues.append(line.split(':', 1)[1].strip())
            
            return ValidationResult(
                entity_id="",  # Will be filled by caller
                entity_name=name,
                entity_type=entity_type,
                description=description,
                confidence=confidence,
                is_hallucinated=is_hallucinated,
                method="hybrid_groq",
                issues=issues,
                validation_time=0.0  # Will be filled by caller
            )
            
        except Exception as e:
            # Groq error, return conservative guess
            return ValidationResult(
                entity_id="",
                entity_name=name,
                entity_type=entity_type,
                description=description,
                confidence=0.5,
                is_hallucinated=False,
                method="hybrid_groq",
                issues=[f"API error: {str(e)}"],
                validation_time=0.0
            )


def main():
    parser = argparse.ArgumentParser(description="Validate GraphRAG entity descriptions for hallucinations")
    parser.add_argument(
        "--method",
        choices=["groq", "gpu", "hybrid"],
        default="groq",
        help="Validation method: groq (API), gpu (local NLI), hybrid (text+API)"
    )
    parser.add_argument(
        "--graphrag-dir",
        default="graphrag_output/output",
        help="Path to GraphRAG output directory"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of entities to validate (for testing). If not set and --all not specified, validates 10 entities by default."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all entities (overrides --limit)"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from cached results"
    )
    parser.add_argument(
        "--output",
        default="validation_report.csv",
        help="Output CSV file for validation report"
    )
    
    args = parser.parse_args()
    
    # Create validator
    if args.method == "groq":
        print("Using Groq API validator (SelfCheckGPT-Prompt)")
        validator = GroqEntityValidator(args.graphrag_dir)
    elif args.method == "gpu":
        print("Using GPU NLI validator (SelfCheckGPT-NLI)")
        validator = GPUNLIValidator(args.graphrag_dir)
    else:  # hybrid
        print("Using Hybrid validator (Text matching + Groq spot checks)")
        validator = HybridValidator(args.graphrag_dir)
    
    # Validate
    if args.all:
        limit = None  # Validate all entities
        print("Validating ALL entities...")
    elif args.limit:
        limit = args.limit  # Validate specified number
        print(f"Validating {limit} entities...")
    else:
        limit = 10  # Default to 10 entities for safety
        print("No --limit or --all specified. Defaulting to 10 entities for testing.")
        print("Use --all to validate all entities, or --limit N to validate N entities.")
    
    results = validator.validate_batch(limit=limit, resume=args.resume)
    
    # Generate report
    if results:
        validator.generate_report(results, args.output)
    else:
        print("No results to report")


if __name__ == "__main__":
    main()
