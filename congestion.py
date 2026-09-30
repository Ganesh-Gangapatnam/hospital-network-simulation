"""
congestion.py
Implements AIMD (Additive Increase / Multiplicative Decrease) congestion control,
simulating how the network adapts its sending rate under varying traffic load.
"""

import random
from framing import Frame, transmit_with_errors


class CongestionController:
    """
    Manages a congestion window (cwin) that grows on success and shrinks
    sharply on failure -- the same principle real TCP uses to avoid
    overwhelming a congested network.
    """

    def __init__(self, initial_cwin: int = 1, max_cwin: int = 16,
                 min_cwin: int = 1):
        self.cwin = initial_cwin
        self.max_cwin = max_cwin
        self.min_cwin = min_cwin

        # History for plotting later (Phase 7 dashboard)
        self.cwin_history: list[int] = [initial_cwin]
        self.event_log: list[str] = []

    def on_success(self):
        """
        Additive Increase: cwin grows by 1 per successful round,
        capped at max_cwin. Slow, steady ramp-up -- avoids immediately
        re-triggering congestion right after backing off.
        """
        self.cwin = min(self.cwin + 1, self.max_cwin)
        self.cwin_history.append(self.cwin)
        self.event_log.append(f"SUCCESS -> cwin={self.cwin}")

    def on_failure(self):
        """
        Multiplicative Decrease: cwin is halved on any failure
        (loss/corruption), floored at min_cwin. Sharp backoff --
        reacts fast to real congestion/errors.
        """
        self.cwin = max(self.cwin // 2, self.min_cwin)
        self.cwin_history.append(self.cwin)
        self.event_log.append(f"FAILURE -> cwin={self.cwin}")


def simulate_traffic(label: str, num_rounds: int, error_rate: float, loss_rate: float):
    """
    Simulates a traffic scenario: for each round, attempts to send
    `cwin` frames simultaneously (bounded by congestion window),
    and updates cwin based on whether any failures occurred.
    """
    print(f"\n=== Scenario: {label} (error_rate={error_rate}, loss_rate={loss_rate}) ===")

    controller = CongestionController(initial_cwin=1, max_cwin=16)
    total_frames_sent = 0
    total_failures = 0

    for round_num in range(1, num_rounds + 1):
        batch_size = controller.cwin
        failures_this_round = 0

        for i in range(batch_size):
            frame = Frame("ICU1", "DOC1", i, "Vitals data packet")
            total_frames_sent += 1

            # Simulate loss
            if random.random() < loss_rate:
                failures_this_round += 1
                continue

            # Simulate corruption
            frame = transmit_with_errors(frame, error_rate=error_rate)
            if not frame.verify():
                failures_this_round += 1

        total_failures += failures_this_round

        if failures_this_round > 0:
            controller.on_failure()
        else:
            controller.on_success()

        print(f"  Round {round_num:2d}: sent {batch_size:2d} frames, "
              f"{failures_this_round} failed -> cwin now {controller.cwin}")

    print(f"\n  Summary: {total_frames_sent} total frames sent, "
          f"{total_failures} total failures, "
          f"final cwin={controller.cwin}")
    return controller


if __name__ == "__main__":
    print("=== Congestion Control (AIMD) Demo ===")

    # Scenario 1: Light, clean traffic -- expect cwin to climb steadily
    light = simulate_traffic("Light traffic", num_rounds=15,
                              error_rate=0.05, loss_rate=0.02)

    # Scenario 2: Heavy, lossy traffic -- expect cwin to stay low / oscillate
    heavy = simulate_traffic("Heavy/lossy traffic", num_rounds=15,
                              error_rate=0.35, loss_rate=0.25)

    print("\n=== cwin history comparison ===")
    print(f"  Light traffic cwin path : {light.cwin_history}")
    print(f"  Heavy traffic cwin path : {heavy.cwin_history}")