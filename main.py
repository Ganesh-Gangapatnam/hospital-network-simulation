"""
main.py
Entry point: runs the complete hospital network simulation end-to-end.
"""

from network_sim import NetworkSimulator


def main():
    simulator = NetworkSimulator()
    simulator.run_full_demo()


if __name__ == "__main__":
    main()