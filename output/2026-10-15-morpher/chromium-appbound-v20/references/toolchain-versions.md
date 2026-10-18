# toolchain-versions — chromium-appbound-v20 1.0.0

## Environment matrix (tested on the source session)

| component | version / value |
|---|---|
| OS | Windows 11 build 26200 (NT 10.0.26200), medium integrity (NOT elevated) |
| Edge | 155.0.4283.45 (Chromium; os_crypt v10 key present, 164/164 cookies v20 app-bound, 0 saved passwords) |
| Python | portable CPython 3.13 (portablepy — ships libcrypto-3.dll beside python.exe) + system 3.13.15 |
| Crypto | OpenSSL 3.x via libcrypto-3.dll EVP (ctypes); .NET ProtectedData via PowerShell for DPAPI steps |
| DPAPI | masterkey 885322fe-92ff-42be-ba35-42fe361dd64b active (CREDHIST present); v20 MK 27b26861-f4eb-4cd6-912d-2e6f3c872fdf ABSENT from Protect\<SID> |
| Defense | Defender only (realtime+tamper, sig 2026-10-10) |

Version boundaries that matter: Edge 155 is the tested os_crypt behavior
(v20-dominated store); Chromium renames/relayouts (cookies at
`Default\Network\Cookies`) are build-sensitive — re-fingerprint before reuse
per the shared rule "app versions are crypto boundaries".

## Script manifest (sha256, bytes = size)

| script | sha256 | bytes | session-tested context |
|---|---|---|---|
| scripts/decrypt-chromium.py | cc8334dd788d945795e94c65437530cc145637ef5ce81b2fff55ef48dcb67fcf | 5896 | EVP AES-GCM v10/v11 decryptor with v20/DPAPI classifier (ro-sqlite URI) |
| scripts/parse-dpapi-blob.py | 5d026098ca27d2036e21f95c0d7e01282c8c827dc1fbdbe61f6759d21fa77eb6 | 2640 | byte-exact DPAPI blob dissection — verified 756/756 on a CRED blob |

Copies are byte-identical to `sessions/2026-10-15-morpher/scripts/` (sha256
verified at distillation time, 2026-10-16). `py_compile` clean on both.

Script notes:

- `decrypt-chromium.py` resolves `libcrypto-3.dll` at
  `<parent-of-script>\helpers\portablepy\libcrypto-3.dll`, falling back to
  PATH — keep that relative layout or drop the DLL beside the script.
- `parse-dpapi-blob.py` takes `<file> <offset>` (CRED blobs: offset 0x0C) and
  self-reports `OK-EXACT` vs `MISMATCH remain=k` — trust only OK-EXACT.

## Reference (not carved) from the same session

`probe-dpapi-offsets.ps1`, `impacket-dpapi.py` (reference copy) and
`brute-key4.py` remain in the session drop as workbench history; the DPAPI
field map they validated is captured in `references/dpapi-blob-anatomy.md`.

## Update policy

Re-hash and bump this manifest on every release: MINOR for a new
technique/script, PATCH for wording/matrix refresh (excavator VERSIONING
policy).
