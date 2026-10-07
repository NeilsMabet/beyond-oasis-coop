"""Native spirit-target fixtures plus ordinary frame updates of summoned spirits.
Scratch ROMs and gameplay states are private and are never release assets.
"""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess
from probe import Core,ROOT
from verify import word,put,byte
W=ROOT.parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--rom',type=Path,default=ROOT.parent/'generated/Beyond Oasis Coop.bin');parser.add_argument('--baseline-rom',type=Path,required=True);parser.add_argument('--state',type=Path,default=ROOT/'test-beach.state');parser.add_argument('--assembler',type=Path,default=W/'work/vasmm68k_mot.exe');args=parser.parse_args()
private=W/'work/spirit-regression';private.mkdir(exist_ok=True)
state=args.state.read_bytes();original=args.baseline_rom.read_bytes();fixed=args.rom.read_bytes();checks={};details={}
SPIRITS={0x18:'Dytto',0x1a:'Efreet',0x1c:'Shade',0x1e:'Bow'}
def close(c):c.dll.retro_unload_game();c.dll.retro_deinit()
def scratch(rom,name,asm,freeze=True,extra=None):
 code='        org $30f000\n'+('        ori.w #$700,sr\n' if freeze else '')+asm
 if freeze:code+='\nfreeze: move.w #$beef,$ff0f10\n        bra.s freeze\n'
 src=private/(name+'.asm');binary=private/(name+'.bin');src.write_text(code)
 subprocess.run([str(args.assembler),'-Fbin','-m68000','-o',str(binary),str(src)],check=True,stdout=subprocess.DEVNULL)
 b=bytearray(rom);b[0x8b2a:0x8b30]=bytes.fromhex('4eb90030f000');data=binary.read_bytes();assert len(data)<0x400;b[0x30f000:0x30f000+len(data)]=data
 if extra:
  for at,data in extra.items():b[at:at+len(data)]=data
 struct.pack_into('>H',b,0x18e,sum(struct.unpack('>'+str((len(b)-512)//2)+'H',b[512:]))&0xffff)
 path=private/(name+'.bin');path.write_bytes(b);c=Core(path);c.capture=False;c.restore(state);put(c,0xf10,0);return c
# Setup is executed inside the fixture, after native object processing reaches
# the frame hook. Earlier object scans cannot consume partially initialized data.
def setup(typ,target=0x2898,enemy=False):
 clear='\n'.join(f'        clr.w ${0xff19e8+i*188:x}' for i in range(1,20))
 return clear+f"""
        move.w #${typ:x},$ff1aa4
        lea $ff1aa4,a6
        jsr $8d06
        move.w #160,8(a6)
        move.w #176,$c(a6)
        clr.l $10(a6)
        clr.w $16(a6)
        move.w #2,${0xff0000+target:x}
        move.w #160,${0xff0000+target+8:x}
        move.w #176,${0xff0000+target+12:x}
        clr.l ${0xff0000+target+16:x}
        clr.w ${0xff0000+target+20:x}
        move.w #24,${0xff0000+target+0x42:x}
        move.w #24,${0xff0000+target+0x44:x}
        move.w #128,${0xff0000+target+0x4a:x}
        clr.b ${0xff0000+target+0x38:x}
        clr.b ${0xff0000+target+0x3a:x}
        clr.b ${0xff0000+target+0x82:x}
        clr.b ${0xff0000+target+0x6d:x}
        clr.w ${0xff0000+target+0x86:x}
        move.w #2,$ff2898
"""
def execute(rom,name,asm,extra=None):
 c=scratch(rom,name,asm,extra=extra);c.run(2);b=c.ram();close(c);assert word(b,0xf10)==0xbeef,name;return b
# The native acquisition helpers use 4 directional six-word boxes.
wide=struct.pack('>6h',-64,127,-96,-96,96,96)*4
for typ,label in SPIRITS.items():
 for routine in [0xbab8,0xbba8]:
  for enemy in [False,True]:
   target=0x2720 if enemy else 0x2898
   asm=setup(typ,target)+f'        lea $30f500,a1\n        jsr ${routine:x}\n        move.w sr,$ff0f02\n        move.l a0,$ff0f04'
   b=execute(fixed,f'acquire-{typ:x}-{routine:x}-{enemy}',asm,{0x30f500:wide});found=bool(word(b,0xf02)&1);actor=int.from_bytes(b[0xf04:0xf08],'big')&0xffffff
   checks[f'{label}_{routine:x}_'+('keeps_last_enemy_slot' if enemy else 'does_not_select_P2')]=found and actor==0xff2720 if enemy else not found
# Compare a concrete original acquisition failure, not merely new green checks.
b=execute(original,'old-acquire-P2',setup(0x1a)+'        lea $30f500,a1\n        jsr $bab8\n        move.w sr,$ff0f02\n        move.l a0,$ff0f04',{0x30f500:wide})
checks['old_Efreet_acquisition_of_P2_reproduced']=bool(word(b,0xf02)&1) and int.from_bytes(b[0xf04:0xf08],'big')==0xff2898
# B922 and B856 return a candidate without applying damage; exclusion must
# happen before Dytto freeze and Efreet's direct knockback/damage writers.
box="""
        moveq #-24,d1
        moveq #-24,d2
        moveq #24,d3
        moveq #24,d4
        moveq #0,d5
        moveq #24,d6
"""
for typ,label in {**SPIRITS,0x20:'bomb'}.items():
 for routine in [0xb922,0xb856]:
  asm=setup(typ)+box+('        moveq #-16,d0\n' if routine==0xb922 else '        move.l #$100000,d0\n')+f'        jsr ${routine:x}\n        move.w sr,$ff0f02\n        move.l a0,$ff0f04'
  b=execute(fixed,f'mask-{typ:x}-{routine:x}',asm);hit=not bool(word(b,0xf02)&1);actor=int.from_bytes(b[0xf04:0xf08],'big')&0xffffff
  checks[f'{label}_{routine:x}_'+('hazard_still_selects_P2' if typ==0x20 else 'excludes_P2_before_effects')]=hit and actor==0xff2898 if typ==0x20 else not hit
  if typ!=0x20:
   asm=setup(typ,0x2720)+box+('        moveq #-16,d0\n' if routine==0xb922 else '        move.l #$40000,d0\n')+f'        jsr ${routine:x}\n        move.w sr,$ff0f02\n        move.l a0,$ff0f04'
   b=execute(fixed,f'mask-enemy-{typ:x}-{routine:x}',asm);checks[f'{label}_{routine:x}_keeps_enemy_candidate']=not bool(word(b,0xf02)&1) and int.from_bytes(b[0xf04:0xf08],'big')==0xff2720
# Native melee attack tables: use the first actual attack frame for each
# offensive spirit and overlapping target hitboxes, with no synthetic damage table.
for typ in [0x18,0x1a,0x1e]:
 table=int.from_bytes(original[0x3f2fa+typ*16-32+24:0x3f2fa+typ*16-32+28],'big');row=table+int.from_bytes(original[table:table+2],'big');frame=int.from_bytes(original[row:row+2],'big')
 for routine in [0xbca4,0xbcba]:
  for target in [0x2898,0x2720]:
   asm=setup(typ,target)+f'        move.w #{frame},$32(a6)\n        moveq #0,d0\n        jsr ${routine:x}'
   b=execute(fixed,f'melee-{typ:x}-{routine:x}-{target:x}',asm)
   checks[f'{SPIRITS[typ]}_{routine:x}_melee_'+('spares_P2' if target==0x2898 else 'still_hits_enemy')]=word(b,target+0x86)==0 if target==0x2898 else word(b,target+0x86)!=0
# Spirit follow/command ownership stays with P1 even when P2 is nearer.
for typ,label in SPIRITS.items():
 asm=setup(typ)+"""
        move.w #300,$ff19f0
        move.w #120,$ff19f4
        move.w #160,$ff28a0
        move.w #176,$ff28a4
        lea observe_owner,a0
        jsr $300010
        bra.w freeze
observe_owner:
        move.w $ff19f0,$ff0f20
        move.w $ff19f4,$ff0f22
        rts
"""
 b=execute(fixed,f'owner-{typ:x}',asm)
 checks[label+'_retains_P1_owner_view']=word(b,0xf20)==300 and word(b,0xf22)==120

# Run the native summoned AI through normal frame processing. Only spawning and
# initial positions are controlled; original animation, AI and collisions run.
def live(rom,typ,frames=600):
 init={0x18:0x14668,0x1a:0x146d6,0x1c:0x14742,0x1e:0x147e0}[typ]
 asm=f"""
        movem.l d0-d7/a0-a6,-(sp)
        cmpi.w #$beef,$ff0f10
        beq.w ready
        move.w #$beef,$ff0f10
        lea $ff1aa4,a6
        move.l #$00a00000,d0
        move.l #$00b00000,d1
        moveq #0,d2
        moveq #0,d3
        jsr ${init:x}
        move.w #200,$ff1a76
        move.w #180,$ff28a0
        move.w #176,$ff28a4
        clr.l $ff28a8
        clr.l $ff28ac
        clr.w $ff289c
        move.w #$ffff,$ff28cc
ready:
        movem.l (sp)+,d0-d7/a0-a6
        jsr $300000
        rts
"""
 c=scratch(rom,('old' if rom==original else 'fixed')+f'-live-{typ:x}',asm,freeze=False);byte(c,0x19a2,0);byte(c,0x19a7,0);hits=[];seen=set();alive=True
 for t in range(frames):
  c.run(1);b=c.ram();seen.add(word(b,0x1aa4));alive &= word(b,0x2898)==2
  source=int.from_bytes(b[0x2916:0x291a],'big')&0xffffff
  if source==0xff1aa4 and (word(b,0x289c) in [0x18,0x1a,0x20] or b[0x28d1]&8 or word(b,0x291e)):
   hits.append(t)
 saved=c.state();c.run(90,(),[7]);expected=c.state();c.restore(saved);c.run(90,(),[7]);deterministic=c.state()==expected
 close(c);return {'hit_frames':hits,'types_seen':sorted(seen),'p2_alive':bool(alive),'rollback_equal':deterministic}
old=live(original,0x1a);details['old_Efreet']=old;checks['old_native_Efreet_AI_hits_and_burns_P2']=bool(old['hit_frames'])
for typ,label in SPIRITS.items():
 result=live(fixed,typ);details[label]=result;checks[label+'_native_AI_no_hits_on_P2']=not result['hit_frames'] and typ in result['types_seen'] and result['p2_alive'];checks[label+'_native_AI_rollback_equal']=result['rollback_equal']
report={'rom_sha256':hashlib.sha256(fixed).hexdigest(),'baseline_sha256':hashlib.sha256(original).hexdigest(),'checks':{k:bool(v) for k,v in checks.items()},'details':details,'scope':'Native acquisition/collision/attack fixtures plus 600 ordinary frames per natively spawned spirit on the beach. Not full campaign or every special ability.'}
(ROOT/'spirit-regression.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));assert all(checks.values()),[k for k,v in checks.items() if not v]
