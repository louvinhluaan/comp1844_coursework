import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

def build_transport_graph():
    MyGraph = nx.Graph()  # Create an empty graph
    
    # Read data from CSV files
    try:
        stations_df = pd.read_csv('data/stations.csv')
        edges_df = pd.read_csv('data/edges.csv')
    except FileNotFoundError as e:
        print(f"Error: {e} - Please check the data/ directory.")
        return None

    # Add nodes and edges to the graph
    for index, row in stations_df.iterrows():
        code = row['Code']
        MyGraph.add_node(
            row['Station_Name'], 
            pos=(row['X_pos'], row['Y_pos']), 
            color=row['Color'], 
            code=code,
            is_interchange=row['Is_Interchange'],
            offset_x=row.get('Offset_X', 600),
            offset_y=row.get('Offset_Y', 600),
            ha=row.get('Align_H', 'left'),
            va=row.get('Align_V', 'bottom')
        )

    # Add edges to the graph
    for index, row in edges_df.iterrows():
        km_distance = row['Distance_km']
        miles_distance = row['Distance_miles']
        
        MyGraph.add_edge(
            row['Source'], 
            row['Target'], 
            line_name=row['Line_Name'], 
            color=row['Color'], 
            km=km_distance,
            miles=miles_distance
        )
        
    print("Data loaded successfully! Total stations:", MyGraph.number_of_nodes(), "| Total connections:", MyGraph.number_of_edges())
    return MyGraph

def get_user_preference():
    while True:
        choice = input("Choose your preference (km/miles): ").strip().lower()
        if choice in ['km', 'miles']:
            return choice
        print("Error: Please enter only 'km' or 'miles'.")

def draw_map(MyGraph, weight_choice):
    fig, ax = plt.subplots(figsize=(24, 16), facecolor='white')
    
    # Use coordinates from stations.csv
    pos = nx.get_node_attributes(MyGraph, 'pos')
    
    node_colors = list(nx.get_node_attributes(MyGraph, 'color').values())
    edge_colors = list(nx.get_edge_attributes(MyGraph, 'color').values())

    # Draw edges
    nx.draw_networkx_edges(MyGraph, pos=pos, edge_color=edge_colors, width=3, alpha=0.95, ax=ax)

    # Draw nodes
    nx.draw_networkx_nodes(MyGraph, pos=pos, node_color=node_colors, node_size=500, 
                          edgecolors='white', linewidths=3, ax=ax)

    # Display edge weights (distances)
    edge_labels = nx.get_edge_attributes(MyGraph, weight_choice)
    # Add unit suffix to edge labels
    edge_labels_with_unit = {edge: f"{value}{weight_choice}" for edge, value in edge_labels.items()}
    
    # Draw edge labels with transparent background to avoid covering edges
    edge_label_collection = nx.draw_networkx_edge_labels(
        MyGraph, pos, 
        edge_labels=edge_labels_with_unit, 
        font_size=7,
        font_weight='bold', 
        font_color='#222222', 
        ax=ax
    )
    
    # Make label backgrounds semi-transparent so edges are visible underneath
    for text_obj in edge_label_collection.values():
        text_obj.set_bbox(dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.5, edgecolor='none'))

    # Display station names next to nodes
    for node_id in MyGraph.nodes():
        node_data = MyGraph.nodes[node_id]
        x, y = pos[node_id]
        
        label_x = x + node_data.get('offset_x', 600)
        label_y = y + node_data.get('offset_y', 600)
        ha = node_data.get('ha', 'left')
        va = node_data.get('va', 'bottom')
        
        ax.text(label_x, label_y, node_id, fontsize=7, fontweight='bold',
                ha=ha, va=va, zorder=6, color='black',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.85, edgecolor='lightgray', linewidth=0.5))
    
    # Create legend
    line_info = {}
    for u, v, data in MyGraph.edges(data=True):
        line_name = data.get('line_name')
        color = data.get('color')
        if line_name not in line_info:
            line_info[line_name] = color
    
    # Sort by line name for consistent legend
    for name in sorted(line_info.keys()):
        color = line_info[name]
        ax.plot([], [], color=color, linewidth=3, label=name)
    
    # Add interchange station to legend
    ax.plot([], [], 'o', color='#ADADAD', markersize=8, markeredgecolor='white', 
            markeredgewidth=2, label='Interchange Station', linestyle='None')
    
    legend = ax.legend(loc='upper right', title='Transit Lines & Stations', edgecolor='black', 
                       framealpha=0.97, fontsize=12, title_fontsize=14, 
                       fancybox=True, shadow=True, scatterpoints=1)
    legend.get_frame().set_linewidth(2)
    
    # Title and layout - use suptitle for figure-level title
    fig.suptitle('Public Transport Network Map', fontsize=20, fontweight='bold', y=0.98)
    plt.axis('off')
    
    # Tight layout with space reserved for title
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()

def extract_network_data(MyGraph):
    # Take km distances from edges
    edge_distances_km = [data['km'] for u, v, data in MyGraph.edges(data=True)]
    num_edges = len(edge_distances_km)
    
    # Calculate sum and average
    total_km = round(np.sum(edge_distances_km), 2)
    total_miles = round(total_km * 0.621371, 2)
    
    avg_km = round(np.mean(edge_distances_km), 2) if num_edges > 0 else 0
    avg_miles = round(avg_km * 0.621371, 2)
    
    # Print results
    print("\n" + "="*60)
    print("TASK 2: NETWORK STATISTICS")
    print("="*60)
    print(f"\nTotal Network Length:")
    print(f"  {total_km} km")
    print(f"  {total_miles} miles")
    
    print(f"\nAverage Distance Per Edge:")
    print(f"  {avg_km} km")
    print(f"  {avg_miles} miles")
    print("="*60 + "\n")

if __name__ == "__main__":
    my_graph = build_transport_graph()
    
    # Check if graph was successfully loaded
    if my_graph is None:
        print("Failed to load graph. Exiting.")
        exit()
    
    user_choice = get_user_preference()
    extract_network_data(my_graph)
    draw_map(my_graph, user_choice)