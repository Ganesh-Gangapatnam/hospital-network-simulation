"""
framing.py
Defines the data frame format, CRC-32 error detection, priority, and
an encryption layer for payload confidentiality.
"""

import random
import zlib
from security import xor_encrypt, xor_decrypt

PRIORITY = {
    "EMERGENCY": 3,
    "ROUTINE": 2,
    "LOW": 1,
}


class Frame:
    """
    Represents one transmitted unit of data between hospital nodes.

    Structure:
      - src, dst           : sender and receiver node IDs
      - seq_num            : sequence number (used for ordering/ARQ)
      - original_payload   : the READABLE message, kept for display/reporting
      - payload            : the ENCRYPTED version -- this is what actually
                              gets "transmitted" and checksummed
      - priority           : "EMERGENCY" | "ROUTINE" | "LOW"
      - checksum           : CRC-32 of the ENCRYPTED payload
      - corrupted          : flag set only by the corruption simulator
    """

    def __init__(self, src: str, dst: str, seq_num: int, payload: str, priority: str = "ROUTINE"):
        self.src = src
        self.dst = dst
        self.seq_num = seq_num
        self.original_payload = payload            # readable text, kept for display
        self.payload = xor_encrypt(payload)         # encrypted text -- this is what's "sent"
        self.priority = priority if priority in PRIORITY else "ROUTINE"
        self.checksum = self._compute_checksum(self.payload)
        self.corrupted = False

    @staticmethod
    def _compute_checksum(payload: str) -> int:
        """Real CRC-32 checksum, computed on the ENCRYPTED payload."""
        return zlib.crc32(payload.encode("utf-8", errors="surrogatepass"))

    def verify(self) -> bool:
        """Recomputes CRC-32 from the current (encrypted) payload and compares."""
        return self._compute_checksum(self.payload) == self.checksum

    def get_decrypted_payload(self) -> str:
        """Decrypts the current payload back to readable text (receiving end)."""
        return xor_decrypt(self.payload)

    def priority_value(self) -> int:
        return PRIORITY[self.priority]

    def __repr__(self):
        status = "CORRUPTED" if self.corrupted else "OK"
        return f"Frame(seq={self.seq_num}, {self.src}->{self.dst}, [{self.priority}], encrypted='{self.payload!r}', {status})"


def corrupt_frame(frame: Frame) -> Frame:
    """
    Simulates a transmission error by altering one character in the
    ENCRYPTED payload, without updating the checksum.
    """
    if len(frame.payload) == 0:
        return frame

    payload_list = list(frame.payload)
    idx = random.randint(0, len(payload_list) - 1)
    original_char = payload_list[idx]
    new_char = chr((ord(original_char) + random.randint(1, 25)) % 1114111)
    payload_list[idx] = new_char

    frame.payload = "".join(payload_list)
    frame.corrupted = True
    return frame


def transmit_with_errors(frame: Frame, error_rate: float = 0.2) -> Frame:
    """Simulates sending a frame across a noisy link."""
    if random.random() < error_rate:
        frame = corrupt_frame(frame)
    return frame


if __name__ == "__main__":
    print("=== Framing, Encryption & Error Detection Demo ===\n")

    messages = [
        ("ICU1", "DOC1", "Patient BP: 180/120", "ROUTINE"),
        ("EMR1", "DOC1", "CODE BLUE: cardiac arrest room 4", "EMERGENCY"),
        ("LAB1", "DOC1", "Blood test: Glucose 140 mg/dL", "ROUTINE"),
        ("PHR1", "SRV", "Stock update: paracetamol low", "LOW"),
    ]

    for i, (src, dst, payload, priority) in enumerate(messages):
        frame = Frame(src, dst, i, payload, priority)
        print(f"Original message : '{payload}'")
        print(f"Encrypted payload: {frame.payload!r}")

        frame = transmit_with_errors(frame, error_rate=0.5)

        if frame.verify():
            print(f"Checksum OK -> accepted")
            print(f"Decrypted at receiver: '{frame.get_decrypted_payload()}'\n")
        else:
            print(f"CRC-32 MISMATCH -> corruption detected, REJECTED\n")