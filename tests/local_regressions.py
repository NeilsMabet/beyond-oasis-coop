from probe import Core,ROOT
from verify import word,put,byte,equip_sword
import json,time
import ctypes as C
c=Core(ROOT.parent/'generated/Beyond Oasis Coop Immortal.bin');c.capture=False
checks={};details={}
def vram():
 # state_save: signature, work RAM, Z80 RAM, zstate/zbank, IO, SAT, VRAM.
 s=c.state();off=16+65536+8192+1+4+16+1024
 return s[off:off+65536]
def both_positions(x,y):
 for base in (0x19e8,0x2898):
  put(c,base+8,x);put(c,base+12,y);put(c,base+16,0);put(c,base+20,0)
  put(c,base+0x8a,200);byte(c,base+0x82,0);byte(c,base+0x9d,0)
  byte(c,base+0x6c,0);byte(c,base+0x6d,0);byte(c,base+0x38,c.ram()[base+0x38]&0xf3)
  put(c,base+4,0);put(c,base+0x2a,0);put(c,base+0x72,0);put(c,base+0x74,0);put(c,base+0x76,0);put(c,base+0x78,0)
# Actual bow projectiles in each direction; each must spawn with P2 as owner.
c.load('test-beach');base=c.state();arrow_runs=[]
for direction in range(4):
 c.restore(base);put(c,0xd80,0x620);byte(c,0xdb0,0);byte(c,0xdb1,6)
 put(c,0xd7e,0xe);put(c,0x19ee,0xe);byte(c,0x198f,255);c.run(2)
 put(c,0x28a0,300);put(c,0x28a4,120);put(c,0x28ac,0);put(c,0x28ae,direction)
 hp=word(c.ram(),0x2922);seen=False;owner=None
 for f in range(90):
  c.run(1,(),[0] if f<8 else ())
  b=c.ram()
  if word(b,0x1b60)==0x34:
   seen=True;owner=int.from_bytes(b[0x1c0a:0x1c0e],'big')
 arrow_runs.append({'direction':direction,'spawned':seen,'owner':owner,'hp_before':hp,'hp_after':word(c.ram(),0x2922)})
checks['p2_bow_no_self_hit_four_directions']=all(r['spawned'] and r['owner']==0xff2898 and r['hp_before']==r['hp_after'] for r in arrow_runs)
details['bow']=arrow_runs
# Lethal damage cannot kill P2 or affect P1; there is no respawn timer.
c.restore(base);hp1=word(c.ram(),0x1a72);put(c,0x291e,0x7fff);c.run(8)
checks['p2_lethal_damage_ignored']=word(c.ram(),0x2898)==2 and word(c.ram(),0x2922)==200
checks['p2_damage_does_not_affect_p1']=word(c.ram(),0x1a72)==hp1
checks['p2_no_respawn_timer']=word(c.ram(),0x2894)==0
# One original melee enemy, with both heroes in its attack area.
c.load('test-combat')
record=bytes.fromhex(json.loads((ROOT/'melee-fixture.json').read_text())['actor_record_hex'])
swapped=bytearray(record)
for i in range(0,len(swapped),2):swapped[i],swapped[i+1]=swapped[i+1],swapped[i]
C.memmove(c.dll.retro_get_memory_data(2)+0x1f0c,bytes(swapped),len(swapped))
for i in range(1,19):
 if i!=7:put(c,0x19e8+188*i,0)
both_positions(226,160);put(c,0x1f14,250);put(c,0x1f18,160);put(c,0x1f20,0)
# Pin the original melee variant: ROM checksum length changes cold-boot RNG.
put(c,0x1f0e,1);put(c,0x1f10,0);put(c,0x1f22,3);byte(c,0x1f43,0x20)
put(c,0x2948,0);put(c,0x294a,0);put(c,0x294c,0);put(c,0x294e,0)
first=None
for frame in range(1200):
 c.run(1);b=c.ram();pending=[word(b,0x1a6e),word(b,0x291e)]
 if any(pending):first={'frame':frame,'pending_damage':pending};break
checks['original_enemy_melee_still_hits_p1']=first is not None and first['pending_damage'][0]>0
details['same_attack']=first
c.run(20);healths=[word(c.ram(),0x1a72),word(c.ram(),0x2922)]
checks['p1_damage_unchanged_p2_invulnerable']=0<healths[0]<200 and healths[1]==200
# Independently observe a real attack against P2 in the full encounter.
c.load('test-combat');c.run(30);enemy_hit=None
for frame in range(1200):
 c.run(1);b=c.ram()
 if word(b,0x291e):enemy_hit={'frame':frame,'pending_damage':word(b,0x291e)};break
checks['real_enemy_attack_hits_p2']=enemy_hit is not None
c.run(8)
checks['p2_reacts_to_real_enemy_hit_without_hp_loss']=word(c.ram(),0x289c) in (0x18,0x1a,0x20) and word(c.ram(),0x2922)==200
details['p2_enemy_hit']=enemy_hit
details['health_after_same_attack']=healths
result={'checks':checks,'all_passed':all(checks.values()),'details':details}
# Separate weapon art while the other player walks.
c.restore(base);equip_sword(c,255);put(c,0x28a0,330);put(c,0x28ae,1);c.run(30)
before=vram();before_key=word(c.ram(),0x1a44);c.run(18,(),[7]);after=vram()
checks['stationary_p1_weapon_art_not_overwritten']=before[0x9f00:0xa300]==after[0x9f00:0xa300] and before_key==word(c.ram(),0x1a44)
checks['p2_has_separate_weapon_tiles']=word(c.ram(),0x28f2)==0x6e1 and before[0xdc20:0xde20]!=after[0xdc20:0xde20]
c.run(20);before=vram();p2_key=word(c.ram(),0x28f4);c.run(18,[6]);after=vram()
checks['stationary_p2_weapon_art_not_overwritten']=before[0xdc20:0xde20]==after[0xdc20:0xde20] and p2_key==word(c.ram(),0x28f4)
# Open the real map through the real inventory, then return without P2 movement.
c.restore(base);put(c,0x28a0,330);c.run(30);before=vram()
def pulse(button):c.run(1,[button]);c.run(15)
pulse(3)
for _ in range(3):pulse(5)
pulse(0);c.run(30);map_art=vram()
for button in [8,8,3]:
 if c.ram()[0x185d]==0:break
 pulse(button)
c.run(4);after=vram()
checks['map_closed']=c.ram()[0x185d]==0
checks['p2_art_restored_without_movement']=before[0xb800:0xba00]==after[0xb800:0xba00]
details['weapon_keys']=[before_key,word(c.ram(),0x1a44)]
result={'checks':checks,'all_passed':all(checks.values()),'details':details}
(ROOT/'local-regressions.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)

assert result['all_passed']

