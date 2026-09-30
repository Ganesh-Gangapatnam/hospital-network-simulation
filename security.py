"""
security.py
Simple XOR-based encryption/decryption layer, simulating confidentiality
for patient data in transit.
"""

SECRET_KEY = "H0SP1TAL_KEY"


def xor_encrypt(plaintext: str, key: str = SECRET_KEY) -> str:
    """Encrypts plaintext by XOR-ing each character with a repeating key."""
    return "".join(
        chr(ord(char) ^ ord(key[i % len(key)]))
        for i, char in enumerate(plaintext)
    )


def xor_decrypt(ciphertext: str, key: str = SECRET_KEY) -> str:
    """XOR decryption is identical to encryption (XOR is its own inverse)."""
    return xor_encrypt(ciphertext, key)


if __name__ == "__main__":
    print("=== Encryption Layer Demo ===\n")

    messages = [
        "Patient BP: 180/120",
        "CODE BLUE: cardiac arrest room 4",
        "Blood test: Glucose 140 mg/dL",
    ]

    for msg in messages:
        encrypted = xor_encrypt(msg)
        decrypted = xor_decrypt(encrypted)

        print(f"Original : {msg}")
        print(f"Encrypted: {encrypted!r}  (unreadable in transit)")
        print(f"Decrypted: {decrypted}")
        print(f"Match original: {decrypted == msg}\n")