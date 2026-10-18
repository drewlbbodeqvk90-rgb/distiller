# DPAPI blob anatomy (byte-exact, verified 756/756)

Source: `scripts/parse-dpapi-blob.py` (byte-identical in `scripts/`), runbook
AGENTS.md §3–4, findings C25, HANDOFF.md §3.5. Layout verified byte-exact
against a real CRED file (756 B parsed of 756 B) and cross-checked with the
ground-truth trick below.

## Blob field map (impacket DPAPI_BLOB layout, little-endian)

```
Version            u32            (observed 1)
GuidCredential     16 B           (credential GUID)
MasterKeyVersion   u32
GuidMasterKey      16 B           → format as 8-4-4-2-2-2-2-2-2 GUID
Flags              u32            (observed 0x20000000 on CRED blobs)
DescriptionLen     u32
Description        UTF-16LE, DescriptionLen bytes
CryptAlgo          u32            (0x6610 = AES-256)
CryptAlgoLen       u32            (bits, e.g. 256)
SaltLen            u32 ; Salt     (SaltLen bytes)
HMacKeyLen         u32 ; HMacKey  (HMacKeyLen bytes)
HashAlgo           u32            (0x800e = SHA-256)
HashAlgoLen        u32            (bits)
HMacLen            u32 ; HMac     (HMacLen bytes)
DataLen            u32 ; Data     (DataLen bytes — the AES-GCM payload)
SignLen            u32 ; Sign     (SignLen bytes)
```
The parser prints running offsets and ends with
`parsed N / len bytes  OK-EXACT | MISMATCH remain=k` — demand OK-EXACT before
drawing conclusions.

## CRED file wrapper (proven)

`%LOCALAPPDATA%\Microsoft\Credentials\<hex>` = 12-byte prefix
`01 00 00 00 | (size-4) u32 | 00 00 00 00 | 01 00 00 00` + DPAPI blob at
offset 0x0C. Session CRED targets (masked names): `JianyingPro Cached
Credential`, `WindowsLive:target=virtualapp/didlogical` user `02ixq…` (22-char
id).

## Ground-truth trick (proven calibration method)

From PowerShell: `[Security.Cryptography.ProtectedData]::Protect(text, $null,
'CurrentUser')` on a KNOWN string, dump hex, parse it with the same field map,
compare field-by-field. This is how the layout above was validated without any
external tool.

## Live Unprotect anomaly (proven dead-end)

- `.NET ProtectedData.Unprotect` REJECTS the structurally-valid CRED blob at
  offset 0x0C with "data is invalid" although: parse is byte-exact, the
  referenced masterkey (`885322fe-92ff-42be-ba35-42fe361dd64b`, active, CREDHIST
  present) is available, and a freshly created roundtrip blob with the SAME
  masterkey decrypts fine. Suspected cause: Flags=0x20000000 / CREDHIST chain
  handling — unresolved.
- P/Invoke `CryptUnprotectData` MUST declare exactly 6 parameters
  (pIn, pEntropy, pReserved, pPrompt, dwFlags, pOut); a 7-param declaration
  silently misbinds and yields uniform error 998/13 at every offset.
- Offline route for CRED blobs: mimikatz `dpapi::cred`
  [UNVERIFIED — not run in-session]. Do not fetch mimikatz onto the target:
  Defender toasts AND kills the spawned process (proven behavior for caught
  files).

## Related v20 fact

Chromium app-bound v20 uses the same DPAPI machinery (`APPB` blob in Local
State), but its masterkey GUID `27b26861-…` is absent from `Protect\<SID>` in
the user hive — see `chromium-os-crypt-formats.md`.
