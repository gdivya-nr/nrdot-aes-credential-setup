"""
AES Encryption Utility for NRDOT Collector confmap aesprovider
--------------------------------------------------------------
Uses AES-256-GCM to encrypt credentials.
Encrypted values are used directly in config.yaml as ${aes:...}
The collector decrypts them natively using OTEL_AES_CREDENTIAL_PROVIDER env var.
"""

import os
import base64
import json
import sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_FILE   = "vault.key"
VAULT_FILE = "vault.enc"


# ── Key Management ─────────────────────────────────────────────────────────────

def generate_key() -> str:
    """Generate a new 256-bit AES key and save to vault.key"""
    key_bytes = os.urandom(32)
    key_b64   = base64.b64encode(key_bytes).decode()

    with open(KEY_FILE, "w") as f:
        f.write(key_b64)
    os.chmod(KEY_FILE, 0o600)

    print(f"[OK] AES key generated and saved to '{KEY_FILE}'")
    print(f"\n     export OTEL_AES_CREDENTIAL_PROVIDER=\"{key_b64}\"\n")
    return key_b64


def load_key() -> bytes:
    """Load AES key from vault.key file"""
    if not os.path.exists(KEY_FILE):
        raise FileNotFoundError(
            f"Key file '{KEY_FILE}' not found. Run: python3 aes_encrypt.py --generate-key"
        )
    with open(KEY_FILE, "r") as f:
        return base64.b64decode(f.read().strip())


# ── Encrypt / Decrypt ──────────────────────────────────────────────────────────

def encrypt(plaintext: str) -> str:
    """
    Encrypt a plaintext string using AES-256-GCM.
    Output format: base64(nonce + ciphertext) — matches aesprovider expected format.
    """
    key    = load_key()
    aesgcm = AESGCM(key)
    nonce  = os.urandom(12)          # 96-bit nonce (GCM standard)
    ct     = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ct).decode()


def decrypt(encrypted_b64: str) -> str:
    """
    Decrypt an AES-256-GCM encrypted base64 string.
    Useful for verifying encrypted values are correct.
    """
    key        = load_key()
    aesgcm     = AESGCM(key)
    raw        = base64.b64decode(encrypted_b64)
    nonce, ct  = raw[:12], raw[12:]
    return aesgcm.decrypt(nonce, ct, None).decode()


# ── Vault File ─────────────────────────────────────────────────────────────────

def save_vault(credentials: dict):
    """Save encrypted credentials to vault.enc for reference"""
    encrypted = {k: encrypt(v) for k, v in credentials.items()}
    with open(VAULT_FILE, "w") as f:
        json.dump(encrypted, f, indent=2)
    os.chmod(VAULT_FILE, 0o600)
    print(f"[OK] Encrypted vault saved to '{VAULT_FILE}'")


# ── CLI ────────────────────────────────────────────────────────────────────────

def print_config_snippet(credentials: dict):
    print("\n" + "="*60)
    print("  Paste these into your config.yaml:")
    print("="*60)
    for key, value in credentials.items():
        enc = encrypt(value)
        print(f'    {key}: "${{{aes:{enc}}}}"')
    print("="*60 + "\n")


def verify_encryption(credentials: dict):
    print("\n" + "="*60)
    print("  Verification (decrypt check):")
    print("="*60)
    for key, value in credentials.items():
        enc       = encrypt(value)
        decrypted = decrypt(enc)
        status    = "[PASS]" if decrypted == value else "[FAIL]"
        print(f"  {status}  {key}: '{decrypted}'")
    print("="*60 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="AES-256-GCM credential encryptor for NRDOT aesprovider"
    )
    parser.add_argument("--generate-key",  action="store_true", help="Generate a new AES key")
    parser.add_argument("--encrypt",       action="store_true", help="Encrypt credentials")
    parser.add_argument("--verify",        action="store_true", help="Verify encryption/decryption")
    parser.add_argument("--username",      type=str,            help="Username to encrypt")
    parser.add_argument("--password",      type=str,            help="Password to encrypt")
    parser.add_argument("--decrypt-value", type=str,            help="Decrypt a single encrypted value")

    args = parser.parse_args()

    if args.generate_key:
        generate_key()
        sys.exit(0)

    if args.decrypt_value:
        try:
            result = decrypt(args.decrypt_value)
            print(f"[OK] Decrypted value: '{result}'")
        except Exception as e:
            print(f"[FAIL] Decryption failed: {e}")
        sys.exit(0)

    if args.encrypt or args.username or args.password:
        if not args.username or not args.password:
            print("[ERROR] Both --username and --password are required.")
            parser.print_help()
            sys.exit(1)

        credentials = {
            "username": args.username,
            "password": args.password,
        }

        save_vault(credentials)
        print_config_snippet(credentials)

        if args.verify:
            verify_encryption(credentials)

        sys.exit(0)

    parser.print_help()
