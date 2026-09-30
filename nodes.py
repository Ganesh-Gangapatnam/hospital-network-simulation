"""
nodes.py
Defines hospital node types and builds the network topology graph.
"""

import networkx as nx
import matplotlib.pyplot as plt


class HospitalNode:
    """Represents a single communicating unit in the hospital network."""

    def __init__(self, node_id: str, name: str, node_type: str):
        self.node_id = node_id
        self.name = name
        self.node_type = node_type  # e.g. 'ICU', 'DOCTOR', 'NURSE', 'EMERGENCY', 'LAB', 'PHARMACY', 'SERVER'

    def __repr__(self):
        return f"<{self.node_type}:{self.name}>"


class HospitalNetwork:
    """Builds and holds the hospital's network topology as a weighted graph."""

    def __init__(self):
        self.graph = nx.Graph()
        self.nodes: dict[str, HospitalNode] = {}
        self._build_topology()

    def _add_node(self, node_id, name, node_type):
        node = HospitalNode(node_id, name, node_type)
        self.nodes[node_id] = node
        self.graph.add_node(node_id, obj=node)

    def _add_link(self, id_a, id_b, weight):
        # weight = combined "cost" of the link (latency + unreliability).
        # Lower weight = better path. Used by Dijkstra routing.
        self.graph.add_edge(id_a, id_b, weight=weight)

    def _build_topology(self):
        # --- Define hospital units ---
        self._add_node("SRV", "Central Server", "SERVER")
        self._add_node("ICU1", "ICU Monitor 1", "ICU")
        self._add_node("ICU2", "ICU Monitor 2", "ICU")
        self._add_node("DOC1", "Doctor Station 1", "DOCTOR")
        self._add_node("DOC2", "Doctor Station 2", "DOCTOR")
        self._add_node("NUR1", "Nurse Station 1", "NURSE")
        self._add_node("EMR1", "Emergency Unit 1", "EMERGENCY")
        self._add_node("EMR2", "Emergency Unit 2", "EMERGENCY")
        self._add_node("LAB1", "Laboratory", "LAB")
        self._add_node("PHR1", "Pharmacy", "PHARMACY")

        # --- Hub links through central server ---
        self._add_link("SRV", "ICU1", 1)
        self._add_link("SRV", "ICU2", 1)
        self._add_link("SRV", "DOC1", 2)
        self._add_link("SRV", "DOC2", 2)
        self._add_link("SRV", "NUR1", 2)
        self._add_link("SRV", "EMR1", 1)
        self._add_link("SRV", "EMR2", 1)
        self._add_link("SRV", "LAB1", 3)
        self._add_link("SRV", "PHR1", 3)

        # --- Direct links (real alternate paths, not through the server) ---
        self._add_link("ICU1", "DOC1", 2)
        self._add_link("ICU2", "DOC2", 2)
        self._add_link("EMR1", "DOC1", 1)
        self._add_link("EMR2", "DOC2", 1)
        self._add_link("NUR1", "ICU1", 2)
        self._add_link("NUR1", "ICU2", 2)
        self._add_link("LAB1", "DOC1", 2)
        self._add_link("LAB1", "DOC2", 3)
        self._add_link("DOC1", "DOC2", 1)     # doctors can consult each other directly
        self._add_link("EMR1", "EMR2", 2)     # emergency units cross-linked
        self._add_link("ICU1", "EMR1", 3)     # ICU can escalate directly to emergency

    def show_topology(self):
        """Prints a text summary of all nodes and links."""
        print("=== Hospital Network Nodes ===")
        for node in self.nodes.values():
            print(f"  {node}")
        print("\n=== Links (weight = cost) ===")
        for a, b, data in self.graph.edges(data=True):
            print(f"  {a} <-> {b}  (weight={data['weight']})")

    def draw(self):
        """Visualizes the topology as a graph diagram."""
        pos = nx.spring_layout(self.graph, seed=42)
        labels = {nid: f"{n.name}" for nid, n in self.nodes.items()}
        colors = []
        color_map = {
            "SERVER": "gray", "ICU": "red", "DOCTOR": "blue",
            "NURSE": "green", "EMERGENCY": "orange",
            "LAB": "purple", "PHARMACY": "brown"
        }
        for nid in self.graph.nodes:
            colors.append(color_map[self.nodes[nid].node_type])

        nx.draw(
            self.graph, pos, labels=labels, node_color=colors,
            node_size=1800, font_size=7, font_color="white"
        )
        edge_labels = nx.get_edge_attributes(self.graph, "weight")
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels)
        plt.title("Hospital Network Topology")
        plt.show()


if __name__ == "__main__":
    network = HospitalNetwork()
    network.show_topology()
    network.draw()