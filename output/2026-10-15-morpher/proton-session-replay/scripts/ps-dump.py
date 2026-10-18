#!/usr/bin/env python3
"""ps-dump.py — full dump of persisted-session (ps-*) localStorage entries."""
import sqlite3, shutil, os, tempfile, sys, json

if len(sys.argv) > 1:
    srcs = [(os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(sys.argv[1])))), sys.argv[1])]
else:
    srcs = [
        ('mail', r'C:\Users\morpher\Downloads\a\session\loot\C12\Firefox\profile-replay\storage\default\https+++mail.proton.me\ls\data.sqlite'),
        ('account', r'C:\Users\morpher\Downloads\a\session\loot\C12\Firefox\profile-replay\storage\default\https+++account.proton.me\ls\data.sqlite'),
    ]
for tag, src in srcs:
    print('=== %s ===' % tag)
    if not os.path.exists(src):
        print('  (no ls db)')
        continue
    t = os.path.join(tempfile.gettempdir(), 'ps-%s.sqlite' % tag)
    shutil.copy(src, t)
    for e in ('-wal', '-shm'):
        if os.path.exists(src + e):
            shutil.copy(src + e, t + e)
        elif os.path.exists(t + e):
            os.remove(t + e)
    c = sqlite3.connect(t)
    for key, val in c.execute("SELECT key, value FROM data WHERE key LIKE 'ps-%'"):
        print('key:', key[:60], 'len', len(val or b''))
        try:
            obj = json.loads(val.decode('utf-8'))
            print(json.dumps(obj, indent=1, ensure_ascii=False)[:1600])
        except Exception as e:
            print('  raw decode err:', e)
            print(repr(val[:400]))
