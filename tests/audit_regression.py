"""Isolated 68000 routine fixtures. Scratch ROMs are private and undistributed.
These establish code behavior, not a claim of encountering every case in play.
"""
from pathlib import Path
import argparse,sys,json,hashlib,subprocess,ctypes as C,struct
ROOT=Path(__file__).resolve().parent;WS=ROOT.parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--rom',type=Path,default=ROOT.parent/'generated/Beyond Oasis Coop.bin');parser.add_argument('--assembler',type=Path,default=WS/'work/vasmm68k_mot.exe');args=parser.parse_args()
sys.path.insert(0,str(ROOT))
from probe import Core
from verify import put,byte,word
rom=args.rom.read_bytes();state=(WS/'work/damage-investigation/user.state').read_bytes();private=WS/'work/coop-audit-fixtures';private.mkdir(exist_ok=True)
def close(c):c.dll.retro_unload_game();c.dll.retro_deinit()
def fixture(name,asm,setup):
 code='        org $30f000\n        ori.w #$700,sr\n        clr.w $ff0f10\n'+asm+'\nfreeze: ori.w #$700,sr\n        move.w #$beef,$ff0f10\n        bra.s freeze\n'
 source=private/(name+'.asm');payload=private/(name+'.bin');source.write_text(code)
 subprocess.run([str(args.assembler),'-Fbin','-m68000','-o',str(payload),str(source)],check=True,stdout=subprocess.DEVNULL)
 b=bytearray(rom);b[0x8b2a:0x8b30]=bytes.fromhex('4eb90030f000');p=payload.read_bytes();b[0x30f000:0x30f000+len(p)]=p
 # The controlled same-frame ordering must not let VBlank consume the first
 # queued transfer. Preserve the fixture's interrupt mask at the loader exit.
 # Only scratch ROMs are changed; this is a scheduling-risk fixture.
 if name.startswith('shared-buffer'):b[0x1457e:0x14580]=bytes.fromhex('ffff')
 struct.pack_into('>H',b,0x18e,sum(struct.unpack('>'+str((len(b)-512)//2)+'H',b[512:]))&0xffff)
 path=private/(name+'-fixture-rom.bin');path.write_bytes(b);c=Core(path);c.capture=False;c.restore(state);setup(c);c.run(300 if name.startswith('shared-buffer') else 2);return c
def fill_large(c):
 for i in range(3,19):put(c,0x19e8+i*188,0x16)
 put(c,0x27dc,0);put(c,0x2898,2)
checks={};details={}
for routine in [0xda1a,0xda2a,0xda62,0xda72]:
 c=fixture(f'allocator-{routine:x}',f'''        lea $ff1c1c,a6
        moveq #15,d0
fill_reserved_test:
        move.w #$16,(a6)
        adda.w #188,a6
        dbra d0,fill_reserved_test
        clr.w $ff27dc
        move.w #2,$ff2898
        jsr ${routine:x}
        move.w sr,d1
        move.l a6,$ff0f00
        move.w d0,$ff0f04
        move.w d1,$ff0f06''',fill_large)
 b=c.ram();result={'routine':f'{routine:06X}','returned_actor':f'{int.from_bytes(b[0xf00:0xf04],"big")&0xffffff:06X}','carry':bool(word(b,0xf06)&1)};details[f'allocator_{routine:x}']=result;close(c)
checks['da1a_excludes_META_even_when_marker_zero']=details['allocator_da1a']['carry']
checks['other_three_allocators_exclude_reserved_slots']=all(details[f'allocator_{a:x}']['carry'] for a in [0xda2a,0xda62,0xda72])
def fill_small(c):
 for i in range(2):put(c,0x2abc+i*90,8)
 for i in range(2,8):put(c,0x2abc+i*90,0)
c=fixture('small-allocator','''        jsr $d9be
        move.l a6,$ff0f00
        move.w d0,$ff0f04''',fill_small)
b=c.ram();tile=word(b,0xf04);details['small_allocator']={'returned_actor':f'{int.from_bytes(b[0xf00:0xf04],"big")&0xffffff:06X}','tile':f'{tile:04X}','start':f'{tile*32:04X}','end_exclusive':f'{(tile+9)*32:04X}'}
checks['small_allocator_does_not_overlap_P2_body_or_weapon']=not(max(tile*32,0xb800)<min((tile+9)*32,0xc000)) and not(max(tile*32,0xdc20)<min((tile+9)*32,0xde20));close(c)
def init_actor(c,base,typ):
 t=rom[0x3f2fa+typ*16-32:][:32];a=bytearray(188);a[:2]=typ.to_bytes(2,'big');a[0x4a:0x4c]=t[:2]
 for off in [0x42,0x44,0x46]:a[off:off+2]=bytes([0,t[2]])
 for off,idx in [(0x48,3),(0x49,4),(0x3d,5),(0x3a,7),(0x36,8),(0x37,9),(0x38,10),(0x3c,11)]:a[off]=t[idx]
 a[0x4c:0x4e]=bytes([0,t[6]])
 for off,idx in [(0x1a,12),(0x1e,16),(0x26,20),(0x22,24),(0x5e,28)]:a[off:off+4]=t[idx:idx+4]
 for off in [0x2c,0x34,0x5c]:a[off:off+2]=b'\xff\xff'
 a=b''.join(a[i:i+2][::-1] for i in range(0,len(a),2));C.memmove(c.dll.retro_get_memory_data(2)+base,a,len(a))
def attack_setup(c,drain=False):
 init_actor(c,0x1cd8,0x36 if drain else 0x26)
 for a,x,y in [(0x19e8,250,160),(0x2898,168,224),(0x1cd8,168,224)]:
  put(c,a+8,x);put(c,a+12,y);put(c,a+16,0);put(c,a+18,0);put(c,a+20,0)
  byte(c,a+0x38,0);byte(c,a+0x39,0);put(c,a+0x86,0);put(c,a+0x4a,0x28)
 for a in [0x1987,0x1989,0x198b]:byte(c,a,0)
 put(c,0x1cdc,8 if drain else 2);put(c,0x1d08,0);put(c,0x1cda,1)
 put(c,0x1d68,4);put(c,0x1d76,12);put(c,0x1d78,0)
 put(c,0x1d80,0);put(c,0x1d82,0)
 for a in [0x1a70,0x1a72]:put(c,a,196)
 put(c,0x2920,200);put(c,0x2922,200)
for name,routine,drain in [('direct-special-attack',0x23b02,False),('health-drain',0x1c772,True)]:
 c=fixture(name,f'''        lea $ff1cd8,a6
        lea ${routine:x},a0
        jsr $300010''',lambda c:attack_setup(c,drain))
 b=c.ram();details[name]={'p1_hp':word(b,0x1a72),'p2_hp':word(b,0x2922),'p1_pending':f'{word(b,0x1a6e):04X}','p2_pending':f'{word(b,0x291e):04X}','p1_x':word(b,0x19f0),'p2_x':word(b,0x28a0),'enemy_state':word(b,0x1cdc)};close(c)
checks['special_attack_selected_P2_writes_only_P2']=details['direct-special-attack']['p1_pending']=='0000' and details['direct-special-attack']['p2_pending']=='A032'
checks['native_drain_selected_P2_preserves_both_HP']=details['health-drain']['p1_hp']==196 and details['health-drain']['p2_hp']==200

def boss_drain_setup(c):
 attack_setup(c)
 put(c,0x1cd8+0x30,0);put(c,0x1cd8+0x2e,0)
c=fixture('boss-drain','''        lea $ff1cd8,a6
        lea $1ab6a,a0
        jsr $300010''',boss_drain_setup)
b=c.ram();details['boss-drain']={'p1_hp':word(b,0x1a72),'p2_hp':word(b,0x2922),'p1_pending':f'{word(b,0x1a6e):04X}','p2_pending':f'{word(b,0x291e):04X}','fixture_completed':word(b,0xf10)==0xbeef,'scope':'Direct invocation of native phase handler 1AB6A, with controlled animation timer and frame offset. Not a natural boss encounter.'};close(c)
checks['boss_drain_selected_P2_preserves_both_HP']=details['boss-drain']['p1_hp']==196 and details['boss-drain']['p2_hp']==200 and details['boss-drain']['fixture_completed']
def queue_setup(c):
 for a in range(0x10b4,0x13cc,2):put(c,a,0)
 put(c,0x1892,0xff);put(c,0x1894,0x10b4);byte(c,0x27fa,255)
samples={}
for both in [False,True]:
 extra='        move.b #$ff,$ff27fa\n        jsr $300018\n' if both else ''
 c=fixture('shared-buffer-'+str(both),'''        move.l #$ff10b4,$ff1892
        clr.b $ff27fa
        jsr original_graphics
'''+extra+'''        bra.s freeze
original_graphics:
        movem.l d0/a0-a1,-(sp)
        jmp $1454c''',queue_setup)
 b=c.ram();q=int.from_bytes(b[0x1892:0x1896],'big')&0xffff
 samples[str(both)]={'buffer':b[0x2fa8:0x3948],'queue':b[0x10b4:q].hex(),'queue_end':q,'fixture_completed':word(b,0xf10)==0xbeef,'pc':None};close(c)
before=samples['False']['buffer'];after=samples['True']['buffer'];different=sum(a!=b for a,b in zip(before,after))
checks['effect_restore_uses_ROM_and_preserves_pending_RAM_data']=different==0 and '007f97d4f50004d0' in samples['True']['queue'] and '001af880a9000780' in samples['True']['queue']
details['shared_decompress_buffer']={'different_bytes':different,'original_buffer_sha256':hashlib.sha256(before).hexdigest(),'after_effect_restore_sha256':hashlib.sha256(after).hexdigest(),'original_queue':samples['False']['queue'],'combined_queue':samples['True']['queue'],'completion':{k:{n:v[n] for n in ['fixture_completed','pc']} for k,v in samples.items()},'scope':'Controlled same-frame scheduling: scratch ROM changes the immediate at 1457E from F9FF to FFFF, retaining the interrupt mask so VBlank cannot consume the first transfer. Both native routines finish. Natural campaign coincidence is not established.'}

for slot in range(8):
 def setup_slot(c,slot=slot):
  for i in range(8):put(c,0x2abc+i*90,8 if i<slot else 0)
 asm='\n'.join(f'        move.w #{8 if i<slot else 0},${0xff2abc+i*90:x}' for i in range(8))+'\n        jsr $d9be\n        move.w d0,$ff0f04'
 c=fixture('small-slot-'+str(slot),asm,lambda c:None)
 tile=word(c.ram(),0xf04);close(c)
 checks['small_slot_'+str(slot)+'_keeps_original_bank']=tile==0x694+9*slot
for name,routine,drain in [('direct-special-attack',0x23b02,False),('health-drain',0x1c772,True),('boss-drain',0x1ab6a,False)]:
 def setup_p1(c,drain=drain,name=name):
  attack_setup(c,drain)
  put(c,0x19f0,168);put(c,0x19f4,224);put(c,0x28a0,250);put(c,0x28a4,160)
  if name=='boss-drain':put(c,0x1cd8+0x30,0);put(c,0x1cd8+0x2e,0)
 asm=f'        lea $ff1cd8,a6\n        lea ${routine:x},a0\n        jsr $300010'
 c=fixture('p1-'+name,asm,setup_p1);b=c.ram();close(c)
 details['p1-'+name]={'p1_hp':word(b,0x1a72),'p2_hp':word(b,0x2922),'p1_pending':f'{word(b,0x1a6e):04X}','p2_pending':f'{word(b,0x291e):04X}'}
 checks['p1_'+name+'_retains_original_damage']=(word(b,0x1a6e)==0xa032 if name=='direct-special-attack' else word(b,0x1a72)==(192 if drain else 188)) and word(b,0x2922)==200


# Capture ownership remains stable when the other player moves closer.
for selected_p2 in [False,True]:
 def capture_setup(c,selected_p2=selected_p2):
  attack_setup(c)
  byte(c,0x2898+0xa1,int(selected_p2))
  for off in [0x20,0x24]:
   put(c,0x27dc+off,0);put(c,0x27dc+off+2,0)
  put(c,0x19f0,168 if selected_p2 else 250)
  put(c,0x19f4,224 if selected_p2 else 160)
  put(c,0x28a0,250 if selected_p2 else 168)
  put(c,0x28a4,160 if selected_p2 else 224)
 asm='        lea $ff1cd8,a6\n        jsr $30095c\n        lea harmless,a0\n        jsr $300010\n        move.l $ff27fc,$ff0f14\n        move.l $ff2800,$ff0f18\n        jsr $3009c0\n        bra.w freeze\nharmless: move.b $ff2939,$ff0f12\n        rts'
 c=fixture('capture-owner-'+str(selected_p2),asm,capture_setup);b=c.ram();close(c)
 checks['capture_owner_stable_'+str(selected_p2)]=bool(b[0xf12]&1)==selected_p2 and int.from_bytes(b[0xf14:0xf18],'big')==(0 if selected_p2 else 16) and int.from_bytes(b[0xf18:0xf1c],'big')==(16 if selected_p2 else 0) and b[0x27fc:0x2804]==bytes(8)

c=Core(args.rom);c.restore(state);c.run(2)
for off in [0x20,0x22,0x24,0x26]:put(c,0x27dc+off,0xffff)
put(c,0x27dc+0xb4,word(c.ram(),0x16ec)^0xffff)
c.run(2);details['room_spawn_masks']={'masks':c.ram()[0x27fc:0x2804].hex(),'marker':c.ram()[0x27dc:0x27e0].hex(),'room':c.ram()[0x16ec:0x16f0].hex(),'saved_room':c.ram()[0x2890:0x2894].hex()};checks['room_spawn_clears_capture_ownership']=c.ram()[0x27fc:0x2804]==bytes(8);close(c)

report={'rom_sha256':hashlib.sha256(rom).hexdigest(),'checks':checks,'details':details,'scope':'Audit fixtures deliberately set actor phase/pool occupancy; no distributed ROM changes. True checks mean the audited regression passed; controlled fixtures do not establish full campaign coverage.'}
(ROOT/'audit-regression.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

assert all(checks.values()),checks
