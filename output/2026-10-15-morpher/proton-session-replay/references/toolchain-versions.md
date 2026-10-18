# toolchain-versions — proton-session-replay 1.0.0

## Environment matrix (tested on the source session)

| component | version / value |
|---|---|
| OS | Windows 11 build 26200 (NT 10.0.26200), medium integrity (NOT elevated) |
| Browser | Firefox 157.0.1, profile 3xzkegqp.default-release |
| Proton web clients | v5; appversion format `web-mail@5.0.135.9` / `web-account@5.0.426.0` (live-scraped from JS bundles) |
| Python | portable CPython 3.13 (portablepy) — stdlib (urllib, sqlite3, json, ssl) for the API path |
| pip-installed (pylibs) | argon2-cffi 25.1.0, argon2_cffi_bindings 26.1.0, cffi 2.1.1, cryptography 50.0.2, PGPy 0.6.0 (+pyasn1 0.6.4, pycparser 3.11) — used only by the offline ps-blob attempt path |
| API endpoints | mail-api.proton.me / account.proton.me (v4) |

## Script manifest (sha256, bytes = size)

| script | sha256 | bytes | session-tested context |
|---|---|---|---|
| scripts/mail-api.py | 3efd0c3b691a96aa725a9a460be2b3d5d3c34b10cb0bf6ebfe9a08f0c619cf0b | 2758 | live appversion scrape + direct mail API read against captured session |
| scripts/mail-dump.py | f4e5ebc5170007c12dc0fbd6f3f2e14b62f868d633c083404bd80fad5d6e4236 | 1777 | mailbox.txt writer — proven 200 / Total=24–25 messages |
| scripts/ps-dump.py | 39f4af9523c6513fab1fdbf2f355f8c2ddc05cf2a6a84d9b6ae03023a6d704e4 | 1408 | ps-* localStorage blob extraction (proven dump; decryption = dead-end 3) |
| scripts/keypassword-try.py | d79df1eabb51846c2333c3e7336dbc44a8ae078fe27c3932ad58bb82650c7240 | 3948 | getLocalKey header-variant matrix + ps-blob AES-GCM framing attempt (dead-end 2 evidence) |

Copies are byte-identical to `sessions/2026-10-15-morpher/scripts/` (sha256
verified at distillation time, 2026-10-16). `py_compile` clean on all four.

Script notes:

- `mail-api.py` hardcodes a session-specific clone path and a UID-suffix
  cookie filter (`%-33clr`) — edit both per run (UID fragments are not secrets).
- `mail-dump.py` is the minimal credential-in, mailbox-out tool; prefer it for
  reuse. `mail-api.py` doubles as the appversion-discovery reference.
- `keypassword-try.py` also installs `cryptography`'s AESGCM usage for the
  blob framing (key16 = ClientKey[:16], iv = data[:16], tag appended) — the
  framing attempt is session-recorded; the full unlock is a dead end (see
  SKILL.md Dead-ends 2–3).

## Update policy

Re-hash and bump this manifest on every release: MINOR for a new
technique/script, PATCH for wording/matrix refresh (excavator VERSIONING
policy).
