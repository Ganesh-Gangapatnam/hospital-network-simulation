"""
network_sim.py
Core simulation engine: orchestrates topology, framing, flow control,
routing, and congestion control into a single reusable simulation class.
main.py simply creates a NetworkSimulator and calls run_full_demo().
"""

from nodes import HospitalNetwork
from framing import Frame, transmit_with_errors
from flow_control import SlidingWindowSender
from routing import Router, print_path_result
from congestion import simulate_traffic
from analyzer import PacketAnalyzer, print_comparison_table
from dashboard import plot_performance_comparison, plot_congestion_window


class NetworkSimulator:
    """
    Ties together topology, framing, flow control, routing, congestion
    control, and analysis into one coherent hospital network simulation.
    """

    def __init__(self):
        self.network = HospitalNetwork()
        self.router = Router(self.network)

    def _section(self, title: str):
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)

    def show_topology(self):
        self._section("NETWORK TOPOLOGY")
        self.network.show_topology()
        print("\n(Close the topology graph window to continue...)")
        self.network.draw()

    def demo_framing(self):
        self._section("FRAMING & ERROR DETECTION")
        frame = Frame("ICU1", "DOC1", 0, "Patient BP: 180/120")
        original = frame.payload
        frame = transmit_with_errors(frame, error_rate=0.5)
        print(f"Sent:     '{original}'")
        print(f"Received: {frame}")
        print("Checksum OK -> accepted" if frame.verify()
              else "Checksum MISMATCH -> corruption detected, rejected")

    def demo_flow_control(self, num_frames: int = 6):
        self._section("FLOW CONTROL + ARQ (RETRANSMISSION)")
        messages = [("ICU1", "DOC1", f"Vitals packet #{i}") for i in range(num_frames)]
        frames = [Frame(s, d, i, p) for i, (s, d, p) in enumerate(messages)]
        for f in frames:
            f._original_payload = f.payload
        sender = SlidingWindowSender(window_size=3, max_retries=4, error_rate=0.3, loss_rate=0.15)
        sender.send_window(frames)
        sender.print_stats()

    def demo_routing(self):
        self._section("DIJKSTRA ROUTING")
        print_path_result("ICU1 -> DOC1 (normal)", self.router.find_path("ICU1", "DOC1"))
        self.router.simulate_congestion("ICU1", "DOC1", extra_cost=10)
        print_path_result("ICU1 -> DOC1 (after congestion)", self.router.find_path("ICU1", "DOC1"))
        failed = self.router.simulate_link_failure("SRV", "EMR1")
        print_path_result("EMR1 -> LAB1 (after link failure)", self.router.find_path("EMR1", "LAB1"))
        self.router.restore_link(failed)

    def demo_congestion(self):
        self._section("CONGESTION CONTROL (AIMD)")
        simulate_traffic("Light traffic", num_rounds=10, error_rate=0.05, loss_rate=0.02)
        simulate_traffic("Heavy/lossy traffic", num_rounds=10, error_rate=0.35, loss_rate=0.25)

    def run_performance_analysis(self):
        self._section("PACKET ANALYZER: PERFORMANCE UNDER DIFFERENT TRAFFIC")
        scenarios = [
            ("Light traffic", 30, 4, 0.05, 0.02),
            ("Normal traffic", 30, 4, 0.15, 0.10),
            ("Heavy traffic", 30, 4, 0.30, 0.20),
            ("Severe/lossy traffic", 30, 4, 0.50, 0.35),
        ]
        all_results = [
            PacketAnalyzer(label).run_scenario(n, w, er, lr)
            for label, n, w, er, lr in scenarios
        ]
        print_comparison_table(all_results)
        return all_results

    def show_dashboard(self, results: list[dict]):
        self._section("VISUAL DASHBOARD")
        print("Generating graphs... (close each window to proceed)")
        plot_performance_comparison(results)
        plot_congestion_window()

    def run_full_demo(self):
        """Runs the entire simulation pipeline end-to-end."""
        self.show_topology()
        self.demo_framing()
        self.demo_flow_control()
        self.demo_routing()
        self.demo_congestion()
        results = self.run_performance_analysis()
        self.show_dashboard(results)

        self._section("SIMULATION COMPLETE")
        print("All modules executed successfully. Graphs saved as PNG in project folder.")