"""Runtime acceptance for title caption and P2 invulnerability."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from PIL import Image
from probe import Core,ROOT
from verify import ROM,word,put,byte
checks={};details={}
off=16+65536+8192+1+4+16+1024
c=Core(ROM);c.run(1000);c.run(8,[3]);c.run(150)
caption=c.picture.copy();s=c.state()
vram=np.frombuffer(s[off:off+65536],dtype='<u2')
expected=[0x61c1+0x5c0+ord(x)-32 for x in 'Coop version']
checks['title_uses_original_font_and_palette']=vram[0xc91c//2:0xc91c//2+12].tolist()==expected
c.run(240);vram2=np.frombuffer(c.state()[off:off+65536],dtype='<u2')
checks['caption_persists_while_start_prompt_blinks']=vram2[0xc91c//2:0xc91c//2+12].tolist()==expected
Image.fromarray(caption).resize((640,448),Image.Resampling.NEAREST).save(ROOT.parent/'title-preview.png')
c.dll.retro_unload_game();c.dll.retro_deinit()
# Pixel comparison with the preceding build proves only the caption is added.
baseline=ROOT.parent.parent/'BeyondOasisCoop-DarkP2/generated/Beyond Oasis Coop Dark P2.bin'
if baseline.exists():
 c=Core(baseline);c.run(1000);c.run(8,[3]);c.run(150)
 diff=np.any(c.picture!=caption,axis=2);ys,xs=np.where(diff)
 checks['title_pixels_only_change_inside_caption']=len(xs)>0 and xs.min()>=112 and xs.max()<208 and ys.min()>=144 and ys.max()<152
 details['title_changed_pixel_bounds']=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())]
 c.dll.retro_unload_game();c.dll.retro_deinit()
c=Core(ROM);c.capture=False;c.load('test-beach');base=c.state()
checks['all_pending_damage_modes_ignored']=True
for damage in [1,8,0xfff,0x1fff,0x4001,0x8001,0xc001,0x7fff,0xffff]:
 c.restore(base);hp1=word(c.ram(),0x1a72);hp2=word(c.ram(),0x2922)
 put(c,0x291e,damage);c.run(12)
 b=c.ram()
 checks['all_pending_damage_modes_ignored'] &= word(b,0x2898)==2 and word(b,0x2922)==hp2 and word(b,0x1a72)==hp1 and word(b,0x2894)==0
# P1's lethal damage and original death processing still work.
c.restore(base);put(c,0x1a72,1);put(c,0x1a6e,0x7fff);c.run(8)
checks['p1_can_still_die']=word(c.ram(),0x1a72)==0 and c.ram()[0x1987]!=0
checks['p1_death_does_not_kill_p2']=word(c.ram(),0x2898)==2 and word(c.ram(),0x2922)>0
# No P2 HUD tiles occur in the live sprite table.
c.restore(base);c.capture=True;put(c,0x28a0,300);c.run(30)
b=c.ram();count=word(b,0x188a);tiles=[word(b,0x13cc+i*8+4)&0x7ff for i in range(count)]
checks['no_p2_health_bar_or_label']=not any(t in range(0x57c,0x580) for t in tiles)
Image.fromarray(c.picture).resize((640,448),Image.Resampling.NEAREST).save(ROOT.parent/'preview.png')
# Repeated heavy damage for 30 seconds; P2 remains controllable throughout.
c.capture=False;c.restore(base);startx=word(c.ram(),0x28a0);alive=True
for frame in range(1800):
 put(c,0x291e,0xffff);c.run(1,(),[7] if frame<20 else ())
 b=c.ram();alive &= word(b,0x2898)==2 and word(b,0x2922)==200
 if frame==19:checks['p2_hit_reaction_interrupts_movement']=word(b,0x289c) in (0x18,0x1a,0x20)
checks['p2_survives_repeated_lethal_damage_30_seconds']=alive
checks={k:bool(v) for k,v in checks.items()}
result={'checks':checks,'details':details,'all_passed':all(checks.values()),'rom_sha256':hashlib.sha256(ROM.read_bytes()).hexdigest()}
(ROOT/'features.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));assert result['all_passed']

