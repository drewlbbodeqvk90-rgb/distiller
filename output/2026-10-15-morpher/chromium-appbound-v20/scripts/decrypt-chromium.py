#!/usr/bin/env python3
"""decrypt-chromium.py — extract + decrypt Chromium (Edge) cookies/login passwords.
Usage: python -X utf8 decrypt-chromium.py <db> <keyhex> <cookies|logins> [out.jsonl]
Requires: sqlite3 (stdlib) + libcrypto-3.dll next to python.exe (portablepy).
v10/v11 = AES-256-GCM (32B key, 12B nonce, tag appended); falls back to AES-128-GCM.
Values without prefix -> DPAPI (report only, use pwsh for those).
"""
import sys, os, json, ctypes, ctypes.util, datetime

sysdir = os.path.dirname(os.path.abspath(__file__))
libname = os.path.join(os.path.dirname(sysdir), 'helpers', 'portablepy', 'libcrypto-3.dll')
if not os.path.exists(libname):
    libname = 'libcrypto-3.dll'
lib = ctypes.CDLL(libname)

# --- EVP AES-GCM via ctypes ---
lib.EVP_CIPHER_CTX_new.restype = ctypes.c_void_p
lib.EVP_aes_256_gcm.restype = ctypes.c_void_p
lib.EVP_aes_128_gcm.restype = ctypes.c_void_p
lib.EVP_DecryptInit_ex.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                   ctypes.c_void_p, ctypes.c_void_p]
lib.EVP_DecryptInit_ex.restype = ctypes.c_int
lib.EVP_DecryptUpdate.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int),
                                   ctypes.c_void_p, ctypes.c_int]
lib.EVP_DecryptUpdate.restype = ctypes.c_int
lib.EVP_DecryptFinal_ex.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
lib.EVP_DecryptFinal_ex.restype = ctypes.c_int
lib.EVP_CIPHER_CTX_ctrl.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
lib.EVP_CIPHER_CTX_ctrl.restype = ctypes.c_int
lib.EVP_CIPHER_CTX_free.argtypes = [ctypes.c_void_p]

EVP_CTRL_AEAD_SET_IVLEN = 0x9
EVP_CTRL_AEAD_SET_TAG = 0x11

def aes_gcm_decrypt(key: bytes, nonce: bytes, data: bytes) -> bytes | None:
    """data = ciphertext + 16B tag. Returns plaintext or None (tag fail)."""
    for keylen, cipher in ((len(key), None),):
        pass
    ct, tag = data[:-16], data[-16:]
    ctx = lib.EVP_CIPHER_CTX_new()
    if not ctx:
        return None
    try:
        if len(key) == 32:
            cipher = lib.EVP_aes_256_gcm()
        elif len(key) == 16:
            cipher = lib.EVP_aes_128_gcm()
        else:
            return None
        if lib.EVP_DecryptInit_ex(ctx, cipher, None, None, None) != 1:
            return None
        if lib.EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_AEAD_SET_IVLEN, len(nonce), None) != 1:
            return None
        if lib.EVP_DecryptInit_ex(ctx, None, None, key, nonce) != 1:
            return None
        out = ctypes.create_string_buffer(len(ct) + 16)
        outlen = ctypes.c_int(0)
        if lib.EVP_DecryptUpdate(ctx, out, ctypes.byref(outlen), ct, len(ct)) != 1:
            return None
        total = outlen.value
        tagbuf = ctypes.create_string_buffer(tag)
        if lib.EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_AEAD_SET_TAG, 16, tagbuf) != 1:
            return None
        finlen = ctypes.c_int(0)
        if lib.EVP_DecryptFinal_ex(ctx, ctypes.byref(out, total), ctypes.byref(finlen)) != 1:
            return None  # auth failure
        return out.raw[: total + finlen.value]
    finally:
        lib.EVP_CIPHER_CTX_free(ctx)

def try_decrypt(key: bytes, val: bytes):
    if val[:3] in (b'v10', b'v11'):
        nonce, body = val[3:15], val[15:]
        plain = aes_gcm_decrypt(key, nonce, body)
        if plain is None and len(key) != 16:
            # fallback: AES-128 with left-16 of key? not standard; try full anyway handled above
            pass
        return plain
    if val[:3] == b'v20':
        return None  # app-bound; needs system key
    return None  # DPAPI-wrapped or unknown

def main():
    db, keyhex, mode, outpath = sys.argv[1], sys.argv[2], sys.argv[3], (sys.argv[4] if len(sys.argv) > 4 else None)
    key = bytes.fromhex(keyhex)
    import sqlite3
    conn = sqlite3.connect('file:%s?mode=ro' % db.replace('\\', '/'), uri=True)
    cur = conn.cursor()
    n_ok = n_dpapi = n_fail = n_v20 = 0
    if mode == 'cookies':
        rows = cur.execute('SELECT host_key, name, encrypted_value, path, expires_utc FROM cookies').fetchall()
        out = open(outpath, 'w', encoding='utf-8') if outpath else None
        for host, name, ev, path, exp in rows:
            if not ev:
                continue
            plain = try_decrypt(key, ev)
            if plain is None:
                if ev[:3] == b'v20':
                    n_v20 += 1
                else:
                    n_dpapi += 1
                continue
            try:
                s = plain.decode('utf-8')
            except UnicodeDecodeError:
                s = plain.decode('latin-1', 'replace')
            n_ok += 1
            rec = {'host': host, 'name': name, 'value': s, 'path': path}
            line = json.dumps(rec, ensure_ascii=False)
            if out:
                out.write(line + '\n')
            else:
                print(line)
        if out:
            out.close()
    else:  # logins
        rows = cur.execute('SELECT origin_url, username_value, password_value FROM logins').fetchall()
        out = open(outpath, 'w', encoding='utf-8') if outpath else None
        for url, user, pw in rows:
            if not pw:
                continue
            plain = try_decrypt(key, pw)
            if plain is None:
                if pw[:3] == b'v20':
                    n_v20 += 1
                else:
                    n_dpapi += 1
                continue
            n_ok += 1
            rec = {'url': url, 'username': user, 'password': plain.decode('utf-8', 'replace')}
            line = json.dumps(rec, ensure_ascii=False)
            if out:
                out.write(line + '\n')
            else:
                print(line)
        if out:
            out.close()
    print('DECRYPTED=%d DPAPI_OR_NOKEY=%d V20=%d TOTAL_FAIL=%d' % (n_ok, n_dpapi, n_v20, n_fail), file=sys.stderr)

if __name__ == '__main__':
    main()