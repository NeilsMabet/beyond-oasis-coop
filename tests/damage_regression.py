"""Damage isolation regression using a user-supplied cave state.
The normal scenario uses original actors unchanged. Fire cases instantiate the
original type-0x24 actor from the ROM's initialization table and run its stock
fire attack, rather than writing pending damage into a hero.
"""
from pathlib import Path
import argparse,struct,zlib,hashlib,json,ctypes as C
from probe import Core,ROOT
from effect_bank import decode
from verify import ROM,put,byte,word
parser=argparse.ArgumentParser()
parser.add_argument('--state',required=True,type=Path)
parser.add_argument('--baseline-rom',type=Path)
args=parser.parse_args()
raw=args.state.read_bytes();data=raw
if data.startswith(b'#RZIPv'):
 cursor=20;out=bytearray()
 while cursor<len(data):
  length=int.from_bytes(data[cursor:cursor+4],'little');cursor+=4
  out.extend(zlib.decompress(data[cursor:cursor+length]));cursor+=length
 assert len(out)==int.from_bytes(data[12:20],'little');data=bytes(out)
if data.startswith(b'RASTATE'):
 assert data[8:12]==b'MEM ';length=int.from_bytes(data[12:16],'little');data=data[16:16+length]
assert data.startswith(b'GENPLUS-GX 1.7.C')
checks={};details={'supplied_state_sha256':hashlib.sha256(raw).hexdigest()}
def close(c):c.dll.retro_unload_game();c.dll.retro_deinit()
def setup(rom,reverse=False):
 c=Core(rom);c.capture=False;c.restore(data)
 one,two=((168,224),(250,160)) if reverse else ((250,160),(168,224))
 for base,(x,y) in [(0x19e8,one),(0x2898,two)]:
  put(c,base+8,x);put(c,base+12,y)
 return c
def ordinary(rom,reverse=False):
 c=setup(rom,reverse);hp=word(c.ram(),0x1a72);pending=[False,False];reacted=False
 for _ in range(120):
  c.run(1);b=c.ram();pending[0]|=word(b,0x1a6e)!=0;pending[1]|=word(b,0x291e)!=0
  reacted |= word(b,0x289c) in (0x18,0x1a,0x20)
 result={'p1_hp_before':hp,'p1_hp_after':word(b,0x1a72),'p2_hp_after':word(b,0x2922),'hit_seen':pending,'p2_reaction_seen':reacted}
 close(c);return result
def fire(rom,reverse=False,attack=0x12):
 c=setup(rom,reverse);b=c.ram();hp=word(b,0x1a72)
 for i in range(4,19):put(c,0x19e8+188*i,0)
 # Same actor initialization as stock ROM routine 0x8D06.
 template=rom.read_bytes()[0x3f2fa+(0x24<<4)-0x20:][:32]
 actor=bytearray(188);actor[:2]=(0x24).to_bytes(2,'big');actor[0x4a:0x4c]=template[:2]
 for off in [0x42,0x44,0x46]:actor[off:off+2]=bytes([0,template[2]])
 for off,idx in [(0x48,3),(0x49,4),(0x3d,5),(0x3a,7),(0x36,8),(0x37,9),(0x38,10),(0x3c,11)]:actor[off]=template[idx]
 actor[0x4c:0x4e]=bytes([0,template[6]])
 for off,idx in [(0x1a,12),(0x1e,16),(0x26,20),(0x22,24),(0x5e,28)]:actor[off:off+4]=template[idx:idx+4]
 for off in [0x2c,0x34,0x5c]:actor[off:off+2]=b'\xff\xff'
 swapped=bytearray(actor)
 for i in range(0,188,2):swapped[i],swapped[i+1]=swapped[i+1],swapped[i]
 C.memmove(c.dll.retro_get_memory_data(2)+0x1cd8,bytes(swapped),188)
 for base in [0x19e8,0x2898,0x1cd8]:
  put(c,base+16,0);put(c,base+18,0);put(c,base+20,0)
  for off in [0x4e,0x50,0x52,0x54,0x56,0x58,0x72,0x74,0x76,0x78]:put(c,base+off,0)
  for off in [0x38,0x39,0x82,0x6c,0x6d]:byte(c,base+off,0)
 put(c,0x1ce0,168);put(c,0x1ce4,224);put(c,0x1cdc,attack);put(c,0x1d02,0)
 for off in [0xa2,0xb4,0x40,0x41]:byte(c,0x1cd8+off,0)
 burned=[False,False];pending=[0,0];timers=[0,0];reaction=False
 for _ in range(80):
  c.run(1);b=c.ram()
  for i,base in enumerate([0x19e8,0x2898]):
   burned[i]|=bool(b[base+0x39]&8);pending[i]|=word(b,base+0x86)
  timers[0]=max(timers[0],b[0x198e]);timers[1]=max(timers[1],b[0x27ec])
  reaction |= word(b,0x289c) in (0x18,0x1a,0x20)
 result={'p1_hp_before':hp,'p1_hp_after':word(b,0x1a72),'p2_hp_after':word(b,0x2922),'burn_seen':burned,'pending_flags':pending,'immunity_timers':timers,'p2_reaction_seen':reaction}
 # Verify the VM is still running and the final state replays deterministically.
 saved=c.state();off=16+65536+8192+1+4+16+1024;native=saved[off:off+65536];vram=b''.join(native[i:i+2][::-1] for i in range(0,len(native),2));result['graphics_intact']=vram[0xa900:0xb800]==decode(rom.read_bytes());c.run(60,(),[7]);expected=c.state();c.restore(saved);c.run(60,(),[7]);result['replay_deterministic']=expected==c.state()
 close(c);return result
if args.baseline_rom:
 old=ordinary(args.baseline_rom);oldfire=fire(args.baseline_rom)
 checks['old_damage_transfer_reproduced']=old['p1_hp_after']<old['p1_hp_before'] and not old['hit_seen'][1]
 checks['old_fire_transfer_reproduced']=oldfire['burn_seen']==[True,False] and oldfire['p1_hp_after']<oldfire['p1_hp_before']
 details['old_normal']=old;details['old_fire']=oldfire
normal=ordinary(ROM);legitimate=ordinary(ROM,True);flame=fire(ROM);p1flame=fire(ROM,True);secondflame=fire(ROM,attack=0xc)
checks['p2_hits_do_not_damage_distant_p1']=normal['p1_hp_after']==normal['p1_hp_before'] and normal['hit_seen']==[False,True]
checks['p2_keeps_reaction_and_immortality']=normal['p2_hp_after']==200 and normal['p2_reaction_seen']
checks['direct_hits_still_damage_p1']=legitimate['p1_hp_after']<legitimate['p1_hp_before']
checks['p2_fire_does_not_burn_or_damage_p1']=flame['p1_hp_after']==flame['p1_hp_before'] and flame['burn_seen']==[False,True]
checks['p2_fire_reaction_and_hp_preserved']=flame['p2_reaction_seen'] and flame['p2_hp_after']==200
checks['direct_fire_still_damages_p1']=p1flame['p1_hp_after']<p1flame['p1_hp_before'] and p1flame['burn_seen']==[True,False]
checks['alternate_fire_attack_is_isolated']=secondflame['p1_hp_after']==secondflame['p1_hp_before'] and secondflame['burn_seen']==[False,True]
checks['alternate_fire_immunity_belongs_to_p2']=secondflame['immunity_timers'][0]==0 and secondflame['immunity_timers'][1]>0
checks['fire_states_replay_deterministically']=all(x['replay_deterministic'] for x in [flame,p1flame,secondflame])
checks['actual_fire_attacks_preserve_effect_graphics']=all(x['graphics_intact'] for x in [flame,p1flame,secondflame])
details.update(normal=normal,p1_direct_hit=legitimate,fire=flame,p1_direct_fire=p1flame,alternate_fire=secondflame)
result={'checks':checks,'details':details,'all_passed':all(checks.values()),'rom_sha256':hashlib.sha256(ROM.read_bytes()).hexdigest()}
(ROOT/'damage-regression.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));assert result['all_passed']
