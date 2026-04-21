import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox, Button
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

def match_station_name(MyGraph, user_input):
    station_names = list(MyGraph.nodes())
    text = user_input.strip()
    if not text:
        return None, "Please enter a station name."
    
    # Exact match
    for name in station_names:
        if name.lower() == text.lower():
            return name, None
    
    # Partial match
    matches = [name for name in station_names if text.lower() in name.lower()]
    if len(matches) == 1:
        return matches[0], None
    elif len(matches) > 1:
        return None, f"Multiple matches: {', '.join(matches)}"
    else:
        return None, f"Station '{text}' not found."

def draw_map(MyGraph, weight_choice):
    # Detect screen size and adapt figure layout
    fig, ax = plt.subplots(figsize=(16, 10), facecolor='white')
    scale = 1.0  # Scale factor for nodes/fonts
    try:
        manager = plt.get_current_fig_manager() # Get the current figure manager
        screen_w = manager.window.winfo_screenwidth()
        screen_h = manager.window.winfo_screenheight()
        dpi = fig.get_dpi()
        fig_w = screen_w * 0.95 / dpi
        fig_h = screen_h * 0.85 / dpi
        fig.set_size_inches(fig_w, fig_h)
        manager.window.state('zoomed')
        # Scale factor based on screen width (1920px = 1.0)
        scale = min(screen_w / 1920, 1.0)
    except Exception:
        pass
    # Adjust margins: more right margin on small screens for legend
    right_margin = 0.88 if scale < 0.8 else 0.92
    plt.subplots_adjust(left=0.01, right=right_margin, bottom=0.12, top=0.93)
    
    # Use coordinates from stations.csv
    pos = nx.get_node_attributes(MyGraph, 'pos')
    
    # Store state for status messages
    state = {'status_text': None, 'route_text': None}
    
    def draw_base_map():
        ax.clear() # Clear the axes for redrawing
        
        node_colors = list(nx.get_node_attributes(MyGraph, 'color').values())
        edge_colors = list(nx.get_edge_attributes(MyGraph, 'color').values())

        # Scale-aware sizes
        s = scale
        node_sz = int(500 * s)
        edge_w = max(2, 3 * s)
        font_edge = max(5, int(7 * s))
        font_label = max(5, int(7 * s))
        font_legend = max(8, int(12 * s))
        font_title_legend = max(9, int(14 * s))
        font_title = max(14, int(20 * s))
        
        # Draw edges
        nx.draw_networkx_edges(MyGraph, pos=pos, edge_color=edge_colors, width=edge_w, alpha=0.95, ax=ax)

        # Draw nodes
        nx.draw_networkx_nodes(MyGraph, pos=pos, node_color=node_colors, node_size=node_sz, 
                              edgecolors='white', linewidths=max(2, 3 * s), ax=ax)

        # Display edge weights (distances)
        edge_labels = nx.get_edge_attributes(MyGraph, weight_choice)
        # Add unit suffix to edge labels
        edge_labels_with_unit = {edge: f"{value}{weight_choice}" for edge, value in edge_labels.items()}
        
        # Draw edge labels with transparent background to avoid covering edges
        edge_label_collection = nx.draw_networkx_edge_labels(
            MyGraph, pos, 
            edge_labels=edge_labels_with_unit, 
            font_size=font_edge,
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
            
            ax.text(label_x, label_y, node_id, fontsize=font_label, fontweight='bold',
                    ha=node_data.get('ha', 'left'), va=node_data.get('va', 'bottom'),
                    zorder=6, color='black',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.85,
                              edgecolor='lightgray', linewidth=0.5))
        
        # Create legend
        line_info = {}
        for u, v, data in MyGraph.edges(data=True):
            line_name = data.get('line_name')
            color = data.get('color')
            if line_name not in line_info:
                line_info[line_name] = color
        
        for name in sorted(line_info.keys()):
            ax.plot([], [], color=line_info[name], linewidth=3, label=name)
        
        ax.plot([], [], 'o', color='#ADADAD', markersize=max(5, int(8 * s)), markeredgecolor='white', 
                markeredgewidth=2, label='Interchange Station', linestyle='None')
        
        legend = ax.legend(loc='upper right', title='Transit Lines & Stations', edgecolor='black', 
                           framealpha=0.97, fontsize=font_legend, title_fontsize=font_title_legend, 
                           fancybox=True, shadow=True, scatterpoints=1)
        legend.get_frame().set_linewidth(2)
        
        fig.suptitle('Public Transport Network Map', fontsize=font_title, fontweight='bold', y=0.96)
        ax.axis('off')
    
    def draw_path_overlay(path):
        # Draw the full base map as-is
        draw_base_map()
        
        # Build path edge list
        path_edgelist = [(path[i], path[i + 1]) for i in range(len(path) - 1)]
        path_nodes = list(set(path))
        
        # Overlay thick gold edges on top of base map
        nx.draw_networkx_edges(MyGraph, pos, edgelist=path_edgelist,
                              edge_color='#FFD700', width=max(4, 7 * scale), alpha=0.85, ax=ax,
                              style='solid')
        
        # Redraw edge labels on top of gold edges so they remain visible
        path_edge_labels = {}
        for i in range(len(path) - 1):
            edge = (path[i], path[i + 1])
            distance = MyGraph[path[i]][path[i + 1]][weight_choice]
            path_edge_labels[edge] = f"{distance}{weight_choice}"
        edge_label_collection = nx.draw_networkx_edge_labels(
            MyGraph, pos, edge_labels=path_edge_labels,
            font_size=max(5, int(7 * scale)), font_weight='bold', font_color='#222222', ax=ax
        )
        for text_obj in edge_label_collection.values():
            text_obj.set_bbox(dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.85, edgecolor='none'))
            text_obj.set_zorder(10)
        
        # Overlay gold ring borders around path nodes
        nx.draw_networkx_nodes(MyGraph, pos, nodelist=path_nodes,
                              node_color=[MyGraph.nodes[n]['color'] for n in path_nodes],
                              node_size=int(500 * scale), edgecolors='#FFD700', linewidths=max(2, 4 * scale), ax=ax)
        
        # Build route info text
        total_dist = round(nx.shortest_path_length(MyGraph, path[0], path[-1], weight=weight_choice), 2)
        route_lines = [f"Route: {path[0]} → {path[-1]}",
                       f"Distance: {total_dist} {weight_choice} | Stops: {len(path) - 1}",
                       ""]
        current_line = None
        for i in range(len(path) - 1):
            edge_data = MyGraph[path[i]][path[i + 1]]
            line_name = edge_data['line_name']
            distance = edge_data[weight_choice]
            if line_name != current_line:
                if current_line is not None:
                    route_lines.append(f">> Transfer to {line_name} at {path[i]}")
                else:
                    route_lines.append(f"Board {line_name} at {path[i]}")
                current_line = line_name
            route_lines.append(f"  {path[i]} → {path[i+1]} ({distance} {weight_choice})")
        
        # Display route info on the left margin of the figure
        if state.get('route_text') is not None:
            state['route_text'].remove()
        route_text = "\n".join(route_lines)
        state['route_text'] = fig.text(0.01, 0.88, route_text,
                fontsize=max(7, int(9 * scale)), fontfamily='monospace', verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='#FFFFF0', alpha=0.95,
                          edgecolor='#555555', linewidth=1.2))
        
        fig.suptitle(f'Shortest Path: {path[0]} → {path[-1]} ({total_dist} {weight_choice})',
                     fontsize=max(14, int(18 * scale)), fontweight='bold', y=0.96)
    
    def set_status(message, color='red'):
        # Display a status message below the title
        if state['status_text'] is not None:
            state['status_text'].remove()
            state['status_text'] = None
        # Truncate long messages to prevent overflow
        display_msg = message if len(message) <= 80 else message[:77] + '...'
        state['status_text'] = fig.text(0.5, 0.89, display_msg, ha='center',
                                        fontsize=max(9, int(12 * scale)),
                                        color=color, fontweight='bold',
                                        bbox=dict(boxstyle='round,pad=0.3',
                                                  facecolor='#FFF0F0', alpha=0.95,
                                                  edgecolor=color, linewidth=1))
        fig.canvas.draw_idle()
    
    def on_find_clicked(event):
        # Find Path button
        if state['status_text'] is not None:
            state['status_text'].remove()
            state['status_text'] = None
        
        source, err1 = match_station_name(MyGraph, tb_start.text)
        if err1:
            set_status(f"Start station: {err1}")
            return
        
        target, err2 = match_station_name(MyGraph, tb_end.text)
        if err2:
            set_status(f"End station: {err2}")
            return
        
        if source == target:
            set_status("Start and end stations are the same!")
            return
        
        try:
            path = nx.shortest_path(MyGraph, source, target, weight=weight_choice)
        except nx.NetworkXNoPath:
            set_status(f"No path found between {source} and {target}.")
            return
        
        draw_path_overlay(path)
        fig.canvas.draw_idle()
    
    def on_reset_clicked(event):
        # Reset button
        if state['status_text'] is not None:
            state['status_text'].remove()
            state['status_text'] = None
        if state['route_text'] is not None:
            state['route_text'].remove()
            state['route_text'] = None
        draw_base_map()
        fig.canvas.draw_idle()
    
    # Draw initial base map
    draw_base_map()
    
    # Create path finder UI controls at the bottom of the figure
    ax_start = fig.add_axes([0.08, 0.03, 0.25, 0.04])
    ax_end = fig.add_axes([0.42, 0.03, 0.25, 0.04])
    ax_btn = fig.add_axes([0.72, 0.03, 0.1, 0.04])
    ax_reset = fig.add_axes([0.84, 0.03, 0.1, 0.04])
    
    tb_start = TextBox(ax_start, 'From:  ', initial='')
    tb_end = TextBox(ax_end, 'To:  ', initial='')
    
    btn_find = Button(ax_btn, 'Find Path', color='#FFD700', hovercolor='#FFC300')
    btn_find.label.set_fontweight('bold')
    btn_find.on_clicked(on_find_clicked)
    
    btn_reset = Button(ax_reset, 'Reset', color='#E0E0E0', hovercolor='#BDBDBD')
    btn_reset.label.set_fontweight('bold')
    btn_reset.on_clicked(on_reset_clicked)

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