import networkx as nx
import matplotlib.pyplot as plt

def draw_pipeline(graph):
    G = nx.DiGraph()
    edge_colors = []

    for u in graph:
        for v in graph[u]:
            data = graph[u][v]
            label = f"{data['capacity']}L/s"
            G.add_edge(u, v, label=label)
            edge_colors.append("red" if data['leak'] else "blue")

    pos = nx.spring_layout(G)
    edge_labels = nx.get_edge_attributes(G, 'label')
    plt.figure(figsize=(7, 5))
    nx.draw(G, pos, with_labels=True, node_color='lightblue',
            node_size=2000, font_size=10, edge_color=edge_colors, width=2)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    return plt