# FS-triage scoring model + v1→v2 calibration doctrine

Source: `scripts/fs-triage.py` (byte-identical in `scripts/`), proposals.md §3,
findings FS-01/02/03, HANDOFF.md §3.3.

## Scoring model (as implemented and tested)

- **Directory score** = keyword score over the lowercased full path
  (`kw_score`) + media-density bonus (`+2` when the dir holds ≥1 media file and
  >50 MB of media). Only dirs with a nonzero keyword score are ranked.
- **File score** = keyword score of the filename + extension score
  (`EXT_SCORE`); files scoring ≥4 enter `file-hits`. In v2, files with a
  noise extension score 0 regardless of name matches.
- **Buckets per dir**: file count, total size, media count/bytes (`MEDIA_EXT`:
  mp4/mov/avi/mkv/wmv/m4v/webm/3gp/jpg/jpeg/png/heic/heif/gif/webp/bmp),
  doc count (`DOC_EXT`: pdf/doc/docx/txt/md/rtf/xlsx/csv), archive count
  (`ARCH_EXT`: 7z/zip/rar/tar/gz).
- **Keyword lexicon** (weights 1–7), groups: privacy (private 6, personal 5,
  nsfw 7, nude 7, onlyfans 7, intim 6, erotic 6, xxx 6, sex 5, adult 4,
  girlfriend 4, wife 3, family 2, cam 3), crypto (wallet 6, seed 6, mnemonic 6,
  metamask 5, keystore 5, trezor 5, ledger 4, phrase 4, crypto 3, exchange 2),
  secrets (password 6, creds 6, credential 6, keys 4, ssh 3, pgp 4, gnupg 4,
  2fa 6, totp 5, otp 3), identity/docs (kyc 6, passport 6, id_card 5,
  identity 4, bank 4, tax 3, salary 4, scan 3, documents 3), backup (backup 3,
  recovery 4, restore 2, old 1), comms (whatsapp 3, telegram 3, signal 2,
  discord 2, chat 2), media (video/videos 4, photo/photos 3, movie 2,
  iphone/samsung/android 2), misc (important 4, do_not_delete 4, new 1).
- **Extension scores**: .kdbx 7, .wallet 6, .kbvault 6, .1pux 6, .p12/.pfx 5,
  .ovpn 5, .key/.pem 4, .rdp 4, .csc 3, .vcf 3, .kape 3, .7z/.rar 2, .zip 1,
  .json 0.
- **Walk**: `os.walk` topdown, prune `PRUNE` names + names starting with `$`,
  wall-clock budget 150 s, roots = user profile + `C:\Users\Public`.

## v1 → v2 calibration (all six rules proven)

1. **Prune toolchains/app-internals by NAME** — v2 extends PRUNE with
   TOOLCHAIN/tools/mingw64*/cmake-*/fixtures/test/tests/lib/include/share/
   plugins/Qt5Compat/GraphicalEffects/InPrivate/playready. Rationale: `private`
   in a Qt cache is noise; `private` in `Dropbox\` is gold.
2. **Noise-extension blacklist** — v2 zeroes scores for
   .rst .html .h .hpp .py .js .css .mo .pot .po .cmake .cpp .c .lua .dll .exe
   (docs/code of installed software otherwise flood the ranking; proven
   pathology: `FIND_XXX.rst` matching the keyword 'xxx').
3. **Self-referential tagging** — the agent's own prior audit output
   (`windows-creds-extractor\results`) scored top in v1; treat own tool output
   dirs as noise AND as an integrity check that the walk reached them.
4. **Media-density bonus > keyword score** for the video-class finding — the
   +2 bonus is what surfaced the CapCut cluster.
5. **Score relative to user-space roots**; report AppData hits separately
   (AppData internals would otherwise outrank user dirs).
6. **Runtime is trivial** — v1: 15 s / ~95 k files / 724 hits (noisy);
   v2: 4 s / ~31 k files / 363 hits. Schedule in the wide-first sweep.

## Proven true-positive (the skill's benchmark)

4 × ~209 MB `0926*.mp4` dated 2026-09-27 — 3 in `AppData\Local\CapCut\Videos`
+ 1 copy in the Downloads root — while shell Pictures/ AND Videos/ were EMPTY.
A standard media-folder audit would have reported none. Also re-confirmed via
lexicon: `private.pem` (RSA key); flagged a `Secrets.kdbx` (test fixture);
established no Dropbox and OneDrive-with-0-personal-files.

## Limits / ethics (proven doctrine)

- Names only — NO content reads (optional EXIF/EXT-header spot-checks on flagged
  media are a follow-up, not part of this pass by default).
- Operator consent for scope; results are indicators, not proof — a `private`
  dir may be empty, an innocuous dir may hold the secret.
- Open follow-ups (unproven): EXIF camera/fingerprint correlation,
  EXIF-stripping detection, duplicate detection across devices, cloud-sync
  config review (which folders ARE synced where).

## Output formats

- `dir-hits[-v2].txt`: `score  path(files=… MB media=N(…MB) docs=… arch=…) [keywords]`, top 250.
- `file-hits[-v2].txt`: `score  size  mtime  path  [keywords(+ext:…)]`, top 3000.
- Console: walk stats + top-20 dir preview.
