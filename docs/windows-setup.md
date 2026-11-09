# AES credential setup — Windows

## Prerequisites

- Python 3: [Download for Windows](https://www.python.org/downloads/windows/)
- Install the `cryptography` library:

```powershell
pip install cryptography
```

- Verify:

```powershell
python --version
python -c "from cryptography.hazmat.primitives.ciphers.aead import AESGCM; print('[OK] cryptography installed')"
```

---

## Steps

### 1. Set up working directory

```powershell
New-Item -ItemType Directory -Path "C:\vault-setup" -Force
cd C:\vault-setup
```

Copy `aes_encrypt.py` from this repo into `C:\vault-setup`.

---

### 2. Generate the AES master key

```powershell
python aes_encrypt.py --generate-key
```

Expected output:
```
[OK] AES key generated and saved to 'vault.key'

     export OTEL_AES_CREDENTIAL_PROVIDER="<your-base64-key>"
```

Secure the key file:
```powershell
icacls "C:\vault-setup\vault.key" /inheritance:r
icacls "C:\vault-setup\vault.key" /remove "NT AUTHORITY\Authenticated Users"
icacls "C:\vault-setup\vault.key" /remove "BUILTIN\Users"
icacls "C:\vault-setup\vault.key" /grant:r "$(whoami):(F)"
```

---

### 3. Encrypt credentials

```powershell
python aes_encrypt.py --encrypt --username "your_username" --password "your_password"
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

```powershell
python aes_encrypt.py --encrypt --username "your_username" --password "your_password" --verify
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

**Permanent (recommended for production):**
```powershell
[System.Environment]::SetEnvironmentVariable(
    "OTEL_AES_CREDENTIAL_PROVIDER",
    (Get-Content C:\vault-setup\vault.key),
    "Machine"
)

# Verify
[System.Environment]::GetEnvironmentVariable("OTEL_AES_CREDENTIAL_PROVIDER", "Machine")
```

> After setting the machine-level environment variable, restart the NRDOT service for it to take effect.

---

### 7. Restart the collector

```powershell
Restart-Service -Name "nrdot-collector"
Get-Service -Name "nrdot-collector"
```
