"""P2 attacks are interrupted by the original hit reaction, without HP loss."""
import json,hashlib
from PIL import Image
from probe import Core,ROOT
from verify import ROM,put,byte,word
c=Core(ROM);c.capture=False;c.load('test-beach')
for base,x in [(0x19e8,256),(0x2898,300)]:
 put(c,base+8,x);put(c,base+12,120);put(c,base+0x16,1)
c.run(8,[0],[0]);before=c.ram();checks={};details={}
checks['both_players_started_real_attack']=word(before,0x19ec)==0xa and word(before,0x289c)==0xa
for base in [0x19e8,0x2898]:
 put(c,base+0x86,8);put(c,base+0x84,0);byte(c,base+0x82,1);byte(c,base+0x83,6)
 put(c,base+0x4e,1);put(c,base+0x50,0);put(c,base+0x52,0);put(c,base+0x54,0)
 put(c,base+0x7e,0xff);put(c,base+0x80,0x1cd8)
c.run(2);b=c.ram()
checks['same_hit_interrupts_both_attacks']=word(b,0x19ec)==0x18 and word(b,0x289c)==0x18
checks['only_p1_loses_hp']=word(b,0x1a72)==192 and word(b,0x2922)==200
checks['no_death_or_respawn']=word(b,0x2898)==2 and word(b,0x2894)==0
# Compare original reaction state/animation sequence and knockback movement.
fields=[4,0x10,0x14,0x16,0x2a,0x2c,0x2e,0x30,0x32,0x56,0x58,0x72,0x74,0x76,0x78]
same=True;positions=[];start=[word(b,0x19f0),word(b,0x19f4),word(b,0x28a0),word(b,0x28a4)]
for frame in range(100):
 c.run(1);b=c.ram()
 same &= all(word(b,0x19e8+f)==word(b,0x2898+f) for f in fields)
 positions.append([word(b,0x19f0)-start[0],word(b,0x19f4)-start[1],word(b,0x28a0)-start[2],word(b,0x28a4)-start[3]])
checks['reaction_animation_matches_p1_all_frames']=same
checks['knockback_displacement_matches_p1']=all(a==x and b==y for a,b,x,y in positions)
checks['knockback_actually_moves_p2']=any(x or y for a,b,x,y in positions)
c.run(120);x=word(c.ram(),0x28a0);c.run(20,(),[7]);checks['p2_can_move_after_recovery']=word(c.ram(),0x28a0)>x
# Repeated lethal body knockback never kills P2 or hurts P1 by contact.
c.load('test-beach');hp1=word(c.ram(),0x1a72);put(c,0x291e,0x7fff);c.run(2);reacted=word(c.ram(),0x289c) in (0x18,0x1a,0x20);c.run(14)
checks['knocked_back_p2_does_not_damage_p1']=word(c.ram(),0x1a72)==hp1
checks['lethal_hit_reaction_keeps_p2_alive']=word(c.ram(),0x2898)==2 and word(c.ram(),0x2922)==200 and reacted
details['reaction_fields_compared']=[hex(f) for f in fields]
details['maximum_knockback_pixels']=max(max(abs(v) for v in row) for row in positions)
result={'checks':checks,'details':details,'all_passed':all(checks.values()),'rom_sha256':hashlib.sha256(ROM.read_bytes()).hexdigest()}
(ROOT/'hit-reaction.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));assert result['all_passed']
