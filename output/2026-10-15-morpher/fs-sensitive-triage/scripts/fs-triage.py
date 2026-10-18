#!/usr/bin/env python3
"""fs-triage.py — sensitive-content discovery by PATH/FILENAME heuristics. No content reads.
Phase A: pruned full-tree walk of user profile; rank DIRECTORIES by sensitive-name score.
Phase B: for hit dirs, inventory files (type buckets, sizes); global ranked file list.
Theory: people organize sensitive material into named folders (private/personal/backup/
wallet...). Path lexicon matching finds these without opening a single file."""
import os, time, re, sys

OUT = r'C:\Users\morpher\Downloads\a\session\loot\fs-triage'
os.makedirs(OUT, exist_ok=True)
ROOTS = [r'C:\Users\morpher', r'C:\Users\Public']
BUDGET_S = 150
t0 = time.time()
V2 = len(sys.argv) > 1 and sys.argv[1] == 'v2'

PRUNE = {'node_modules', '.git', '.svn', '__pycache__', 'cache', 'Cache', 'Code Cache',
         'GPUCache', 'cache2', 'startupCache', 'shader-cache', 'Crashes', 'Crashpad',
         'Crash Reports', 'Temp', 'temp', '$Recycle.Bin', 'WindowsApps', 'WER',
         'Minidump', 'D3DSCache', 'Packages', '.vscode', '.cargo', 'target', 'dist',
         'build', '.gradle', '.m2', 'venv', '.venv', 'site-packages', '__MACOSX',
         'Calibration', 'ServiceProfiles', 'Comms', 'Widgets', 'PlayFab'}
if V2:
    PRUNE |= {'TOOLCHAIN', 'tools', 'mingw64', 'mingw64-full', 'mingw64-reextract',
              'mingw64-temp', 'cmake-3.31.0-windows-x86_64', 'fixtures', 'test',
              'tests', 'test-tools', 'lib', 'include', 'share', 'plugins', 'Qt5Compat',
              'GraphicalEffects', 'InPrivate', 'playready', 'PlayReady'}
NOISE_EXT = {'.rst', '.html', '.h', '.hpp', '.py', '.js', '.css', '.mo', '.pot', '.po',
             '.cmake', '.cpp', '.c', '.lua', '.dll', '.exe'} if V2 else set()

KW = {
    'private': 6, 'personal': 5, 'privat': 6, 'secret': 5, 'nsfw': 7, 'nude': 7,
    'adult': 4, 'sex': 5, 'xxx': 6, 'intim': 6, 'erotic': 6, 'cam': 3, '18+': 5,
    'onlyfans': 7, 'nudes': 7, 'my_video': 5, 'family': 2, 'girlfriend': 4, 'wife': 3,
    'wallet': 6, 'seed': 6, 'mnemonic': 6, 'metamask': 5, 'keystore': 5, 'ledger': 4,
    'trezor': 5, 'phrase': 4, 'crypto': 3, 'exchange': 2,
    'password': 6, 'passwd': 6, 'pwd': 4, 'creds': 6, 'credential': 6, 'keys': 4,
    'ssh': 3, 'pgp': 4, 'gnupg': 4, '2fa': 6, 'totp': 5, 'auth': 2, 'otp': 3,
    'backup': 3, 'recovery': 4, 'restore': 2, 'old': 1,
    'kyc': 6, 'passport': 6, 'id_card': 5, 'identity': 4, 'documents': 3, 'docs': 1,
    'bank': 4, 'banking': 4, 'invoice': 2, 'tax': 3, 'salary': 4, 'contract': 2,
    'scan': 3, 'scans': 3, 'pdf': 1,
    'chat': 2, 'whatsapp': 3, 'telegram': 3, 'signal': 2, 'discord': 2,
    'photo': 3, 'photos': 3, 'foto': 3, 'video': 4, 'videos': 4, 'movie': 2, 'rec': 1,
    'phone': 2, 'mobile': 1, 'samsung': 2, 'android': 2, 'iphone': 2,
    'Important': 4, 'important': 4, 'do_not_delete': 4, 'new': 1, 'fin': 2,
}
EXT_SCORE = {'.kdbx': 7, '.key': 4, '.pem': 4, '.p12': 5, '.pfx': 5, '.ovpn': 5,
             '.rdp': 4, '.wallet': 6, '.csc': 3, '.kbvault': 6, '.1pux': 6, '.json': 0,
             '.7z': 2, '.zip': 1, '.rar': 2, '.vcf': 3, '.kape': 3}
MEDIA_EXT = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.m4v', '.webm', '.3gp',
             '.jpg', '.jpeg', '.png', '.heic', '.heif', '.gif', '.webp', '.bmp'}
DOC_EXT = {'.pdf', '.doc', '.docx', '.txt', '.md', '.rtf', '.xlsx', '.csv'}
ARCH_EXT = {'.7z', '.zip', '.rar', '.tar', '.gz'}

dirs = []          # (path, nfiles, totsize, nmedia, mediasize, ndoc, narch)
file_hits = []     # (score, path, size, mtime, reason)
nfiles_total = 0
noskip = 0

def kw_score(name_lower):
    s = 0
    hits = []
    for kw, w in KW.items():
        if kw in name_lower:
            s += w
            hits.append(kw)
    return s, hits

for ROOT in ROOTS:
    for dirpath, dirnames, filenames in os.walk(ROOT, topdown=True, followlinks=False):
        if time.time() - t0 > BUDGET_S:
            break
        dirnames[:] = [d for d in dirnames if d not in PRUNE and not d.startswith('$')]
        nfiles = totsize = nmedia = mediasize = ndoc = narch = 0
        dlow = dirpath.lower()
        for fn in filenames:
            nfiles_total += 1
            try:
                st = os.stat(os.path.join(dirpath, fn))
            except OSError:
                noskip += 1
                continue
            sz = st.st_size
            totsize += sz
            ext = os.path.splitext(fn)[1].lower()
            fl = fn.lower()
            if ext in MEDIA_EXT:
                nmedia += 1
                mediasize += sz
            elif ext in DOC_EXT:
                ndoc += 1
            elif ext in ARCH_EXT:
                narch += 1
            fs, fh = kw_score(fl)
            es = EXT_SCORE.get(ext, 0)
            if ext in NOISE_EXT:
                es = 0
            if fs + es >= 4:
                file_hits.append((fs + es, os.path.join(dirpath, fn), sz,
                                  time.strftime('%Y-%m-%d', time.localtime(st.st_mtime)),
                                  ','.join(fh) + (('+ext:' + ext) if es else '')))
        if dirpath != ROOT:
            dirs.append((dirpath, nfiles, totsize, nmedia, mediasize, ndoc, narch, dlow))

# rank dirs: name score + media-density bonus
ranked = []
for d in dirs:
    path, nf, ts_, nm, ms, nd, na, dlow = d
    s, hits = kw_score(dlow)
    if s:
        media_bonus = 2 if (nm > 0 and ms > 50 * 1024 * 1024) else 0
        ranked.append((s + media_bonus, path, nf, ts_, nm, ms, nd, na, ','.join(hits)))
ranked.sort(key=lambda r: -r[0])

SUF = '-v2' if V2 else ''
with open(os.path.join(OUT, 'dir-hits%s.txt' % SUF), 'w', encoding='utf-8') as f:
    for r in ranked[:250]:
        f.write('%3d  %-110s files=%-6d %.1fMB media=%d(%.0fMB) docs=%d arch=%d  [%s]\n' %
                (r[0], r[1][:110], r[2], r[3] / 1048576, r[4], r[5] / 1048576, r[6], r[7], r[8]))

file_hits.sort(key=lambda x: -x[0])
with open(os.path.join(OUT, 'file-hits%s.txt' % SUF), 'w', encoding='utf-8') as f:
    for x in file_hits[:3000]:
        f.write('%3d  %10d  %s  %s  [%s]\n' % (x[0], x[2], x[3], x[1], x[4]))

print('walked %d dirs, %d files in %.0fs (stat-fail %d)' % (len(dirs), nfiles_total, time.time() - t0, noskip))
print('dir hits (score>=6): %d | file hits: %d' % (sum(1 for r in ranked if r[0] >= 6), len(file_hits)))
for r in ranked[:20]:
    print('%3d %-95s media=%d(%.0fMB) [%s]' % (r[0], r[1][:95], r[4], r[5] / 1048576, r[8]))