# AES credential setup — Linux

## Prerequisites

**RHEL / CentOS / Oracle Linux:**
```bash
sudo dnf install -y python3 python3-pip
pip3 install cryptography
```

**Ubuntu / Debian:**
```bash
sudo apt-get update && sudo apt-get install -y python3 python3-pip
pip3 install cryptography
```

Verify:
```bash
python3 -c "from cryptography.hazmat.primitives.ciphers.aead import AESGCM; print('[OK] cryptography installed')"
```

---

## Steps

### 1. Set up working directory

```bash
mkdir -p ~/vault-setup && cd ~/vault-setup
```

Copy `aes_encrypt.py` from this repo into `~/vault-setup`.

---

### 2. Generate the AES master key

```bash
python3 aes_encrypt.py --generate-key
```

Expected output:
```
[OK] AES key generated and saved to 'vault.key'

     export OTEL_AES_CREDENTIAL_PROVIDER="<your-base64-key>"
```

Verify key file permissions (set to `600` automatically):
```bash
ls -la ~/vault-setup/vault.key
# Expected: -rw-------
```

---

### 3. Encrypt credentials

```bash
python3 aes_encrypt.py --encrypt --username "your_username" --password "your_password"
```

Expected output:
```
============================================================
  Paste these into your config.yaml:
============================================================
    username: "${aes:BASE64_ENCRYPTED_USERNAME}"
    password: "${aes:BASE64_ENCRYPTED_PASSWORD}"
============================================================
```

---

### 4. Verify encryption (optional)

```bash
python3 aes_encrypt.py --encrypt --username "your_username" --password "your_password" --verify
```

Expected output:
```
  [PASS]  username: 'your_username'
  [PASS]  password: 'your_password'
```

---

### 5. Update `config.yaml`

```yaml
receivers:
  nrsqlserver:
    server: "your-sql-server.com"
    port: 1433
    # Encrypted credentials are referenced here using ${aes:...} placeholders
    username: "${aes:YOUR_ENCRYPTED_USERNAME_HERE}"
    password: "${aes:YOUR_ENCRYPTED_PASSWORD_HERE}"
```

---

### 6. Set `OTEL_AES_CREDENTIAL_PROVIDER` environment variable

```bash
sudo bash -c 'echo "OTEL_AES_CREDENTIAL_PROVIDER=$(cat ~/vault-setup/vault.key)" >> /etc/nrdot-collector-host/nrdot-collector-host.conf'

# Verify
grep OTEL_AES_CREDENTIAL_PROVIDER /etc/nrdot-collector-host/nrdot-collector-host.conf
```

---

### 7. Restart the collector

```bash
sudo systemctl daemon-reload
sudo systemctl restart nrdot-collector-host
sudo systemctl status nrdot-collector-host
```
