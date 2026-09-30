"""
flow_control.py
Implements sliding window flow control + ARQ (retransmission on error/loss),
with priority-aware sending so urgent frames (e.g. EMERGENCY) are sent
before routine or low-priority traffic. Re-encrypts payload fresh on
every retry since Frame stores the transmitted payload in encrypted form.
"""

import random
from framing import Frame, transmit_with_errors
from security import xor_encrypt


class SlidingWindowSender:
    """
    Sends frames using a sliding window: up to `window_size` frames
    can be "in flight" (sent but not yet acknowledged) at once.
    Any frame that comes back NAK'd (or never gets ACK'd -> simulated
    as lost) is retransmitted until it succeeds or max retries is hit.
    """

    def __init__(self, window_size: int = 4, max_retries: int = 5,
                 error_rate: float = 0.3, loss_rate: float = 0.15):
        self.window_size = window_size
        self.max_retries = max_retries
        self.error_rate = error_rate   # chance a frame gets corrupted in transit
        self.loss_rate = loss_rate     # chance a frame is dropped entirely (never arrives)

        # Stats reused by the packet analyzer
        self.total_sent = 0
        self.total_retransmissions = 0
        self.total_dropped_permanently = 0
        self.total_delivered = 0

    def _transmit_one_attempt(self, frame: Frame) -> str:
        """
        Simulates ONE attempt to send a frame across the link.
        Returns: 'ACK' (delivered correctly), 'NAK' (arrived but corrupted),
                 or 'LOST' (never arrived at all).
        """
        self.total_sent += 1

        # Simulate total packet loss (frame never reaches destination)
        if random.random() < self.loss_rate:
            return "LOST"

        # Simulate transmission with possible corruption
        received_frame = transmit_with_errors(frame, error_rate=self.error_rate)

        if received_frame.verify():
            return "ACK"
        else:
            return "NAK"

    def send_frame(self, frame: Frame) -> bool:
        """
        Sends a single frame, retransmitting on NAK/LOST up to max_retries.
        Returns True if eventually delivered, False if it exhausted retries.
        """
        attempts = 0
        while attempts <= self.max_retries:
            result = self._transmit_one_attempt(frame)

            if result == "ACK":
                if attempts > 0:
                    print(f"  [Frame {frame.seq_num}] Delivered after {attempts} retransmission(s).")
                else:
                    print(f"  [Frame {frame.seq_num}] Delivered on first attempt.")
                print(f"  [Frame {frame.seq_num}] Decrypted at receiver: '{frame.get_decrypted_payload()}'")
                self.total_delivered += 1
                return True

            # NAK or LOST -> retransmit
            attempts += 1
            self.total_retransmissions += 1
            status_word = "corrupted (NAK)" if result == "NAK" else "lost"
            print(f"  [Frame {frame.seq_num}] Attempt {attempts}: {status_word} -> retransmitting...")

            # Re-encrypt the CLEAN original text fresh on every retry.
            # frame.payload holds the ENCRYPTED (possibly corrupted-in-place)
            # version, so we must rebuild it from frame.original_payload
            # rather than reusing whatever is currently in frame.payload.
            frame.payload = xor_encrypt(frame.original_payload)
            frame.checksum = frame._compute_checksum(frame.payload)
            frame.corrupted = False

        print(f"  [Frame {frame.seq_num}] FAILED after {self.max_retries} retries -> giving up.")
        self.total_dropped_permanently += 1
        return False

    def send_window(self, frames: list[Frame]):
        """
        Sends frames in priority order first (EMERGENCY before ROUTINE
        before LOW), then in sliding-window-sized batches within that
        order. This ensures a critical alert never waits behind routine
        traffic just because it arrived later in the queue.
        """
        sorted_frames = sorted(frames, key=lambda f: -f.priority_value())

        for i in range(0, len(sorted_frames), self.window_size):
            batch = sorted_frames[i:i + self.window_size]
            labels = [f"{f.seq_num}({f.priority})" for f in batch]
            print(f"\n--- Sending window: frames {labels} ---")
            for frame in batch:
                self.send_frame(frame)

    def print_stats(self):
        print("\n=== Flow Control / ARQ Stats ===")
        print(f"  Total transmission attempts : {self.total_sent}")
        print(f"  Total retransmissions       : {self.total_retransmissions}")
        print(f"  Successfully delivered      : {self.total_delivered}")
        print(f"  Permanently failed          : {self.total_dropped_permanently}")


if __name__ == "__main__":
    print("=== Sliding Window + ARQ Demo (Priority-Aware, Encrypted) ===")

    messages = [
        ("ICU1", "DOC1", "Patient BP: 180/120", "ROUTINE"),
        ("ICU1", "DOC1", "Heart Rate: 95 bpm", "ROUTINE"),
        ("EMR1", "DOC1", "CODE BLUE: cardiac arrest room 4", "EMERGENCY"),
        ("LAB1", "DOC1", "Blood test: Glucose 140 mg/dL", "ROUTINE"),
        ("NUR1", "ICU1", "Medication administered: 500mg", "ROUTINE"),
        ("ICU2", "DOC1", "Oxygen saturation: 92%", "ROUTINE"),
        ("EMR1", "NUR1", "Incoming ambulance, prep bed 3", "EMERGENCY"),
        ("PHR1", "SRV", "Stock update: paracetamol low", "LOW"),
    ]

    frames = [Frame(src, dst, i, payload, priority)
              for i, (src, dst, payload, priority) in enumerate(messages)]

    sender = SlidingWindowSender(window_size=3, max_retries=4, error_rate=0.3, loss_rate=0.15)
    sender.send_window(frames)
    sender.print_stats()