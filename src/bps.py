from pathlib import Path
import struct,zlib,json
ROOT=Path(__file__).resolve().parent

def number(n):
    out=bytearray()
    while True:
        v=n&127;n>>=7
        if not n:out.append(v|128);return bytes(out)
        out.append(v);n-=1

def create(source,target):
    meta=b'Beyond Oasis Coop Immortal; original animation; dark P2; title caption; invulnerable P2.'
    out=bytearray(b'BPS1'+number(len(source))+number(len(target))+number(len(meta))+meta)
    source_cursor=0;target_cursor=0;written=0;stats=[0,0,0,0]
    def action(mode,data_or_length,offset=None):
        nonlocal written,source_cursor,target_cursor
        length=len(data_or_length) if mode==1 else data_or_length
        assert length>0
        out.extend(number(((length-1)<<2)|mode));stats[mode]+=length
        if mode==1:out.extend(data_or_length)
        if mode in (2,3):
            cursor=source_cursor if mode==2 else target_cursor
            delta=offset-cursor;out.extend(number((abs(delta)<<1)|(delta<0)))
            if mode==2:source_cursor=offset+length
            else:target_cursor=offset+length
        written+=length
    # Unchanged original bytes refer directly to the user's input ROM.
    i=0
    while i<len(source):
        same=source[i]==target[i];start=i
        while i<len(source) and (source[i]==target[i])==same:i+=1
        action(0,i-start) if same else action(1,target[start:i])
    # Small new executable payload, then its long zero-filled alignment gap.
    payload=target[len(source):0x310000];code=payload.rstrip(b'\0')
    if code:action(1,code)
    gap=len(payload)-len(code)
    if gap:
        action(1,b'\0')
        if gap>1:action(3,gap-1,written-1)
    # SourceCopy relocates original tiles. Only altered bytes are literals.
    shaded=target[0x310000:0x35f100];original=source[0xc0000:0x10f100];assert len(shaded)==len(original)
    i=0
    while i<len(shaded):
        same=shaded[i]==original[i];start=i
        while i<len(shaded) and (shaded[i]==original[i])==same:i+=1
        action(2,i-start,0xc0000+start) if same else action(1,shaded[start:i])
    action(1,target[0x35f100:])
    assert written==len(target)
    out.extend(struct.pack('<II',zlib.crc32(source),zlib.crc32(target)))
    out.extend(struct.pack('<I',zlib.crc32(out)))
    return bytes(out),stats

def apply(source,patch):
    assert patch[:4]==b'BPS1' and zlib.crc32(patch[:-4])==struct.unpack('<I',patch[-4:])[0]
    cursor=4
    def read_number():
        nonlocal cursor
        value=0;shift=1
        while True:
            byte=patch[cursor];cursor+=1;value+=(byte&127)*shift
            if byte&128:return value
            shift<<=7;value+=shift
    source_size=read_number();target_size=read_number();meta=read_number();cursor+=meta
    assert source_size==len(source)
    output=bytearray();source_cursor=0;target_cursor=0
    while len(output)<target_size:
        v=read_number();mode=v&3;length=(v>>2)+1;at=len(output)
        if mode==0:output.extend(source[at:at+length])
        elif mode==1:output.extend(patch[cursor:cursor+length]);cursor+=length
        elif mode==2:
            delta=read_number();source_cursor+=-(delta>>1) if delta&1 else delta>>1
            output.extend(source[source_cursor:source_cursor+length]);source_cursor+=length
        else:
            delta=read_number();target_cursor+=-(delta>>1) if delta&1 else delta>>1
            for _ in range(length):output.append(output[target_cursor]);target_cursor+=1
    assert cursor==len(patch)-12
    assert (zlib.crc32(source),zlib.crc32(output))==struct.unpack('<II',patch[-12:-4])
    return bytes(output)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--rom',required=True,type=Path)
    parser.add_argument('--target',type=Path,default=ROOT.parent/'generated/Beyond Oasis Coop Immortal.bin')
    parser.add_argument('--output',type=Path,default=ROOT.parent/'beyond-oasis-coop-immortal.bps')
    args=parser.parse_args()
    source=args.rom.read_bytes();target=args.target.read_bytes()
    patch,stats=create(source,target)
    assert apply(source,patch)==target
    args.output.write_bytes(patch)
    print('BPS bytes',len(patch),'action bytes',stats)
