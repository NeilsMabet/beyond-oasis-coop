"""Build from the supplied payload, or reassemble with --assembler vasmm68k_mot.exe."""
import argparse,pathlib,hashlib,subprocess,struct,json
from shade import shade_art,ART_TARGET
import re
from effects import decode
root=pathlib.Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--rom',required=True,type=pathlib.Path)
parser.add_argument('--output',type=pathlib.Path,default=root.parent/'generated/Beyond Oasis Coop Immortal.bin')
parser.add_argument('--assembler',type=pathlib.Path)
args=parser.parse_args()
if args.rom.resolve()==args.output.resolve():raise SystemExit('Refusing to overwrite original ROM')
manifest=json.loads((root.parent/'manifest.json').read_text())
original=args.rom.read_bytes()
if hashlib.sha256(original).hexdigest()!=manifest['original_sha256']:raise SystemExit('Unsupported ROM')
if args.assembler:
 subprocess.run([str(args.assembler.resolve()),'-Fbin','-m68000','-L',str(root/'coop.lst'),'-o',str(root/'payload.bin'),str(root/'coop.asm')],check=True,cwd=root)
payload=(root/'payload.bin').read_bytes()
if hashlib.sha256(payload).hexdigest()!=manifest['payload_sha256']:raise SystemExit('Payload differs from pinned release; update manifest intentionally for development')
b=bytearray(original);b.extend(payload)
assert len(b)==ART_TARGET
b.extend(shade_art(original));b.extend(bytes((-len(b))%32))
assert len(b)==0x35f100
effects=decode(original);assert len(effects)==0xf00
b.extend(effects)
def patch(at,expect,new):
    expect=bytes.fromhex(expect);new=bytes.fromhex(new)
    assert len(expect)==len(new)
    assert b[at:at+len(expect)]==expect,(hex(at),b[at:at+len(expect)].hex())
    b[at:at+len(expect)]=new
patch(0x33d2,'4a3900ff0bfd','4eb90030002c')
patch(0xb922,'488048c03e2e0008','4ef9003000404e71') # masked projectiles/fire use actual target
patch(0xb856,'3c2e0008d246','4ef900300044') # body impacts use actual target
patch(0x14df6,'13fc000e00ff198e','4eb9003000484e71') # fire immunity belongs to the hit hero
patch(0xbcea,'082e00030037660001a4','4ef90030003c4e714e71') # route raw enemy collision paths to the selected real hero
patch(0xb7f0,'202e007eb088','4ef900300038') # thrown heroes do not damage each other
patch(0x5884,'92403d41008a','4eb900300034') # keep hit reaction; suppress only P2 HP subtraction
patch(0x57fa,'302e008667000142','4ef9003000304e71')
patch(0x8b2a,'61006c5c6100ca4a610053b8','4eb9003000004e714e714e71')
patch(0x217c,'43f900ff165c41f900a1000361000808','4eb9003000044e714e714e714e714e71')
patch(0xbcd8,'23fc0000beba00ff1940','4ef9003000084e714e71')
patch(0xbeba,'4a28006d6714','4ef90030000c')
patch(0x101f4,'7610','760e') # scripted hostile-enemy count excludes META/P2
patch(0x1021c,'7610','760e') # script enemy count excludes two reserved slots
patch(0x10238,'7010','700e') # script object lookup excludes reserved slots
patch(0xdf16,'48e701024e904cdf4080','4eb9003000104e714e71')
patch(0xbe68,'bdfc00ff19e8','4eb900300014')
patch(0xbd40,'bdfc00ff19e8','4eb900300014')
patch(0xa2a6,'4df900ff13cc','4eb900300018')
patch(0x82ae,'720636014441','4ef90030001c')
patch(0x82f8,'362e0016671c','4ef900300020')
patch(0xb954,'4a6800006f000062','4ef9003000244e71')
patch(0x3d2e,'51f900ff185d','4ef900300028')
patch(0xda24,'7011','700f') # DA1A also excludes META/P2
patch(0xa232,'4a6e00006b0000ec082e00000036','4ef90030004c4e714e714e714e71') # hide P2 while original dialogue owns its bank
patch(0xda34,'7010','700e')
patch(0xda6c,'7011','700f')
patch(0xda7c,'7010','700e')
for route in json.loads((root/'target-routes.json').read_text()):
 address=route['address'];old=bytes.fromhex(route['original'])
 replacement=bytes.fromhex('4eb9')+address.to_bytes(4,'big')+bytes.fromhex('4e71')*((len(old)-6)//2)
 patch(route['pc'],route['original'],replacement.hex())
struct.pack_into('>I',b,0x1a4,len(b)-1)
if len(b)%2:b.append(0)
struct.pack_into('>H',b,0x18e,sum(struct.unpack('>'+str((len(b)-512)//2)+'H',b[512:]))&0xffff)

if hashlib.sha256(b).hexdigest()!=manifest['patched_sha256']:raise SystemExit('Build hash mismatch')
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_bytes(b)
print(args.output,hashlib.sha256(b).hexdigest())
