"""Check real layouts/transfers across bounded gameplay and menu scenarios."""
from pathlib import Path
import json,zlib,hashlib
from probe import Core,ROOT
from verify import ROM,word,put,byte
W=ROOT.parents[2];rom=ROM.read_bytes();off=16+65536+8192+1+4+16+1024
def unpack(p):
 b=p.read_bytes()
 if b.startswith(b'#RZIPv'):
  at=20;out=bytearray()
  while at<len(b):n=int.from_bytes(b[at:at+4],'little');at+=4;out.extend(zlib.decompress(b[at:at+n]));at+=n
  b=bytes(out)
 if b.startswith(b'RASTATE'):b=b[16:16+int.from_bytes(b[12:16],'little')]
 return b
cases=[('beach',ROOT/'test-beach.state',240),('combat',ROOT/'test-combat.state',360),('village',ROOT/'test-village.state',240),('cave',W/'work/damage-investigation/user.state',360),('fire',W/'work/burn-user.state',360),('map',ROOT/'test-beach.state',360),('story',W/'work/first-battle-stuck.state',1100)]
failures=[];details=[];modes=set();total=0;locked_frames=0;resumed=False;story_locked=False
for name,path,frames in cases:
 c=Core(ROM);c.capture=False;c.restore(unpack(path));seen=0;transfers=0
 for f in range(frames):
  one=[];two=[]
  if name=='story':one=[0] if f%68<8 else []
  elif name=='map':
   # Real Start/inventory/map sequence, also covered by local_regressions.
   buttons={8:3,24:5,40:5,56:5,72:0,180:8,200:8,220:3}
   one=[buttons[f]] if f in buttons else []
  else:two=[[7,5,6,4][(f//40)%4]] if f%80<40 else [0] if f%50<8 else []
  c.run(1,one,two);b=c.ram();state=c.state();reg=state[off+65536+256:off+65536+288];modes.add((reg[11],reg[13]))
  if f<5:continue
  active=word(b,0x2898)==2 and b[0x185d]==0 and b[0x1983]==0
  if name=='story':
   if b[0x1983]:story_locked=True;locked_frames+=1
   elif story_locked and active and word(b,0x28cc)!=0xffff:resumed=True
  if active:
   seen+=1
   if reg[11]&3 or reg[13]!=0x37:failures.append((name,f,'incompatible hscroll mode',reg[11],reg[13]))
   if (word(b,0x28b0),word(b,0x28f2))!=(0x5c0,0x6e1):failures.append((name,f,'wrong P2 bank'))
  q=int.from_bytes(b[0x1892:0x1896],'big')&0xffff
  if not (0x10b4<=q<=0x134c and (q-0x10b4)%8==0):failures.append((name,f,'DMA queue outside known capacity',q));continue
  for a in range(0x10b4,q,8):
   source=(int.from_bytes(b[a:a+4],'big')&0x7fffff)*2;dst=word(b,a+4);length=word(b,a+6)*2;transfers+=1
   if b[0x1983] and 0x310000<=source<0x35f100:failures.append((name,f,'P2 body upload during dialogue'))
   if active and max(dst,0xb800)<min(dst+length,0xc000) and not (0x310000<=source<0x35f100):failures.append((name,f,'foreign body transfer',source,dst,length,{'1982':b[0x1982],'1983':b[0x1983],'17b8':b[0x17b8],'185d':b[0x185d],'185e':b[0x185e],'17bd':b[0x17bd]}))
   if active and max(dst,0xdc20)<min(dst+length,0xde20) and not (0x110000<=source<0x160000):failures.append((name,f,'foreign weapon transfer',source,dst,length))
 details.append({'scenario':name,'frames':frames,'active_frames':seen,'queued_transfers_observed':transfers});total+=frames
 c.dll.retro_unload_game();c.dll.retro_deinit()
checks={'dialogue_guard_exercised_and_body_resumed':locked_frames>0 and resumed,'all_scenarios_have_active_gameplay':all(x['active_frames']>0 for x in details),'no_layout_or_transfer_conflicts_observed':not failures,'only_full_screen_hscroll_observed':all(mode==0 and table==0x37 for mode,table in modes)}
report={'checks':checks,'all_passed':all(checks.values()),'rom_sha256':hashlib.sha256(rom).hexdigest(),'frames':total,'modes':sorted(modes),'scenarios':details,'failures':failures[:30],'scope':'Bounded scenes and sampled queues; not full campaign coverage or a trace of every direct CPU VDP write.'}
(ROOT/'vram-regression.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));assert report['all_passed']
