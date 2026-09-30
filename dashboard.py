"""
dashboard.py
Visualizes performance metrics as bar/line charts for the final report.
"""

import matplotlib.pyplot as plt
from analyzer import PacketAnalyzer
from congestion import simulate_traffic


def plot_performance_comparison(all_metrics: list[dict]):
    """
    Plots packet loss %, throughput, and retransmission % across
    traffic scenarios as grouped bar charts.
    """
    labels = [m["label"] for m in all_metrics]
    packet_loss = [m["packet_loss_percent"] for m in all_metrics]
    throughput = [m["throughput_fps"] for m in all_metrics]
    retransmission = [m["retransmission_rate_percent"] for m in all_metrics]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    axes[0].bar(labels, packet_loss, color="crimson")
    axes[0].set_title("Packet Loss %")
    axes[0].set_ylabel("%")
    axes[0].tick_params(axis="x", rotation=20)

    axes[1].bar(labels, throughput, color="steelblue")
    axes[1].set_title("Throughput (frames/sec)")
    axes[1].set_ylabel("frames/sec")
    axes[1].tick_params(axis="x", rotation=20)

    axes[2].bar(labels, retransmission, color="darkorange")
    axes[2].set_title("Retransmission Rate %")
    axes[2].set_ylabel("%")
    axes[2].tick_params(axis="x", rotation=20)

    fig.suptitle("Network Performance Under Different Traffic Conditions")
    plt.tight_layout()
    plt.savefig("performance_comparison.png", dpi=150)
    print("Saved: performance_comparison.png")
    plt.show()


def plot_congestion_window():
    """
    Plots cwin (congestion window) growth over time for light vs.
    heavy traffic, showing AIMD behavior visually.
    """
    light = simulate_traffic("Light traffic", num_rounds=15,
                              error_rate=0.05, loss_rate=0.02)
    heavy = simulate_traffic("Heavy/lossy traffic", num_rounds=15,
                              error_rate=0.35, loss_rate=0.25)

    plt.figure(figsize=(9, 5))
    plt.plot(light.cwin_history, label="Light traffic", marker="o", color="green")
    plt.plot(heavy.cwin_history, label="Heavy/lossy traffic", marker="o", color="red")
    plt.xlabel("Round")
    plt.ylabel("Congestion Window (cwin)")
    plt.title("Congestion Window (AIMD) Over Time")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("congestion_window.png", dpi=150)
    print("Saved: congestion_window.png")
    plt.show()


if __name__ == "__main__":
    print("=== Building Performance Dashboard ===\n")

    scenarios = [
        ("Light traffic",        30, 4, 0.05, 0.02),
        ("Normal traffic",       30, 4, 0.15, 0.10),
        ("Heavy traffic",        30, 4, 0.30, 0.20),
        ("Severe/lossy traffic", 30, 4, 0.50, 0.35),
    ]

    all_results = []
    for label, num_frames, window_size, error_rate, loss_rate in scenarios:
        analyzer = PacketAnalyzer(label)
        result = analyzer.run_scenario(num_frames, window_size, error_rate, loss_rate)
        all_results.append(result)

    plot_performance_comparison(all_results)
    plot_congestion_window()

    print("\nDashboard complete. Both PNGs saved in your project folder.")