"""Reproduce the first-boss softlock, then resume the same state with the fix.
Only the boss receives injected pending damage; all death, dialogue, cleanup and
room transitions execute through the original game code and real input.
"""
from pathlib import Path
import tempfile,struct,json,hashlib
from PIL import Image
from probe import Core,ROOT
from verify import ROM,word,put

def snapshot(c):
 b=c.ram()
 return {'script':hex(int.from_bytes(b[0x17b2:0x17b6],'big')),
         'room':hex(int.from_bytes(b[0x16ec:0x16f0],'big')),
         'p2_type':word(b,0x2898),'p2_health':word(b,0x2922),
         'p2_death_timer':word(b,0x2894),'story_lock':b[0x1983],
         'active_enemy_slots':sum(word(b,0x19e8+188*i)>0 and word(b,0x19e8+188*i)<0x8000 for i in range(4,19))}
def advance_dialogue(c):
 for _ in range(14):c.run(8,[0]);c.run(60)
def close(c):c.dll.retro_unload_game();c.dll.retro_deinit()
checks={};details={}
# Revert only the enemy counter to reproduce its original failure, in scratch only.
b=bytearray(ROM.read_bytes());assert b[0x101f4:0x101f6]==bytes.fromhex('760e')
b[0x101f4:0x101f6]=bytes.fromhex('7610')
struct.pack_into('>H',b,0x18e,sum(struct.unpack('>'+str((len(b)-512)//2)+'H',b[512:]))&0xffff)
checks['regression_restores_original_wrong_counter']=b[0x101f4:0x101f6]==bytes.fromhex('7610')
with tempfile.TemporaryDirectory(prefix='beyond-oasis-regression-') as temp:
 broken=Path(temp)/'broken.bin';broken.write_bytes(b)
 c=Core(broken);c.capture=False;c.load('test-combat')
 checks['fixture_contains_first_miniboss']=word(c.ram(),0x1cd8)==0x22
 put(c,0x1d5e,0x7fff);c.run(240)
 checkpoint=c.state();before=snapshot(c);advance_dialogue(c);old=snapshot(c)
 checks['unfixed_counter_softlock_reproduced']=old['room']==before['room'] and old['script']=='0x4382e' and old['active_enemy_slots']==0 and old['p2_type']==2 and old['story_lock']!=0
 details['old_release_after_dialogue']=old;close(c)
 # The exact same blocked state must resume without restarting the campaign.
 c=Core(ROM);c.capture=False;c.restore(checkpoint);advance_dialogue(c);fixed=snapshot(c)
 checks['same_state_reaches_next_story_room']=fixed['room']=='0x2e3a8' and fixed['room']!=before['room']
 checks['next_story_script_runs']=fixed['script']=='0x46218'
 checks['story_releases_player_controls']=fixed['story_lock']==0
 checks['p2_remains_alive_and_invulnerable']=fixed['p2_type']==2 and fixed['p2_health']==200 and fixed['p2_death_timer']==0
 details['fixed_release_after_dialogue']=fixed
 x=word(c.ram(),0x19f0);c.run(20,[7]);checks['p1_can_move_after_scene']=word(c.ram(),0x19f0)>x
 c.capture=True;c.run(1);Image.fromarray(c.picture).resize((640,448),Image.Resampling.NEAREST).save(ROOT.parent/'story-preview.png')
 saved=c.state();c.run(60);expected=c.state();c.restore(saved);c.run(60)
 checks['resumed_scene_save_restore_deterministic']=c.state()==expected
 close(c)
 # Also exercise the candidate normally from the pre-kill combat fixture.
 c=Core(ROM);c.capture=False;c.load('test-combat');put(c,0x1d5e,0x7fff);c.run(240);advance_dialogue(c)
 fresh=snapshot(c);checks['fresh_boss_defeat_also_advances']=fresh['room']=='0x2e3a8' and fresh['story_lock']==0 and fresh['p2_type']==2
 close(c)
result={'checks':checks,'details':details,'all_passed':all(checks.values()),'rom_sha256':hashlib.sha256(ROM.read_bytes()).hexdigest()}
(ROOT/'story-regression.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));assert result['all_passed']
