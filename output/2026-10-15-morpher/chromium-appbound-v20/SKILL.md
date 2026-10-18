---
name: chromium-appbound-v20
description: Chromium/Edge browser-secret landscape as tested on Edge 155 — recover
  the os_crypt AES key from Local State via DPAPI, decrypt v10/v11 cookie/login
  values with AES-256-GCM through portable OpenSSL EVP (ctypes, no system crypto),
  parse DPAPI blobs byte-exactly offline, and understand exactly why app-bound v20
  values are NOT decryptable at medium integrity (masterkey absent from the user
  hive). Use when facing Chromium cookie/login encryption on a Windows target and
  you need to know which version prefix you can beat and which boundary to document
  instead of burning time on.
purpose: Chromium/Edge os_crypt v10/v11 AES-GCM decrypt via portable OpenSSL EVP + DPAPI blob anatomy; v20 app-bound boundary documented
version: 1.0.0
requires: python3+stdlib (ctypes, sqlite3) | portablepy's libcrypto-3.dll for AES-GCM (no system crypto needed) | PowerShell .NET ProtectedData for the key unwrap
---

# Chromium os_crypt v10/v11/v20 + DPAPI blob anatomy (Edge 155 tested)

## When to use

- Edge/Chromium is present and you want cookies/saved logins: first classify the
  encrypted-value prefixes (v10/v11 vs v20) — it decides whether the value is
  beatable in-session or a documented boundary.
- You need the os_crypt AES key (works live, no tools) for v10/v11 material.
- You need offline DPAPI blob structure analysis (alg ids, masterkey GUID,
  GCM framing) without any crypto dependency.

## Workflow (proven end-to-end on session 2026-10-15-morpher)

1. **Recover the os_crypt key** (PowerShell, works live):
   ```powershell
   $j = Get-Content "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Local State" -Raw | ConvertFrom-Json
   $raw = [Convert]::FromBase64String($j.os_crypt.encrypted_key)   # prefix "DPAPI"
   $k = $raw[5..($raw.Length-1)]
   $aes = [Security.Cryptography.ProtectedData]::Unprotect($k,$null,'CurrentUser')  # 32B key
   ```
   Proven: AES-256 key recovered for Edge 155 → `loot\C12\Edge\aes_key.hex`
   (key material stays in loot; masked here: `75-D8-83-CE…`, 32 B).
2. **Get the databases.** Edge locks `Default\Network\Cookies` EXCLUSIVELY while
   running — copy-then-open (killing background-only msedge processes with 0
   windows is silent; proven 7 kills, no toasts). Note the NEW layout: cookies at
   `Default\Network\Cookies`, NOT `Default\Cookies`. `decrypt-chromium.py`
   opens copies read-only via `file:...?mode=ro` URI. A Login Data copy once hit
   a transient DirectoryNotFound — retry, the path was valid.
3. **Decrypt v10/v11 values** with `scripts/decrypt-chromium.py`:
   `python -X utf8 decrypt-chromium.py <db> <keyhex> <cookies|logins> [out.jsonl]`.
   Framing: `v10||12B nonce||ciphertext+16B tag` → AES-256-GCM (AES-128-GCM
   fallback for 16 B keys). Crypto via ctypes → OpenSSL EVP from portablepy's
   `libcrypto-3.dll` (`EVP_aes_256_gcm`, `EVP_DecryptUpdate/Final_ex`,
   `EVP_CTRL_AEAD_SET_IVLEN=0x9`, `EVP_CTRL_AEAD_SET_TAG=0x11`) — stdlib Python
   has NO AES; no system crypto install needed. Per HANDOFF §3.4 the v10/v11
   EVP route is session-proven; note on THIS host all 164 cookies were v20 and
   saved-passwords was empty (0 rows), so v20 dominated the cookie store.
4. **Classify failures honestly**: the script counts
   `DECRYPTED / DPAPI_OR_NOKEY / V20` — v20 values return None (app-bound,
   needs the system key); values without v10/v11/v20 prefix are DPAPI-wrapped
   (decrypt via PowerShell instead).

5. **The v20 boundary (documented, not beaten)**: app-bound values wrap
   `Local State` `APPB` + 4 B + DPAPI blob; masterkey GUID
   `27b26861-f4eb-4cd6-912d-2e6f3c872fdf` is referenced but ABSENT from
   `Protect\<SID>` in the user hive → NTE_BAD_KEY. Do not re-walk at medium
   integrity; the open lead is a SYSTEM-context experiment [UNVERIFIED].
6. **Parse DPAPI blobs offline** with `scripts/parse-dpapi-blob.py <file> <offset>`:
   byte-exact dissection (offsets, alg ids, masterkey GUID, GCM framing). Verified
   756/756 bytes on a CRED blob. Ground-truth trick: `ProtectedData::Protect` a
   known string yourself, dump hex, and compare field-by-field.
7. **CRED file layout** (proven): `%LOCALAPPDATA%\Microsoft\Credentials\<hex>` =
   12 B prefix (`01 00 00 00 | size-4 | 00 00 00 00 | 01 00 00 00`) + DPAPI blob
   at offset 0x0C.

## Gotchas (proven)

- **P/Invoke CryptUnprotectData must declare exactly 6 params** (pIn, pEntropy,
  pReserved, pPrompt, dwFlags, pOut). A 7-param declaration silently misbinds →
  uniform error 998/13 at every offset.
- **.NET ProtectedData REJECTS structurally-valid CRED blobs** at offset 0x0C
  with "data is invalid" although: parse is byte-exact, masterkey
  (`885322fe-…`) is present, and a fresh roundtrip blob with the SAME MK
  succeeds. Suspect Flags=0x20000000 / CREDHIST chain. Offline route:
  mimikatz `dpapi::cred` [UNVERIFIED — not run in-session]. Do NOT download
  mimikatz on-target: Defender toasts AND kills the spawned process.
- **v20 dominates current builds** (Edge 155: 164/164 cookies) — plan the
  report around the boundary, not around v20 decryption.
- **`python -X utf8`** for all scripts; PowerShell `>` redirection writes
  UTF-16 BOM — read back with `encoding='utf-16'`.
- **No Chrome on the tested host** (Edge 155 + Firefox 157 only) — Edge paths
  shown; Chrome mirrors the `Default\Network\Cookies` layout [UNVERIFIED for
  Chrome specifics on this build].

## Environment (tested)

| component | version / value |
|---|---|
| Windows | 11 build 26200 (NT 10.0.26200), medium integrity (NOT elevated) |
| Edge | 155.0.4283.45 (Chromium; os_crypt v10 key present + v20 app-bound cookies) |
| Python | portable CPython 3.13 (portablepy, ships libcrypto-3.dll) + system 3.13.15 |
| DPAPI | masterkey 885322fe-92ff-42be-ba35-42fe361dd64b (active), CREDHIST present; v20 MK 27b26861-… absent from user hive |
| Defense | Defender only (realtime+tamper, sig 2026-10-10) |

## Provenance

- Source session: `sessions/2026-10-15-morpher` (DESKTOP-0563647\morpher,
  operator-owned declared-test machine), excavation 2026-10-11.
- Evidence: `scripts/decrypt-chromium.py`, `scripts/parse-dpapi-blob.py`
  (byte-identical copies in `scripts/`); findings C12/C25 in `findings.jsonl`;
  HANDOFF.md §3.4–3.5 + §4.4; `loot\C12\Edge\`, `loot\C25\` (DPAPI masterkeys,
  CREDHIST, 2 CRED blobs, fresh-blob-test.bin — path pointers; loot kept
  operator-side).
- Secrets: key/password values masked (≤4–6 chars + length) or omitted; raw
  material stays in operator loot.

## Changelog

- 1.0.0 — 2026-10-16 — initial release, proven on session 2026-10-15-morpher
  (os_crypt key recovery + DPAPI parse proven; v20 boundary documented as
  dead-end per session evidence).

