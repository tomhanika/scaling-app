import networkx as nx


class GraphService:

    def __init__(self, frame, datastorage):
        self.frame = frame
        self.datastorage = datastorage

    def create_lattice_graph(self, evt=None):
        # Create Lattice Graph from JSON Layout, then Draws it.

        if self.datastorage.lattice is None:
            return

        graph = nx.Graph()

        x_min = 0
        x_max = 0
        y_min = 0
        y_max = 0
        y_min_node = None
        y_max_node = None

        for node in self.datastorage.lattice['positions']:

            # Determine utmost nodes and their positions on each axis
            for node_number, coords in node.items():
                if coords[0] < x_min:
                    x_min = coords[0]
                if coords[0] > x_max:
                    x_max = coords[0]
                if coords[1] <= y_min:
                    y_min = coords[1]
                    y_min_node = node_number
                if coords[1] >= y_max:
                    y_max = coords[1]
                    y_max_node = node_number

                name = str(self.datastorage.lattice['shorthand-annotation'][int(node_number)][node_number][0]) + "\n" \
                       + str(self.datastorage.lattice['shorthand-annotation'][int(node_number)][node_number][1])

                graph.add_node(node_number, pos=(coords[0], coords[1]), color="blue", label=name)

        for edges in self.datastorage.lattice['edges']:
            for origin in edges:
                for target in edges[origin]:
                    graph.add_edge(origin, target)

        # Add invisible buffer nodes to prevent graph from redrawing when utmost nodes are moved.
        xbuffer = 1
        ybuffer = 0.8

        graph.add_node("anchor0", pos=(x_min - xbuffer, y_min - ybuffer), color="red", label="")
        graph.add_node("anchor1", pos=(x_max + xbuffer, y_min - ybuffer), color="red", label="")
        graph.add_node("anchor2", pos=(x_min - xbuffer, y_max + ybuffer), color="red", label="")
        graph.add_node("anchor3", pos=(x_max + xbuffer, y_max + ybuffer), color="red", label="")

        self.frame.graph.draw_graph(graph, (x_min, x_max, y_min, y_max), y_min_node, y_max_node)

    def clear(self, evt=None):
        # Displays Empty Graph on Graph Panel

        self.datastorage.lattice = None
        graph = nx.Graph()
        self.frame.graph.draw_graph(graph, (0, 0, 0, 0), None, None)
