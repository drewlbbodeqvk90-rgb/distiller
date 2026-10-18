# Proton web session model (v5) — proven facts and framing

Source: findings C10-06 … C10-24, `scripts/ps-dump.py` + `keypassword-try.py`
outputs, Proton WebClients source study (persistedSessionStorage.ts,
sessionBlobCryptoHelper.ts, offlineKey.ts, api/auth.ts — cited in C10-07),
HANDOFF.md §3.2. All below proven in-session unless tagged otherwise.

## Session topology

- **account.proton.me session**: web app for login; writes `AUTH-<uid>` /
  `REFRESH-<uid>` cookies (uid = 32-char lowercase alnum, e.g. `llk2…`).
- **mail session**: forked via SSO; MEMORY-ONLY — the forked mail session never
  writes any cookie; its access token lives in the tab's JS heap.
- **Login flow**: transient login-flow AUTH cookie lives 3–8 s in the cookies DB,
  then the browser deletes it after the SSO redirect (C10-12; observed across 5
  login cycles 17:27–17:59).
- **Persistence** = localStorage `ps-1` blob only (per-host, in
  `storage\default\https+++<host>\ls\data.sqlite`, table `data`, keys `ps-*`).
  `default-persistent=false` (user did not tick keep-me-signed-in) means nothing
  usable persists.

## Token/scope lifecycle (proven)

- Cookie deletion ≠ token death: a captured login-session token REMAINED VALID
  server-side after the cookie was deleted — `GET core/v4/auth/scopes` → 200
  (C10-13). Validity = server-side session lifetime; a live token was re-dumped
  hourly-scale for 12 h (C10-20).
- Scope mask example (C10-13): mask `6043026126208` decoded to
  [loggedin, nondelinquent, vpn, drive, docs, pass, verified, lumo, meet] —
  pre-2FA locked-equivalent; NOT mail/self/user; not escalatable without TOTP.
- 2FA completion does NOT rewrite the AUTH cookie (C10-14) — the full-scope
  token exists only inside the running browser. The captured REFRESH token was
  already consumed → 400 Invalid refresh token.
- Proven capture recipe: watcher polls live `cookies.sqlite` (~3 s) and
  snapshots on any new/changed proton cookie; on a login event, a dedicated
  prober polls `GET /api/core/v4/users` with the captured cookie (~0.25 s
  cadence) until 200 = full scope, then fires the mail read (C10-16/17).

## API surface proven

| endpoint | use | result |
|---|---|---|
| `mail-api.proton.me/api/mail/v4/messages?Page=0&PageSize=N` | mailbox LIST with full-scope token, DIRECT | 200, Total=24/25 |
| `mail-api.proton.me/api/mail/v4/conversations` | conversation list | 200 |
| `account.proton.me/api/core/v4/users` | scope probe (200 = full scope) | 200 when full |
| `account.proton.me/api/core/v4/auth/scopes` | scope mask read | 200 + mask |
| `account.proton.me/api/core/v4/auth/v4/sessions/forks` | fork push | 422 Invalid selector (dead end) |
| `*/api/auth/v4/sessions/local/key` | ClientKey fetch | 200 own-auth / 401 cross-UID |
| `api/core/v4/auth/cookies` (POST) | refresh-cookie replay | 401 consumed/revoked |

Headers that worked (all requests): `Cookie: AUTH-<uid>=<val>`,
`x-pm-uid: <uid>`, `x-pm-appversion: web-mail@5.0.135.9` (or
`web-account@5.0.426.0`), `Accept: application/json`,
`User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/157.0`.
`Web_x`-style appversion → error 5002 (proven).

## ps-blob crypto (proven structure, unproven unlocks)

- mail `ps-1`: payloadType=`default` → blob contains `{keyPassword}` encrypted
  AES-GCM with key=ClientKey (16 B key, 16 B IV prefix framing attempted in
  `keypassword-try.py`; ClientKey is server-side per session — needs the
  session's OWN live auth, so offline mail-blob unlock is a dead end).
- account `ps-*`: payloadType=`offline` → Argon2id(password, offlineKeySalt),
  ARGON2_PARAMS.RECOMMENDED = {passes:1, parallelism:4, memoryExponent:19,
  tagLength:32}. 14-candidate run (pw-try.py) → no match; password unknown.
- Chain if password were known: account password → keyPassword (ps blob) →
  address private keys → PGP body decryption. Bodies themselves are
  `-----BEGIN PGP MESSAGE-----` (ProtonMail).
- Open lead: memory-scan the login moment — the password transits memory at
  login (HANDOFF §8).

## Watcher pattern (v5 telemetry, REFERENCE)

`watch-proton.py` (session drop, REFERENCE verdict): poll live cookies.sqlite
every 3 s within a time window (6 h proven), instant dual-probe snapshot
(`/users` + mail-api) on any new/changed proton cookie. Gotcha fixed in-session:
a stale `-shm` copy raises errno 22 and killed the auto-replay — copy DB + WAL,
drop stale `-shm`.
