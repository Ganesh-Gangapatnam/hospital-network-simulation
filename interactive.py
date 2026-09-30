"""
interactive.py
Interactive command-line demo: type a message, pick source/destination,
and watch it go through framing, error detection, ARQ, and routing live.
"""

from nodes import HospitalNetwork
from framing import Frame, transmit_with_errors, PRIORITY
from flow_control import SlidingWindowSender
from routing import Router, print_path_result


def choose_node(prompt: str, network: HospitalNetwork) -> str:
    while True:
        node_id = input(prompt).strip().upper()
        if node_id in network.nodes:
            return node_id
        print(f"  '{node_id}' not found. Valid nodes: {list(network.nodes.keys())}")


def choose_priority() -> str:
    options = list(PRIORITY.keys())
    while True:
        raw = input(f"  Priority {options} [default ROUTINE]: ").strip().upper()
        if raw == "":
            return "ROUTINE"
        if raw in PRIORITY:
            return raw
        print(f"  Invalid priority. Choose from {options}.")


def run_interactive():
    network = HospitalNetwork()
    router = Router(network)
    seq_counter = 0

    print("=== Interactive Hospital Network Demo ===")
    print(f"Available nodes: {list(network.nodes.keys())}")
    print("Type 'quit' at any prompt to exit.\n")

    while True:
        src = choose_node("\nSource node (e.g. ICU1): ", network)
        if src == "QUIT":
            break
        dst = choose_node("Destination node (e.g. DOC1): ", network)
        if dst == "QUIT":
            break

        message = input("Message text: ").strip()
        if message.lower() == "quit":
            break

        priority = choose_priority()

        # --- Routing: show the chosen path before sending ---
        path_result = router.find_path(src, dst)
        print_path_result(f"Route {src} -> {dst}", path_result)

        # --- Framing + transmission + ARQ ---
        frame = Frame(src, dst, seq_counter, message, priority)
        frame._original_payload = frame.payload
        seq_counter += 1

        sender = SlidingWindowSender(window_size=1, max_retries=4, error_rate=0.3, loss_rate=0.15)
        print(f"\nSending frame: {frame}")
        sender.send_frame(frame)
        sender.print_stats()

        again = input("\nSend another message? (y/n): ").strip().lower()
        if again != "y":
            break

    print("\nInteractive demo ended.")


if __name__ == "__main__":
    run_interactive()