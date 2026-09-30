"""
routing.py
Implements Dijkstra-based shortest-path routing over the hospital network graph,
with support for simulating link failure/congestion and automatic rerouting.
"""

import networkx as nx
from nodes import HospitalNetwork


class Router:
    """
    Wraps the HospitalNetwork graph and provides path-finding,
    including handling link failures/congestion by rerouting.
    """

    def __init__(self, network: HospitalNetwork):
        self.network = network
        self.graph = network.graph

    def find_path(self, src: str, dst: str) -> list[str] | None:
        """
        Returns the lowest-cost path from src to dst using Dijkstra's
        algorithm (via networkx's shortest_path, weighted by 'weight').
        Returns None if no path exists (e.g. network partitioned).
        """
        try:
            path = nx.dijkstra_path(self.graph, src, dst, weight="weight")
            cost = nx.dijkstra_path_length(self.graph, src, dst, weight="weight")
            return path, cost
        except nx.NetworkXNoPath:
            return None, None
        except nx.NodeNotFound as e:
            print(f"  Routing error: {e}")
            return None, None

    def simulate_congestion(self, node_a: str, node_b: str, extra_cost: int):
        """
        Simulates a link becoming congested by temporarily increasing its weight.
        A congested link is still usable, just less attractive to Dijkstra --
        it will be avoided in favor of alternate paths if one is cheaper overall.
        """
        if self.graph.has_edge(node_a, node_b):
            old_weight = self.graph[node_a][node_b]["weight"]
            self.graph[node_a][node_b]["weight"] = old_weight + extra_cost
            print(f"  [Congestion] Link {node_a}<->{node_b} weight: {old_weight} -> {old_weight + extra_cost}")
        else:
            print(f"  [Congestion] No direct link {node_a}<->{node_b} to congest.")

    def simulate_link_failure(self, node_a: str, node_b: str):
        """
        Simulates a total link failure by removing the edge entirely.
        Forces Dijkstra to find a completely different path, if one exists.
        """
        if self.graph.has_edge(node_a, node_b):
            weight = self.graph[node_a][node_b]["weight"]
            self.graph.remove_edge(node_a, node_b)
            print(f"  [Failure] Link {node_a}<->{node_b} (was weight={weight}) is now DOWN.")
            return (node_a, node_b, weight)  # so we can restore it later
        else:
            print(f"  [Failure] No direct link {node_a}<->{node_b} to fail.")
            return None

    def restore_link(self, failed_link):
        """Restores a previously failed link (undoes simulate_link_failure)."""
        if failed_link:
            node_a, node_b, weight = failed_link
            self.graph.add_edge(node_a, node_b, weight=weight)
            print(f"  [Recovery] Link {node_a}<->{node_b} restored (weight={weight}).")


def print_path_result(label: str, path_result):
    path, cost = path_result
    if path is None:
        print(f"  {label}: NO PATH AVAILABLE")
    else:
        route_str = " -> ".join(path)
        print(f"  {label}: {route_str}  (total cost={cost})")


if __name__ == "__main__":
    print("=== Dijkstra Routing Demo ===\n")

    network = HospitalNetwork()
    router = Router(network)

    # --- 1. Normal routing ---
    print("1) Normal conditions:")
    print_path_result("ICU1 -> DOC1", router.find_path("ICU1", "DOC1"))
    print_path_result("EMR1 -> LAB1", router.find_path("EMR1", "LAB1"))
    print_path_result("NUR1 -> PHR1", router.find_path("NUR1", "PHR1"))

    # --- 2. Simulate congestion on the cheapest ICU1<->DOC1 path ---
    print("\n2) After congesting the direct ICU1<->DOC1 link:")
    router.simulate_congestion("ICU1", "DOC1", extra_cost=10)
    print_path_result("ICU1 -> DOC1 (rerouted?)", router.find_path("ICU1", "DOC1"))

    # --- 3. Simulate a link failure ---
    print("\n3) After the SRV<->EMR1 link fails completely:")
    failed = router.simulate_link_failure("SRV", "EMR1")
    print_path_result("EMR1 -> LAB1 (rerouted?)", router.find_path("EMR1", "LAB1"))

    # --- 4. Restore and confirm back to normal ---
    print("\n4) After restoring the failed link:")
    router.restore_link(failed)
    print_path_result("EMR1 -> LAB1 (back to normal)", router.find_path("EMR1", "LAB1"))