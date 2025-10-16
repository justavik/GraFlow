"""
GraphML Knowledge Graph Visualization Script
Generates publication-ready PNG visualization of GraphRAG output
"""

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from collections import Counter
import numpy as np

def load_graphml(file_path):
    """Load GraphML file and return NetworkX graph"""
    print(f"Loading graph from {file_path}...")
    G = nx.read_graphml(file_path)
    print(f"✓ Loaded graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    return G

def analyze_graph_structure(G):
    """Analyze and print graph statistics"""
    print("\n" + "="*60)
    print("GRAPH STATISTICS")
    print("="*60)
    
    # Basic stats
    print(f"Nodes: {G.number_of_nodes()}")
    print(f"Edges: {G.number_of_edges()}")
    print(f"Density: {nx.density(G):.6f}")
    
    # Degree distribution
    degrees = dict(G.degree())
    avg_degree = sum(degrees.values()) / len(degrees)
    max_degree_node = max(degrees.items(), key=lambda x: x[1])[0]
    print(f"\nAverage Degree: {avg_degree:.2f}")
    print(f"Max Degree Node: '{max_degree_node}' (degree: {degrees[max_degree_node]})")
    
    # Top 10 hub nodes
    print("\nTop 10 Hub Nodes:")
    sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (node, deg) in enumerate(sorted_nodes, 1):
        print(f"  {i}. {node[:50]:50s} (degree: {deg})")
    
    # Connected components
    if not nx.is_connected(G):
        components = list(nx.connected_components(G))
        print(f"\nConnected Components: {len(components)}")
        print(f"  Largest Component: {len(max(components, key=len))} nodes")
    else:
        print("\nGraph is fully connected")
    
    return degrees, sorted_nodes

def create_visualization(G, degrees, output_path='graph_visualization.png', 
                        top_n=100, figsize=(20, 16)):
    """
    Create publication-ready graph visualization
    
    Args:
        G: NetworkX graph
        degrees: Node degree dictionary
        output_path: Output PNG file path
        top_n: Number of top nodes to display (for large graphs)
        figsize: Figure size (width, height)
    """
    print(f"\n{'='*60}")
    print(f"CREATING VISUALIZATION")
    print(f"{'='*60}")
    
    # For large graphs, extract subgraph of most connected nodes
    if G.number_of_nodes() > top_n:
        print(f"Graph too large. Visualizing top {top_n} most connected nodes...")
        top_nodes = [node for node, _ in sorted(degrees.items(), 
                                                 key=lambda x: x[1], 
                                                 reverse=True)[:top_n]]
        G_viz = G.subgraph(top_nodes).copy()
        print(f"✓ Extracted subgraph: {G_viz.number_of_nodes()} nodes, {G_viz.number_of_edges()} edges")
    else:
        G_viz = G
        print(f"Visualizing full graph ({G.number_of_nodes()} nodes)")
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    
    # Layout algorithm - spring layout for force-directed positioning
    print("Computing layout (this may take a minute)...")
    pos = nx.spring_layout(G_viz, k=2/np.sqrt(G_viz.number_of_nodes()), 
                           iterations=50, seed=42)
    
    # Node sizes based on degree (importance)
    node_degrees = dict(G_viz.degree())
    node_sizes = [300 + (node_degrees[node] * 50) for node in G_viz.nodes()]
    
    # Node colors based on degree centrality (hub importance)
    degree_centrality = nx.degree_centrality(G_viz)
    node_colors = [degree_centrality[node] for node in G_viz.nodes()]
    
    # Edge weights (if available)
    edge_weights = []
    for u, v in G_viz.edges():
        edge_data = G_viz.get_edge_data(u, v)
        weight = float(edge_data.get('weight', 1.0)) if edge_data else 1.0
        edge_weights.append(weight)
    
    # Normalize edge weights for visualization
    max_weight = max(edge_weights) if edge_weights else 1.0
    edge_alphas = [0.2 + (0.6 * w / max_weight) for w in edge_weights]
    edge_widths = [0.5 + (2.5 * w / max_weight) for w in edge_weights]
    
    # Draw edges first (so nodes appear on top)
    print("Drawing edges...")
    for (u, v), alpha, width in zip(G_viz.edges(), edge_alphas, edge_widths):
        nx.draw_networkx_edges(
            G_viz, pos,
            edgelist=[(u, v)],
            width=width,
            alpha=alpha,
            edge_color='#666666',
            ax=ax
        )
    
    # Draw nodes
    print("Drawing nodes...")
    nx.draw_networkx_nodes(
        G_viz, pos,
        node_size=node_sizes,
        node_color=node_colors,
        cmap='YlOrRd',
        alpha=0.9,
        edgecolors='black',
        linewidths=1.5,
        ax=ax
    )
    
    # Draw labels only for top hub nodes (to avoid clutter)
    top_hubs = sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)[:20]
    top_hub_nodes = {node: node for node, _ in top_hubs}
    
    print("Drawing labels for top 20 hubs...")
    nx.draw_networkx_labels(
        G_viz, pos,
        labels=top_hub_nodes,
        font_size=8,
        font_weight='bold',
        font_color='black',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                  edgecolor='black', alpha=0.8),
        ax=ax
    )
    
    # Title and annotations
    title = f"GraphRAG Knowledge Graph Visualization\n"
    title += f"{G.number_of_nodes()} Entities | {G.number_of_edges()} Relationships"
    if G.number_of_nodes() > top_n:
        title += f" (showing top {top_n} connected nodes)"
    
    ax.set_title(title, fontsize=18, fontweight='bold', pad=20)
    
    # Legend
    legend_elements = [
        mpatches.Patch(facecolor='#FFEDA0', edgecolor='black', 
                      label='Low Connectivity (peripheral concepts)'),
        mpatches.Patch(facecolor='#FEB24C', edgecolor='black', 
                      label='Medium Connectivity'),
        mpatches.Patch(facecolor='#F03B20', edgecolor='black', 
                      label='High Connectivity (hub concepts)'),
        Line2D([0], [0], color='#666666', linewidth=3, alpha=0.8,
                  label='Strong Relationship'),
        Line2D([0], [0], color='#666666', linewidth=1, alpha=0.3,
                  label='Weak Relationship')
    ]
    
    ax.legend(handles=legend_elements, loc='upper right', 
             fontsize=10, frameon=True, fancybox=True, shadow=True)
    
    # Add metadata annotation
    metadata_text = f"Chunk Size: 3200 tokens\n"
    metadata_text += f"Avg. Degree: {sum(node_degrees.values()) / len(node_degrees):.1f}\n"
    metadata_text += f"Graph Density: {nx.density(G_viz):.4f}"
    
    ax.text(0.02, 0.02, metadata_text, transform=ax.transAxes,
           fontsize=10, verticalalignment='bottom',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Remove axes
    ax.axis('off')
    
    # Tight layout
    plt.tight_layout()
    
    # Save with high DPI for publication quality
    print(f"\nSaving visualization to {output_path}...")
    plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    print(f"✓ Saved high-resolution PNG (300 DPI)")
    
    # Also save a lower resolution version for quick preview
    preview_path = output_path.replace('.png', '_preview.png')
    plt.savefig(preview_path, dpi=100, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"✓ Saved preview PNG (100 DPI): {preview_path}")
    
    plt.close()
    
    return output_path

def create_degree_distribution_plot(degrees, output_path='degree_distribution.png'):
    """Create degree distribution histogram"""
    print(f"\nCreating degree distribution plot...")
    
    fig, ax = plt.subplots(figsize=(10, 6), facecolor='white')
    
    degree_values = list(degrees.values())
    
    # Histogram
    ax.hist(degree_values, bins=50, color='#3498db', alpha=0.7, 
            edgecolor='black', linewidth=1.2)
    
    ax.set_xlabel('Node Degree (Number of Connections)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
    ax.set_title('Degree Distribution of Knowledge Graph', 
                 fontsize=14, fontweight='bold', pad=15)
    
    # Add statistics
    stats_text = f"Mean: {np.mean(degree_values):.1f}\n"
    stats_text += f"Median: {np.median(degree_values):.1f}\n"
    stats_text += f"Max: {np.max(degree_values)}"
    
    ax.text(0.95, 0.95, stats_text, transform=ax.transAxes,
           fontsize=11, verticalalignment='top', horizontalalignment='right',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    ax.grid(True, alpha=0.3, linestyle='--')
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    print(f"✓ Saved degree distribution: {output_path}")
    plt.close()

def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("GraphRAG Knowledge Graph Visualization")
    print("="*60)
    
    # File paths
    graphml_path = r"c:\Users\avikc\Projects\GraFlow\graphrag_output\output\graph.graphml"
    output_dir = r"c:\Users\avikc\Projects\GraFlow\paper\paper_figures"
    
    # Load graph
    G = load_graphml(graphml_path)
    
    # Analyze structure
    degrees, sorted_nodes = analyze_graph_structure(G)
    
    # Create visualizations
    graph_viz_path = f"{output_dir}/fig3_knowledge_graph.png"
    degree_dist_path = f"{output_dir}/fig4_degree_distribution.png"
    
    # Main graph visualization (top 25 nodes for clarity)
    create_visualization(G, degrees, output_path=graph_viz_path, top_n=25)
    
    # Degree distribution
    create_degree_distribution_plot(degrees, output_path=degree_dist_path)
    
    print("\n" + "="*60)
    print("✅ VISUALIZATION COMPLETE!")
    print("="*60)
    print(f"\nGenerated files:")
    print(f"  1. {graph_viz_path}")
    print(f"  2. {graph_viz_path.replace('.png', '_preview.png')}")
    print(f"  3. {degree_dist_path}")
    print(f"\nReady for inclusion in your paper!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
