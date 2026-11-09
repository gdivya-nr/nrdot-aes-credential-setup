# NRDOT AES Credential Setup

This repository provides a reference implementation for encrypting database credentials
used with the NRDOT OpenTelemetry Collector's built-in AES provider (`aesprovider`).

> **Note**: This is a sample reference only.
> Any tool that produces AES-256-GCM encrypted output in `base64(nonce + ciphertext)`
> format (standard base64, 12-byte nonce) is compatible with the `aesprovider`.

## How it works

- **Master key**: A unique 32-byte AES-256 key is generated and stored in the server's
  environment variable (`OTEL_AES_CREDENTIAL_PROVIDER`).
- **Encryption**: Credentials are encrypted offline using AES-256-GCM.
- **Config**: `config.yaml` references encrypted strings using `${aes:<encrypted-value>}` placeholders.
- **Runtime**: The collector reads the master key from the environment and decrypts credentials in memory.

## Setup guides

- [Windows setup](docs/windows-setup.md)
- [Linux setup](docs/linux-setup.md)

## Reference script

- [`aes_encrypt.py`](aes_encrypt.py) — AES-256-GCM encryption utility
