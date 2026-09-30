"""
analyzer.py
Collects performance metrics from simulation runs, produces comparative
statistics (packet loss %, throughput, latency, retransmissions, routing
cost), and logs every run's results to a CSV file for historical record.
"""

import time
import csv
import os
from datetime import datetime
from framing import Frame
from flow_control import SlidingWindowSender
from nodes import HospitalNetwork
from routing import Router


class PacketAnalyzer:
    """
    Runs a batch of frames through a SlidingWindowSender under given
    traffic conditions, records delivery/performance metrics, and also
    tracks the routing cost (Dijkstra path weight) for the src->dst pair
    used in that scenario.
    """

    def __init__(self, label: str, router: Router = None):
        self.label = label
        self.metrics = {}
        # Reuse a shared Router/network if given, else create a fresh one.
        self.router = router if router is not None else Router(HospitalNetwork())

    def run_scenario(self, num_frames: int, window_size: int,
                      error_rate: float, loss_rate: float,
                      src: str = "ICU1", dst: str = "DOC1", max_retries: int = 4):
        messages = [
            (src, dst, f"Vitals packet #{i}") for i in range(num_frames)
        ]
        frames = [Frame(s, d, i, payload) for i, (s, d, payload) in enumerate(messages)]

        sender = SlidingWindowSender(
            window_size=window_size, max_retries=max_retries,
            error_rate=error_rate, loss_rate=loss_rate
        )

        # --- Routing: find the current best path for this src->dst pair ---
        path, path_cost = self.router.find_path(src, dst)
        path_str = " -> ".join(path) if path else "NO PATH"

        start_time = time.perf_counter()
        import io
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            sender.send_window(frames)
        elapsed = time.perf_counter() - start_time

        total_delivered = sender.total_delivered
        total_failed = sender.total_dropped_permanently
        total_attempts = sender.total_sent
        total_retransmissions = sender.total_retransmissions

        packet_loss_percent = (total_failed / num_frames) * 100 if num_frames else 0
        throughput = total_delivered / elapsed if elapsed > 0 else 0
        retransmission_rate = (total_retransmissions / total_attempts) * 100 if total_attempts else 0
        avg_latency_ms = (elapsed / num_frames) * 1000 if num_frames else 0

        self.metrics = {
            "label": self.label,
            "src": src,
            "dst": dst,
            "route": path_str,
            "route_cost": path_cost if path_cost is not None else -1,
            "num_frames": num_frames,
            "delivered": total_delivered,
            "permanently_failed": total_failed,
            "total_attempts": total_attempts,
            "retransmissions": total_retransmissions,
            "packet_loss_percent": round(packet_loss_percent, 2),
            "throughput_fps": round(throughput, 2),
            "retransmission_rate_percent": round(retransmission_rate, 2),
            "avg_latency_ms": round(avg_latency_ms, 3),
            "elapsed_sec": round(elapsed, 4),
        }
        return self.metrics


def print_comparison_table(all_metrics):
    headers = ["Scenario", "Route", "Cost", "Delivered", "Failed", "Loss %", "Retrans %", "Throughput (fps)"]
    print("\n" + " | ".join(f"{h:>14}" for h in headers))
    print("-" * (17 * len(headers)))
    for m in all_metrics:
        row = [
            m["label"], m["route"], str(m["route_cost"]),
            str(m["delivered"]), str(m["permanently_failed"]),
            f"{m['packet_loss_percent']}%", f"{m['retransmission_rate_percent']}%",
            str(m["throughput_fps"]),
        ]
        print(" | ".join(f"{v:>14}" for v in row))


def save_results_to_csv(all_metrics, filename="results_log.csv"):
    fieldnames = [
        "timestamp", "label", "src", "dst", "route", "route_cost",
        "num_frames", "delivered", "permanently_failed",
        "total_attempts", "retransmissions", "packet_loss_percent",
        "throughput_fps", "retransmission_rate_percent", "avg_latency_ms",
        "elapsed_sec"
    ]
    file_exists = os.path.isfile(filename)
    with open(filename, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for m in all_metrics:
            row = {"timestamp": timestamp, **m}
            writer.writerow(row)
    print(f"\nResults appended to {filename}")


if __name__ == "__main__":
    print("=== Packet Analyzer: Performance + Routing Cost Under Different Traffic ===")

    # Shared router/network so we can show routing cost changing across scenarios
    shared_router = Router(HospitalNetwork())

    scenarios = [
        # (label, num_frames, window_size, error_rate, loss_rate)
        ("Light traffic",        30, 4, 0.05, 0.02),
        ("Normal traffic",       30, 4, 0.15, 0.10),
        ("Heavy traffic",        30, 4, 0.30, 0.20),
        ("Severe/lossy traffic", 30, 4, 0.50, 0.35),
    ]

    all_results = []
    for i, (label, num_frames, window_size, error_rate, loss_rate) in enumerate(scenarios):
        # Simulate the direct ICU1<->DOC1 link getting progressively more
        # congested as traffic gets heavier, so routing cost visibly
        # changes across scenarios (demonstrates rerouting under load).
        if i == 2:  # before "Heavy traffic"
            shared_router.simulate_congestion("ICU1", "DOC1", extra_cost=5)
        elif i == 3:  # before "Severe/lossy traffic"
            shared_router.simulate_congestion("ICU1", "DOC1", extra_cost=10)

        analyzer = PacketAnalyzer(label, router=shared_router)
        result = analyzer.run_scenario(num_frames, window_size, error_rate, loss_rate)
        all_results.append(result)

    print_comparison_table(all_results)
    save_results_to_csv(all_results)