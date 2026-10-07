"""Headless behavioral checks against the real ROM and official libretro core."""
import ctypes as C, hashlib, json, pathlib, time
from probe import Core, ROOT
ROM=ROOT.parent/'generated/Beyond Oasis Coop.bin'
def word(b,off):return int.from_bytes(b[off:off+2],'big')
def put(c,off,value):C.memmove(c.dll.retro_get_memory_data(2)+off,value.to_bytes(2,'little'),2)
def byte(c,off,value):C.memmove(c.dll.retro_get_memory_data(2)+(off^1),bytes([value]),1)
def equip_sword(c,units):
    put(c,0xd80,0x200+units);byte(c,0xdb0,0);byte(c,0xdb1,2)
    put(c,0xd7e,0xc);put(c,0x19ee,0xc);byte(c,0x198f,0xff);c.run(2)
def target_fixture(c,combat):
    c.restore(combat)
    # Hold one real guard in place for repeatable melee/resource checks. The
    # independent AI/damage test above runs with ordinary enemy updates enabled.
    byte(c,0x17b8,c.ram()[0x17b8]|2)
    put(c,0x1d9c,240);put(c,0x1da0,160);put(c,0x1da8,0);put(c,0x1e1e,100)
    byte(c,0x1d94+0x38,c.ram()[0x1d94+0x38]&0xf3);byte(c,0x1d94+0x6d,0)
    byte(c,0x1d94+0x82,0);byte(c,0x1d94+0x9d,0);put(c,0x1d94+0x86,0)
    put(c,0x28a0,220);put(c,0x28a4,160);put(c,0x28ac,0);put(c,0x28a8,0);put(c,0x28aa,0)
    put(c,0x289c,0);put(c,0x28c2,0);put(c,0x28ae,1);byte(c,0x291a,0);byte(c,0x2935,0)
def boot(c):
    c.capture=False
    c.run(1000)
    for buttons,wait in [([3],300),([3],180),([0],180),([3],60),([3],60),([0],4800)]:
        c.run(8,buttons);c.run(wait)
    assert word(c.ram(),0x19e8)==2 and word(c.ram(),0x19f0)>0,'Cold boot did not reach gameplay'
    c.save('test-beach')
def main():
    c=Core(ROM);boot(c)
    checks={}
    checks['cold_boot_checksum']=True
    s=c.state();b=c.ram();c.run(20,(),[7]);a=c.ram()
    checks['independent_movement']=a[0x19f0:0x19f8]==b[0x19f0:0x19f8] and word(a,0x28a0)>word(b,0x28a0)
    c.restore(s);c.run(8,(),[8]);c.run(20);b=c.ram()
    checks['independent_jump']=int.from_bytes(b[0x28a8:0x28ac],'big')>0 and int.from_bytes(b[0x19f8:0x19fc],'big')==0
    c.restore(s);c.run(8,(),[0]);b=c.ram()
    checks['independent_attack']=word(b,0x289c)!=word(b,0x19ec)
    c.restore(s);put(c,0x28a0,500);c.run(8)
    checks['catch_up']=abs(word(c.ram(),0x28a0)-word(c.ram(),0x19f0))<40
    c.restore(s);c.run(100,[4]);c.run(240)
    checks['room_transition']=word(c.ram(),0x2898)==2 and word(c.ram(),0x2922)==word(c.ram(),0x2920)
    c.save('test-village')
    c.run(120,[4]);c.run(30,[7]);c.run(150,[4]);c.run(600)
    assert word(c.ram(),0x1cd8)>2,'Battle fixture did not spawn'
    checks['intro_script_progress']=c.ram()[0x1983]==0
    put(c,0x19f0,200);put(c,0x19f4,220);put(c,0x19fc,0);c.run(90)
    put(c,0x28a0,256);put(c,0x28a4,160);put(c,0x28ac,0)
    initial=c.ram();c.run(300);b=c.ram()
    checks['p2_immune_to_enemy_damage']=word(b,0x2922)==word(initial,0x2922) and word(b,0x2898)==2
    c.save('test-combat');combat=c.state()
    target_fixture(c,combat);health_before=word(c.ram(),0x1e1e)
    c.run(8,(),[0]);c.run(25);byte(c,0x17b8,c.ram()[0x17b8]&0xfd);c.run(30)
    checks['p2_damages_enemy']=word(c.ram(),0x1e1e)<health_before
    c.restore(combat);put(c,0x291e,0x7fff);c.run(8)
    checks['p2_immune_to_lethal_pending_damage']=word(c.ram(),0x2898)==2 and word(c.ram(),0x2922)==word(c.ram(),0x2920)
    put(c,0x2890,0);c.run(8)
    checks['room_transition_keeps_p2_alive']=word(c.ram(),0x2898)==2
    c.run(1900)
    checks['p2_has_no_death_timer']=word(c.ram(),0x2894)==0 and word(c.ram(),0x2898)==2
    c.restore(combat);s=c.state();c.run(90,(),[0]);a=c.state();c.restore(s);c.run(90,(),[0]);b=c.state()
    checks['serialize_restore_determinism']=a==b
    c.load('test-beach');s=c.state();put(c,0x28a0,word(c.ram(),0x19f0));put(c,0x28a4,word(c.ram(),0x19f4));start=c.ram()
    for _ in range(25):c.run(8,[0],[0]);c.run(12)
    b=c.ram();checks['direct_friendly_fire_disabled']=word(b,0x1a72)==word(start,0x1a72) and word(b,0x2922)==word(start,0x2922)
    target_fixture(c,combat);equip_sword(c,2)
    checks['p2_weapon_switch']=word(c.ram(),0x289e)==0xc
    c.run(8,(),[0]);c.run(25)
    checks['p2_shared_sword_wear']=word(c.ram(),0xd80)==0x201
    for _ in range(6):
        byte(c,0x1d94+0x82,0);byte(c,0x1d94+0x9d,0);put(c,0x1d94+0x86,0)
        c.run(8,(),[0]);c.run(25)
    b=c.ram();checks['broken_weapon_reloads_both']=word(b,0xd80)==0 and word(b,0x19ee)==0xa and word(b,0x289e)==0xa
    target_fixture(c,combat);equip_sword(c,1)
    for _ in range(7):c.run(8,[0],[0]);c.run(25)
    b=c.ram();checks['last_sword_unit_no_underflow']=word(b,0xd80)==0 and word(b,0x19ee)==0xa and word(b,0x289e)==0xa
    c.capture=True;c.load('test-combat');c.run(1);c.save('verified-combat')
    result={'checks':checks,'all_passed':all(checks.values()),'rom_sha256':hashlib.sha256(ROM.read_bytes()).hexdigest(),'state_sha256':hashlib.sha256(a).hexdigest()}
    (ROOT/'checks.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2),flush=True)
    assert result['all_passed']
if __name__=='__main__':main()
