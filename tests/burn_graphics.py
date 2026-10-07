"""Separate graphics banks; optionally exercise a user state without shipping it.
Burn flags isolate rendering; actual fire attacks remain in damage_regression.py.
"""
from pathlib import Path
import argparse,json,zlib,hashlib
from PIL import Image
from probe import Core,ROOT
from verify import ROM,word,put,byte
parser=argparse.ArgumentParser();parser.add_argument('--state',required=True,type=Path);parser.add_argument('--baseline-rom',type=Path);args=parser.parse_args()
raw=args.state.read_bytes();state=raw
if state.startswith(b'#RZIPv'):
 p=20;out=bytearray()
 while p<len(state):
  n=int.from_bytes(state[p:p+4],'little');p+=4;out.extend(zlib.decompress(state[p:p+n]));p+=n
 state=bytes(out)
if state.startswith(b'RASTATE'):state=state[16:16+int.from_bytes(state[12:16],'little')]
assert state.startswith(b'GENPLUS-GX')
from effect_bank import decode
def swapped(b):return b''.join(b[i:i+2][::-1] for i in range(0,len(b),2))
def vram(c):
 off=16+65536+8192+1+4+16+1024
 return swapped(c.state()[off:off+65536])
rom=ROM.read_bytes();effects=decode(rom);assert len(effects)==0xf00
def frame(b,base,key):
 mapping=int.from_bytes(b[base+0x1a:base+0x1e],'big');art=int.from_bytes(b[base+0x1e:base+0x22],'big')
 a=mapping+2*key;delta=int.from_bytes(rom[a:a+2],'big')
 if not delta:return b''
 a+=delta;n=int.from_bytes(rom[a:a+2],'big')+1;out=bytearray();assert n<=80
 for i in range(n):
  at=a+2+6*i;size=rom[at];tile=int.from_bytes(rom[at+2:at+4],'big')&0x7ff
  count=(((size>>2)&3)+1)*((size&3)+1);source=art+((size&0xf0)<<12)+tile*32
  out.extend(rom[source:source+count*32])
 return bytes(out)
checks={};details={'state_sha256':hashlib.sha256(raw).hexdigest(),'effect_bank_bytes':len(effects),'scenarios':[]}
if args.baseline_rom:
 c=Core(args.baseline_rom);c.restore(state);c.run(10)
 different=sum(a!=b for a,b in zip(vram(c)[0xa900:0xb800],effects));checks['old_effect_bank_corruption_reproduced']=different>0;details['old_corrupted_bytes']=different
 c.dll.retro_unload_game();c.dll.retro_deinit()
for who in [0,1,2]:
 c=Core(ROM);c.restore(state);history=[[],[]];effect_ok=True;body_ok=[True,True];burn_seen=[False,False]
 for i,a in enumerate([0x19e8,0x2898]):
  if who==2 or who==i:byte(c,a+0x39,c.ram()[a+0x39]|8)
 for t in range(160):
  c.run(1, [7] if 30<=t<45 else (), [6] if 60<=t<75 else ())
  b=c.ram();v=vram(c)
  for i,a in enumerate([0x19e8,0x2898]):
   key=word(b,a+0x34);history[i].append(key);history[i]=history[i][-4:]
   burn_seen[i]|=bool(b[a+0x39]&8)
   if t>4:
    at=word(b,a+0x18)*32
    body_ok[i]&=any(v[at:at+len(f)]==f for k in history[i] if (f:=frame(b,a,k)))
  if t>4:effect_ok &= v[0xa900:0xb800]==effects
  if t==10:Image.fromarray(c.picture).save(ROOT.parent/f'burn-player-{who+1}.png')
 checks[f'case_{who}_effects_intact']=effect_ok
 checks[f'case_{who}_both_bodies_intact']=all(body_ok)
 checks[f'case_{who}_burn_visible']=all(burn_seen[i] for i in ([0,1] if who==2 else [who]))
 checks[f'case_{who}_p2_banks_migrated']=word(b,0x28b0)==0x5c0 and word(b,0x28f2)==0x6e1
 saved=c.state();c.run(60,(),[7]);expected=c.state();c.restore(saved);c.run(60,(),[7])
 checks[f'case_{who}_deterministic']=c.state()==expected
 details['scenarios'].append({'burn_target':who,'bodies_match_original_frames':body_ok,'effects_match':effect_ok,'burn_seen':burn_seen})
 c.dll.retro_unload_game();c.dll.retro_deinit()
report={'checks':checks,'details':details,'all_passed':all(checks.values()),'rom_sha256':hashlib.sha256(rom).hexdigest()}
(ROOT/'burn-graphics.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));assert report['all_passed']
