#!/usr/bin/env python3
"""mail-api.py — read Proton mail API with the live scoped session (33clr)."""
import sqlite3, json, re, urllib.request, urllib.error, os, shutil, tempfile

CLONE = r'C:\Users\morpher\Downloads\a\session\loot\C12\Firefox\profile-replay'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/157.0'
UID = None
pair = {}

base = os.path.join(tempfile.gettempdir(), 'clone_cookies2.sqlite')
shutil.copy(os.path.join(CLONE, 'cookies.sqlite'), base)
c = sqlite3.connect(base)
for host, name, value in c.execute(
        'SELECT host, name, value FROM moz_cookies WHERE name LIKE ?', ('%-33clr%',)):
    pair[name] = value
    if name.startswith('AUTH-'):
        UID = name[5:]
print('UID:', UID, '| cookies:', list(pair))

# fetch mail web app version
appv = 'web-mail@5.0.135.9'
try:
    html = urllib.request.urlopen(urllib.request.Request(
        'https://mail.proton.me/', headers={'User-Agent': UA}), timeout=30).read().decode('utf-8', 'replace')
    srcs = re.findall(r'src="([^"]+\.js[^"]*)"', html)
    for s in srcs[:3]:
        url = 'https://mail.proton.me' + s if s.startswith('/') else s
        try:
            js = urllib.request.urlopen(urllib.request.Request(
                url, headers={'User-Agent': UA}), timeout=30).read().decode('utf-8', 'replace')
        except Exception:
            continue
        cands = re.findall(r'APP_VERSION[=\'"\s:]+([0-9]+\.[0-9.]+)', js)
        if cands:
            appv = 'web-mail@' + sorted(set(cands))[-1]
            break
except Exception as e:
    print('version fetch fail:', e)
print('appversion:', appv)

hdr = '; '.join('%s=%s' % (k, v) for k, v in pair.items())
url = 'https://mail.proton.me/api/mail/v4/messages?Page=0&PageSize=10&Sort=Time&Desc=1&LabelID=0'
req = urllib.request.Request(url)
req.add_header('Cookie', hdr)
req.add_header('x-pm-uid', UID)
req.add_header('x-pm-appversion', appv)
req.add_header('Accept', 'application/json')
req.add_header('User-Agent', UA)
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.loads(r.read().decode('utf-8', 'replace'))
        print('HTTP', r.status, '| total:', j.get('Total'))
        for m in (j.get('Messages') or [])[:10]:
            print('---')
            print('  ID:', m.get('ID'))
            print('  From:', (m.get('Sender') or {}).get('Address'),
                  '<%s>' % (m.get('Sender') or {}).get('Name'))
            print('  Time:', m.get('Time'), 'Size:', m.get('Size'),
                  'Unread:', m.get('Unread'), 'NumMessages:', m.get('NumMessages'))
            subj = m.get('Subject') or ''
            print('  Subject(%d): %s' % (len(subj), subj[:80]))
except urllib.error.HTTPError as e:
    print('HTTP', e.code, e.read().decode('utf-8', 'replace')[:300])