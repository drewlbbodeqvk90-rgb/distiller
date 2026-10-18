#!/usr/bin/env python3
"""parse-dpapi-blob.py — parse DPAPI blob structure (impacket DPAPI_BLOB layout).
Usage: python -X utf8 parse-dpapi-blob.py <file> <offset>
"""
import sys, struct

def u32(b, o):
    return struct.unpack_from('<I', b, o)[0]

def parse(b, base=0, label=''):
    o = 0
    def take(n, name):
        nonlocal o
        v = b[o:o+n]
        o += n
        return v
    def take4(name):
        nonlocal o
        v = u32(b, o)
        o += 4
        return v
    print(f'== {label} (offset {base}, len {len(b)})')
    ver = take4('Version'); print(f'  Version           = {ver} (off {base+o-4})')
    gcred = take(16, 'GuidCredential'); print(f'  GuidCredential    = {gcred.hex()}')
    mkver = take4('MasterKeyVersion'); print(f'  MasterKeyVersion  = {mkver}')
    gmk = take(16, 'GuidMasterKey'); g = struct.unpack('<IHH8s', gmk)
    guid = f'{g[0]:08x}-{g[1]:04x}-{g[2]:04x}-{g[3][:2].hex()}-{g[3][2:].hex()}'
    print(f'  GuidMasterKey     = {guid}')
    flags = take4('Flags'); print(f'  Flags             = 0x{flags:08x}')
    dlen = take4('DescriptionLen'); print(f'  DescriptionLen    = {dlen}')
    desc = take(dlen, 'Description')
    try:
        print(f'  Description       = {desc.decode("utf-16-le")!r}')
    except Exception as e:
        print(f'  Description       = {desc.hex()} ({e})')
    algo = take4('CryptAlgo'); print(f'  CryptAlgo         = 0x{algo:08x}')
    alen = take4('CryptAlgoLen'); print(f'  CryptAlgoLen      = {alen}')
    slen = take4('SaltLen'); print(f'  SaltLen           = {slen}')
    salt = take(slen, 'Salt'); print(f'  Salt              = {salt.hex()}')
    hklen = take4('HMacKeyLen'); print(f'  HMacKeyLen        = {hklen}')
    hk = take(hklen, 'HMacKey'); print(f'  HMacKey           = {hk.hex()}')
    halgo = take4('HashAlgo'); print(f'  HashAlgo          = 0x{halgo:08x}')
    halen = take4('HashAlgoLen'); print(f'  HashAlgoLen       = {alen and halen}')
    hmlen = take4('HMacLen'); print(f'  HMacLen           = {hmlen}')
    hm = take(hmlen, 'HMac'); print(f'  HMac              = {hm.hex()}')
    dlen2 = take4('DataLen'); print(f'  DataLen           = {dlen2}')
    data = take(dlen2, 'Data'); print(f'  Data[0:16]        = {data[:16].hex()} ... ({dlen2}B)')
    slen2 = take4('SignLen'); print(f'  SignLen           = {slen2}')
    sign = take(slen2, 'Sign'); print(f'  Sign              = {sign.hex()}')
    print(f'  parsed {o} / {len(b)} bytes  {"OK-EXACT" if o == len(b) else "MISMATCH remain=%d" % (len(b)-o)}')

if __name__ == '__main__':
    path, off = sys.argv[1], int(sys.argv[2])
    data = open(path, 'rb').read()
    parse(data[off:], off, path)