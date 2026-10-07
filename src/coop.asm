        org $300000
; Experimental single-room hook. P2 uses the last $BC-byte actor slot.
P1      equ $ff19e8
P2      equ $ff2898
META    equ $ff27dc
        bra.w update
        bra.w read_pads
        bra.w enemy_hit
        bra.w filter_hit
        bra.w enemy_update
        bra.w hero_check
        bra.w draw_hud
        bra.w pickup_owner
        bra.w interaction_owner
        bra.w projectile_target
        bra.w menu_return
        bra.w title_caption
        bra.w damage_gate
        bra.w preserve_p2_health
        bra.w thrown_hero_target
        bra.w collision_entry
        bra.w projectile_collision
        bra.w body_collision
        bra.w fire_immunity
        bra.w render_actor
update:
        move.w P2,-(sp)
        move.w META,-(sp)
        clr.w P2
        clr.w META
        jsr $f788
        move.w (sp)+,META
        move.w (sp)+,P2
        jsr $557a
        movem.l d0-d7/a0-a6,-(sp)
        lea META,a5
        lea P2,a6
        cmpi.w #$5032,2(a5)
        bne.w spawn
        move.l $ff16ec,d0
        cmp.l $b4(a5),d0
        beq.w initialized
        bra.w spawn
spawn:
        move.w #$fffe,(a5)
        move.w #$5032,2(a5)
        move.l $ff16ec,$b4(a5)
        clr.w $b8(a5)
        lea P1,a0
        movea.l a6,a1
        moveq #39,d0
copy_actor:
        move.l (a0)+,(a1)+
        dbra d0,copy_actor
        clr.w $9e(a6)
        move.w #$05c0,$18(a6)
; The original room spawn is collision checked. Reuse it without an unsafe X offset.
        move.w #$ffff,$34(a6)
        move.w #$ffff,$5c(a6)
        clr.l $7e(a6)
        clr.w $86(a6)
        clr.w $a0(a6)
        clr.l $b0(a6)
        clr.l $b4(a6)
        move.w #$06e1,$5a(a6)
        move.w $88(a6),$8a(a6)
        clr.l 4(a5)
        clr.l 8(a5)
        clr.l $c(a5)
        clr.l $10(a5)
        clr.l $14(a5)
        clr.l $18(a5)
        clr.w $1c(a5)
        clr.l $20(a5)
        clr.l $24(a5)
initialized:
; Migrate unused metadata bytes from earlier builds before using grab masks.
        cmpi.b #6,$1f(a5)
        beq.w metadata_ready
        clr.l $20(a5)
        clr.l $24(a5)
        move.b #6,$1f(a5)
metadata_ready:
alive:
        tst.w $1c(a5)
        beq.w graphics_ready
        move.w #$ffff,$34(a6)
        move.w #$ffff,$5c(a6)
        clr.w $1c(a5)
graphics_ready:
        tst.b $ff1983
        bne.w finished
        move.w $88(a6),$8a(a6)
        move.w $8(a6),d0
        sub.w $ff1716,d0
        bmi.w teleport
        cmpi.w #319,d0
        bhi.w teleport
        move.w $c(a6),d0
        sub.w $10(a6),d0
        sub.w $ff171a,d0
        bmi.w teleport
        cmpi.w #223,d0
        bls.w nearby
teleport:
        tst.l P1+$10
        bne.w nearby
        move.l P1+8,8(a6)
        move.l P1+$c,$c(a6)
        move.w P1+$14,$14(a6)
        clr.l $10(a6)
        clr.l $56(a6)
        clr.l $72(a6)
        clr.l $76(a6)
        clr.w 4(a6)
        clr.w $2a(a6)
nearby:
        move.w P1+6,d0
        bne.w mirror_weapon
        move.w $ff0d7e,d0
mirror_weapon:
        cmp.w 6(a6),d0
        beq.w weapon_current
        move.w #$ffff,$5c(a6)
        move.w d0,6(a6)
weapon_current:
        move.l $ff165c,-(sp)
        move.w $ff1660,-(sp)
        move.l $28(a5),$ff165c
        move.w $2c(a5),$ff1660
; Swap the 64-word input history as well, so P2 attacks never read P1 input.
        move.l $ff16e8,-(sp)
        move.l $b0(a5),$ff16e8
        lea $ff1668,a0
        lea $30(a5),a1
        moveq #31,d0
swap_history:
        move.l (a0),d1
        move.l (a1),(a0)+
        move.l d1,(a1)+
        dbra d0,swap_history
        lea $ff1982,a0
        lea 4(a5),a1
        moveq #4,d0
swap_flags:
        move.l (a0),d1
        move.l (a1),(a0)+
        move.l d1,(a1)+
        dbra d0,swap_flags
        move.l $ff197e,d1
        move.l $18(a5),$ff197e
        move.l d1,$18(a5)
        move.w $ff0d7e,-(sp)
        move.w $ff0e3c,-(sp)
        sf $ff1986
        jsr $5670
        move.w (sp)+,$ff0e3c
        move.w (sp)+,d7
        lea META,a5
        lea P2,a6
        move.l $ff197e,d1
        move.l $18(a5),$ff197e
        move.l d1,$18(a5)
        lea $ff1982,a0
        lea 4(a5),a1
        moveq #4,d0
restore_flags:
        move.l (a0),d1
        move.l (a1),(a0)+
        move.l d1,(a1)+
        dbra d0,restore_flags
; The original wear routine clears P1's weapon and requests a reload. That
; request was made inside P2's isolated flags; publish it back to P1 as well.
        cmp.w $ff0d7e,d7
        beq.w weapon_unchanged
        st $ff198f
weapon_unchanged:
        lea $ff1668,a0
        lea $30(a5),a1
        moveq #31,d0
restore_history:
        move.l (a0),d1
        move.l (a1),(a0)+
        move.l d1,(a1)+
        dbra d0,restore_history
        move.l (sp)+,$ff16e8
        move.w (sp)+,$ff1660
        move.l (sp)+,$ff165c
        move.w $88(a6),$8a(a6)
finished:
        movem.l (sp)+,d0-d7/a0-a6
        bsr.w dark_art
        jsr $deec
        rts
; Only P1 may pick up items or start object/story interactions.
pickup_owner:
        cmpa.l #P2,a6
        bne.w pickup_original
        ori.b #1,ccr
        rts
pickup_original:
        moveq #6,d1
        move.w d1,d3
        neg.w d1
        jmp $82b4
interaction_owner:
        cmpa.l #P2,a6
        bne.w interaction_original
        andi.b #$fe,ccr
        rts
interaction_original:
        move.w $16(a6),d3
        bne.w interaction_nonzero
        jmp $831a
interaction_nonzero:
        jmp $82fe
read_pads:
        lea $ff165c,a1
        lea $a10003,a0
        jsr $2992
        movem.l d0-d7/a0-a6,-(sp)
        tst.b $ff185d
        beq.w menu_inactive
        move.w #1,META+$1c
menu_inactive:
        lea META+$28,a1
        lea $a10005,a0
        jsr $2992
        andi.w #$3f3f,META+$2a
        lea META,a5
        move.w $b0(a5),d0
        subq.w #2,d0
        andi.w #$7e,d0
        move.w d0,$b0(a5)
        lea $30(a5),a0
        move.w $2a(a5),(a0,d0.w)
        cmpi.w #63,$b2(a5)
        bcc.w sample_done
        addq.w #1,$b2(a5)
sample_done:
        movem.l (sp)+,d0-d7/a0-a6
        rts
; Player arrows exclude both heroes. Enemy arrows retain their normal targets.
projectile_target:
        cmpi.w #$34,(a6)
        bne.w projectile_original
        cmpi.l #P1,$aa(a6)
        beq.w player_projectile
        cmpi.l #P2,$aa(a6)
        bne.w projectile_original
player_projectile:
        cmpa.l #P1,a0
        beq.w projectile_skip
        cmpa.l #P2,a0
        beq.w projectile_skip
projectile_original:
        tst.w (a0)
        ble.w projectile_skip
        jmp $b95c
projectile_skip:
        jmp $b9bc
menu_return:
        sf $ff185d
        move.w #$ffff,P2+$34
        move.w #$ffff,P2+$5c
        jmp $3d34
; Enemy melee tables target each player using the original hitbox evaluator.
enemy_hit:
        bsr.w restore_position
        movem.l d0-d7/a0-a6,-(sp)
        bsr.w attack_index
        btst #3,$37(a6)
        bne.w attack_masks_ready
        move.l P2+$b0,d1
        bclr d6,d1
        move.l d1,P2+$b0
        move.l P2+$b4,d1
        bclr d6,d1
        move.l d1,P2+$b4
attack_masks_ready:
        move.l #$beba,$ff1940
        lea P1,a0
        lea P2+$b0,a5
        bsr.w independent_hit
        movem.l (sp),d0-d7/a0-a6
        move.l #$beba,$ff1940
        lea P2,a0
        lea P2+$b4,a5
        bsr.w independent_hit
        bsr.w attack_index
        move.l P2+$b0,d1
        or.l P2+$b4,d1
        bclr #3,$37(a6)
        btst d6,d1
        beq.w attack_masks_done
        bset #3,$37(a6)
attack_masks_done:
        movem.l (sp)+,d0-d7/a0-a6
        bsr.w retarget_position
        rts
attack_index:
        move.l a6,d6
        subi.l #P1,d6
        divu.w #$bc,d6
        andi.l #$ffff,d6
        rts
independent_hit:
        bsr.w attack_index
        move.l (a5),d1
        bclr #3,$37(a6)
        btst d6,d1
        beq.w hit_mask_ready
        bset #3,$37(a6)
hit_mask_ready:
        move.l a5,-(sp)
        moveq #0,d7
        jsr $bcea
        movea.l (sp)+,a5
        bsr.w attack_index
        btst #3,$37(a6)
        beq.w hit_recorded
        move.l (a5),d1
        bset d6,d1
        move.l d1,(a5)
hit_recorded:
        rts
; Reject only direct hero-to-hero hits; explosions retain their object owner.
filter_hit:
        cmpa.l #P1,a6
        beq.w hero_source
        cmpa.l #P2,a6
        bne.w apply_hit
hero_source:
        cmpa.l #P1,a0
        beq.w ignore_hit
        cmpa.l #P2,a0
        beq.w ignore_hit
apply_hit:
        tst.b $6d(a0)
        beq.w no_guard
        jmp $bec0
no_guard:
        jmp $bed4
ignore_hit:
        rts
; Run one enemy against the nearest living hero. Only the target coordinates
; are substituted; health, damage and rendering keep their own actor records.
enemy_update:
        movem.l d7/a6,-(sp)
        movem.l d0-d3/a0,-(sp)
        clr.w P2+$a0
        tst.b $ff1983
        bne.w target_selected
        cmpi.w #2,P2
        bne.w target_selected
; A grab keeps its original victim even if the other hero comes closer.
        move.l a6,d0
        subi.l #P1,d0
        divu.w #$bc,d0
        andi.l #$ffff,d0
        move.l META+$20,d1
        btst d0,d1
        bne.w target_selected
        move.l META+$24,d1
        btst d0,d1
        bne.w force_p2_target
        move.w P1+8,d0
        sub.w 8(a6),d0
        bpl.w dist1x
        neg.w d0
dist1x:
        move.w P1+$c,d1
        sub.w $c(a6),d1
        bpl.w dist1y
        neg.w d1
dist1y:
        add.w d1,d0
        move.w P2+8,d2
        sub.w 8(a6),d2
        bpl.w dist2x
        neg.w d2
dist2x:
        move.w P2+$c,d3
        sub.w $c(a6),d3
        bpl.w dist2y
        neg.w d3
dist2y:
        add.w d3,d2
        cmp.w d0,d2
        bcc.w target_selected
force_p2_target:
        move.w #1,P2+$a0
        move.l P1+8,P2+$a4
        move.l P1+$c,P2+$a8
        move.l P1+$10,P2+$ac
        bsr.w retarget_position
target_selected:
        movem.l (sp)+,d0-d3/a0
        jsr (a0)
        bsr.w restore_position
        clr.w P2+$a0
        movem.l (sp)+,d7/a6
        rts
restore_position:
        tst.w P2+$a0
        beq.w position_done
        move.l P2+$a4,P1+8
        move.l P2+$a8,P1+$c
        move.l P2+$ac,P1+$10
        bclr #1,P2+$a1
position_done:
        rts
retarget_position:
        tst.w P2+$a0
        beq.w retarget_done
        move.l P2+8,P1+8
        move.l P2+$c,P1+$c
        move.l P2+$10,P1+$10
        bset #1,P2+$a1
retarget_done:
        rts
hero_check:
        cmpa.l #P1,a6
        beq.w hero_checked
        cmpa.l #P2,a6
hero_checked:
        rts
draw_hud:
; No P2 label or health UI. Preserve original sprite-render entry contract.
; Old save states contain P2 tiles inside the stock effect bank. Repair it
; once, after all sprite DMA requests have been collected for this frame.
        tst.b META+$1e
        beq.w effects_ready
        movem.l d0-d1/a0-a1,-(sp)
; Immutable, predecoded ROM art: no shared decompression RAM is touched.
        movea.l $ff1892,a0
        move.l #$1af880,(a0)+
        move.w #$a900,(a0)+
        move.w #$780,(a0)+
        move.l a0,$ff1892
        movem.l (sp)+,d0-d1/a0-a1
        clr.b META+$1e
effects_ready:
        lea $ff13cc,a6
        rts

; Title uses the original game's font, palette and plane, before fade-in.
title_caption:
        movem.l d0-d7/a0-a6,-(sp)
        lea caption_text,a6
        move.l #$491c0003,d5
        move.w #$61c1,d6
        jsr $2ce4
        movem.l (sp)+,d0-d7/a0-a6
        tst.b $ff0bfd
        rts
caption_text:
        dc.b "Coop version",0
        even

; All pending damage paths pass here, including environmental damage created
; during the hero update. P1 takes the exact original path.
damage_gate:
; Both heroes take the original damage and hit-reaction path.
        move.w $86(a6),d0
        beq.w damage_none
        jmp $5802
damage_none:
        jmp $5942

; Preserve only P2 health. Original stun, interruption, knockback and immunity
; frames still run, with the same flags/metadata as P1.
preserve_p2_health:
        cmpa.l #P2,a6
        beq.w health_unchanged
        sub.w d0,d1
health_unchanged:
        move.w d1,$8a(a6)
        rts

 ; A knocked-back hero is not a damaging projectile against the other hero.
thrown_hero_target:
        cmpa.l #P1,a6
        beq.w thrown_hero_source
        cmpa.l #P2,a6
        bne.w thrown_original
thrown_hero_source:
        cmpa.l #P1,a0
        beq.w thrown_skip
        cmpa.l #P2,a0
        beq.w thrown_skip
thrown_original:
        move.l $7e(a6),d0
        cmp.l a0,d0
        beq.w thrown_skip
        jmp $b7fa
thrown_skip:
        jmp $b848

; Some enemy families bypass enemy_hit and call the stock collision evaluator.
; Always evaluate real actor positions, and route a single-hero attack to its
; selected actor. A return trampoline restores the AI's temporary target view.
collision_entry:
        move.w sr,-(sp)
        btst #1,P2+$a1
        beq.w collision_unmodified
        movem.l d0-d7/a0-a6,-(sp)
        bsr.w restore_position
        movem.l (sp)+,d0-d7/a0-a6
        tst.w d7
        bne.w collision_prepared
        cmpa.l #P1,a0
        bne.w collision_prepared
        lea P2,a0
collision_prepared:
        move.w (sp)+,sr
        pea collision_return
        bra.w collision_original
collision_unmodified:
        move.w (sp)+,sr
collision_original:
        btst #3,$37(a6)
        bne.w collision_no_hit
        jmp $bcf4
collision_no_hit:
        jmp $be96
collision_return:
        move.w sr,-(sp)
        movem.l d0-d7/a0-a6,-(sp)
        bsr.w retarget_position
        movem.l (sp)+,d0-d7/a0-a6
        move.w (sp)+,sr
        rts

; Masked collision helpers are also used by fire/projectiles and body impacts.
projectile_collision:
        move.w sr,-(sp)
        ext.w d0
        ext.l d0
        btst #1,P2+$a1
        beq.w projectile_collision_plain
        movem.l d0-d7/a0-a6,-(sp)
        bsr.w restore_position
        movem.l (sp)+,d0-d7/a0-a6
        cmpi.l #1,d0
        bne.w projectile_collision_ready
        move.l #$100000,d0
projectile_collision_ready:
        move.w (sp)+,sr
        pea collision_return
        bra.w projectile_collision_original
projectile_collision_plain:
        move.w (sp)+,sr
projectile_collision_original:
        move.w 8(a6),d7
        jmp $b92a
body_collision:
        move.w sr,-(sp)
        btst #1,P2+$a1
        beq.w body_collision_plain
        movem.l d0-d7/a0-a6,-(sp)
        bsr.w restore_position
        movem.l (sp)+,d0-d7/a0-a6
        cmpi.l #1,d0
        bne.w body_collision_ready
        move.l #$100000,d0
body_collision_ready:
        move.w (sp)+,sr
        pea collision_return
        bra.w body_collision_original
body_collision_plain:
        move.w (sp)+,sr
body_collision_original:
        move.w 8(a6),d6
        add.w d6,d1
        jmp $b85c
fire_immunity:
        cmpa.l #P2,a0
        bne.w fire_immunity_p1
        move.b #14,META+$10
        rts
fire_immunity_p1:
        move.b #14,$ff198e
        rts

; Original animation/mapping table is retained. Only the source of body tiles
; changes; no palette RAM is consumed and no other actor's graphics change.
dark_art:
        cmpi.w #2,P2
        bne.w dark_art_done
; Body B800-BFFF; weapon DC20-DE1F (16 tiles). Original small objects
; retain D280-DB7F. Full-screen hscroll uses DC00-DC03 (VDP reg11=0).
; Menus invalidate both banks before gameplay resumes.
        cmpi.w #$05c0,P2+$18
        beq.w body_bank_ready
        move.w #$05c0,P2+$18
        move.w #$ffff,P2+$34
; Old Immortal5 states may have P2 art over these item slots. Invalidate
; their cached mappings so every live object reuploads its original tiles.
        move.w #$ffff,$ff2af0
        move.w #$ffff,$ff2b4a
        move.w #$ffff,$ff2ba4
        move.w #$ffff,$ff2bfe
        move.w #$ffff,$ff2c58
        move.w #$ffff,$ff2cb2
        move.w #$ffff,$ff2d0c
        move.w #$ffff,$ff2d66
        st META+$1e
body_bank_ready:
        cmpi.w #$06e1,P2+$5a
        beq.w weapon_bank_ready
        move.w #$06e1,P2+$5a
        move.w #$ffff,P2+$5c
weapon_bank_ready:
        cmpi.l #$13cdfc,P2+$1a
        bne.w dark_art_done
        cmpi.l #$310000,P2+$1e
        beq.w dark_art_done
        move.w #$ffff,P2+$34
        move.l #$310000,P2+$1e
dark_art_done:
        rts
; Original dialogue text owns B800-BFFF while P1's story lock is set.
; Do not upload P2 body/weapon art during that interval. On resume the
; native renderer reloads both mappings before displaying the helper.
render_actor:
        cmpa.l #P2,a6
        bne.w render_original
        tst.b $ff1983
        bne.w render_hidden
        tst.b $ff185d
        bne.w render_hidden
render_original:
        tst.w (a6)
        bmi.w render_negative
        btst #0,$36(a6)
        beq.w render_static
        jmp $a9a0
render_negative:
        jmp $a324
render_static:
        jmp $ad76
render_hidden:
        move.w #$ffff,P2+$34
        move.w #$ffff,P2+$5c
        rts
        even

; Per-object capture ownership uses META+20/+24 (two 32-bit masks).
grab_lock:
        movem.l d0-d1,-(sp)
        move.l a6,d0
        subi.l #P1,d0
        divu.w #$bc,d0
        andi.l #$ffff,d0
        move.l META+$20,d1
        bclr d0,d1
        move.l d1,META+$20
        move.l META+$24,d1
        bclr d0,d1
        move.l d1,META+$24
        btst #0,P2+$a1
        beq.w grab_lock_p1
        move.l META+$24,d1
        bset d0,d1
        move.l d1,META+$24
        bra.w grab_lock_done
grab_lock_p1:
        move.l META+$20,d1
        bset d0,d1
        move.l d1,META+$20
grab_lock_done:
        movem.l (sp)+,d0-d1
        rts
grab_unlock:
        movem.l d0-d1,-(sp)
        move.l a6,d0
        subi.l #P1,d0
        divu.w #$bc,d0
        andi.l #$ffff,d0
        move.l META+$20,d1
        bclr d0,d1
        move.l d1,META+$20
        move.l META+$24,d1
        bclr d0,d1
        move.l d1,META+$24
        movem.l (sp)+,d0-d1
        rts
route_01a39c:
        move.w sr,-(sp)
        bsr.w grab_lock
        btst #0,P2+$a1
        beq.w route_01a39c_p1
        move.w (sp)+,sr
        dc.b $08,$f9,$00,$03,$00,$ff,$28,$ce
        rts
route_01a39c_p1:
        move.w (sp)+,sr
        dc.b $08,$f9,$00,$03,$00,$ff,$1a,$1e
        rts
route_01a3a4:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01a3a4_p1
        move.w (sp)+,sr
        dc.b $08,$b9,$00,$06,$00,$ff,$28,$ce
        rts
route_01a3a4_p1:
        move.w (sp)+,sr
        dc.b $08,$b9,$00,$06,$00,$ff,$1a,$1e
        rts
route_01a3ac:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01a3ac_p1
        move.w (sp)+,sr
        dc.b $00,$39,$00,$0c,$00,$ff,$28,$d0
        rts
route_01a3ac_p1:
        move.w (sp)+,sr
        dc.b $00,$39,$00,$0c,$00,$ff,$1a,$20
        rts
route_01a3b4:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01a3b4_p1
        move.w (sp)+,sr
        dc.b $02,$39,$ff,$f3,$00,$ff,$28,$d1
        rts
route_01a3b4_p1:
        move.w (sp)+,sr
        dc.b $02,$39,$ff,$f3,$00,$ff,$1a,$21
        rts
route_01a3bc:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01a3bc_p1
        move.w (sp)+,sr
        dc.b $51,$f9,$00,$ff,$29,$1b
        rts
route_01a3bc_p1:
        move.w (sp)+,sr
        dc.b $51,$f9,$00,$ff,$1a,$6b
        rts
route_01a3c2:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01a3c2_p1
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$00,$00,$ff,$28,$c2
        rts
route_01a3c2_p1:
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$00,$00,$ff,$1a,$12
        rts
route_01a3ca:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01a3ca_p1
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$02,$00,$ff,$28,$9c
        rts
route_01a3ca_p1:
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$02,$00,$ff,$19,$ec
        rts
route_01a3ec:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01a3ec_p1
        move.w (sp)+,sr
        dc.b $0c,$79,$00,$14,$00,$ff,$28,$e2
        rts
route_01a3ec_p1:
        move.w (sp)+,sr
        dc.b $0c,$79,$00,$14,$00,$ff,$1a,$32
        rts
route_01a412:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01a412_p1
        move.w (sp)+,sr
        dc.b $08,$39,$00,$03,$00,$ff,$28,$d0
        rts
route_01a412_p1:
        move.w (sp)+,sr
        dc.b $08,$39,$00,$03,$00,$ff,$1a,$20
        rts
route_01a458:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01a458_p1
        move.w (sp)+,sr
        dc.b $4a,$b9,$00,$ff,$28,$a8
        rts
route_01a458_p1:
        move.w (sp)+,sr
        dc.b $4a,$b9,$00,$ff,$19,$f8
        rts
route_01a462:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01a462_p1
        move.w (sp)+,sr
        dc.b $4a,$39,$00,$ff,$29,$1a
        rts
route_01a462_p1:
        move.w (sp)+,sr
        dc.b $4a,$39,$00,$ff,$1a,$6a
        rts
route_01a678:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01a678_p1
        move.w (sp)+,sr
        dc.b $08,$39,$00,$03,$00,$ff,$28,$d0
        rts
route_01a678_p1:
        move.w (sp)+,sr
        dc.b $08,$39,$00,$03,$00,$ff,$1a,$20
        rts
route_01a6ba:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01a6ba_p1
        move.w (sp)+,sr
        dc.b $4a,$b9,$00,$ff,$28,$a8
        rts
route_01a6ba_p1:
        move.w (sp)+,sr
        dc.b $4a,$b9,$00,$ff,$19,$f8
        rts
route_01a6c4:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01a6c4_p1
        move.w (sp)+,sr
        dc.b $4a,$39,$00,$ff,$29,$1a
        rts
route_01a6c4_p1:
        move.w (sp)+,sr
        dc.b $4a,$39,$00,$ff,$1a,$6a
        rts
route_01a788:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01a788_p1
        move.w (sp)+,sr
        dc.b $08,$39,$00,$03,$00,$ff,$28,$d0
        rts
route_01a788_p1:
        move.w (sp)+,sr
        dc.b $08,$39,$00,$03,$00,$ff,$1a,$20
        rts
route_01a7dc:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01a7dc_p1
        move.w (sp)+,sr
        dc.b $4a,$b9,$00,$ff,$28,$a8
        rts
route_01a7dc_p1:
        move.w (sp)+,sr
        dc.b $4a,$b9,$00,$ff,$19,$f8
        rts
route_01a7e6:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01a7e6_p1
        move.w (sp)+,sr
        dc.b $4a,$39,$00,$ff,$29,$1a
        rts
route_01a7e6_p1:
        move.w (sp)+,sr
        dc.b $4a,$39,$00,$ff,$1a,$6a
        rts
route_01ab18:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ab18_p1
        move.w (sp)+,sr
        dc.b $33,$ee,$00,$08,$00,$ff,$28,$a0
        rts
route_01ab18_p1:
        move.w (sp)+,sr
        dc.b $33,$ee,$00,$08,$00,$ff,$19,$f0
        rts
route_01ab20:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ab20_p1
        move.w (sp)+,sr
        dc.b $33,$ee,$00,$0c,$00,$ff,$28,$a4
        rts
route_01ab20_p1:
        move.w (sp)+,sr
        dc.b $33,$ee,$00,$0c,$00,$ff,$19,$f4
        rts
route_01ab2a:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ab2a_p1
        move.w (sp)+,sr
        dc.b $23,$c0,$00,$ff,$29,$0a
        rts
route_01ab2a_p1:
        move.w (sp)+,sr
        dc.b $23,$c0,$00,$ff,$1a,$5a
        rts
route_01ab30:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ab30_p1
        move.w (sp)+,sr
        dc.b $23,$c0,$00,$ff,$29,$0e
        rts
route_01ab30_p1:
        move.w (sp)+,sr
        dc.b $23,$c0,$00,$ff,$1a,$5e
        rts
route_01ab36:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ab36_p1
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$48,$00,$ff,$28,$a8
        rts
route_01ab36_p1:
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$48,$00,$ff,$19,$f8
        rts
route_01ab3e:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ab3e_p1
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$00,$00,$ff,$28,$ae
        rts
route_01ab3e_p1:
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$00,$00,$ff,$19,$fe
        rts
route_01ab46:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ab46_p1
        move.w (sp)+,sr
        dc.b $08,$f9,$00,$00,$00,$ff,$28,$cf
        rts
route_01ab46_p1:
        move.w (sp)+,sr
        dc.b $08,$f9,$00,$00,$00,$ff,$1a,$1f
        rts
route_01ab4e:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ab4e_p1
        move.w (sp)+,sr
        dc.b $33,$fc,$01,$3c,$00,$ff,$28,$ca
        rts
route_01ab4e_p1:
        move.w (sp)+,sr
        dc.b $33,$fc,$01,$3c,$00,$ff,$1a,$1a
        rts
route_01abb8:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01abb8_p1
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$45,$00,$ff,$28,$a8
        rts
route_01abb8_p1:
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$45,$00,$ff,$19,$f8
        rts
route_01abcc:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01abcc_p1
        move.w (sp)+,sr
        dc.b $30,$39,$00,$ff,$29,$22
        rts
route_01abcc_p1:
        move.w (sp)+,sr
        dc.b $30,$39,$00,$ff,$1a,$72
        rts
route_01abde:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01abde_p1
        move.w P2+$8a,-(sp)
        move.w 2(sp),sr
        dc.b $33,$c0,$00,$ff,$29,$22
        move.w sr,-(sp)
        move.w 2(sp),P2+$8a
        move.w (sp)+,sr
        lea 4(sp),sp
        rts
route_01abde_p1:
        move.w (sp)+,sr
        dc.b $33,$c0,$00,$ff,$1a,$72
        rts
route_01abec:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01abec_p1
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$48,$00,$ff,$28,$a8
        rts
route_01abec_p1:
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$48,$00,$ff,$19,$f8
        rts
route_01abfc:
        move.w sr,-(sp)
        bsr.w grab_unlock
        btst #0,P2+$a1
        beq.w route_01abfc_p1
        move.w (sp)+,sr
        dc.b $51,$f9,$00,$ff,$27,$e0
        rts
route_01abfc_p1:
        move.w (sp)+,sr
        dc.b $51,$f9,$00,$ff,$19,$82
        rts
route_01ac02:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ac02_p1
        move.w (sp)+,sr
        dc.b $08,$b9,$00,$03,$00,$ff,$28,$ce
        rts
route_01ac02_p1:
        move.w (sp)+,sr
        dc.b $08,$b9,$00,$03,$00,$ff,$1a,$1e
        rts
route_01ac0a:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ac0a_p1
        move.w (sp)+,sr
        dc.b $08,$b9,$00,$00,$00,$ff,$28,$cf
        rts
route_01ac0a_p1:
        move.w (sp)+,sr
        dc.b $08,$b9,$00,$00,$00,$ff,$1a,$1f
        rts
route_01ac12:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ac12_p1
        move.w (sp)+,sr
        dc.b $02,$39,$ff,$f3,$00,$ff,$28,$d0
        rts
route_01ac12_p1:
        move.w (sp)+,sr
        dc.b $02,$39,$ff,$f3,$00,$ff,$1a,$20
        rts
route_01ac1a:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ac1a_p1
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$26,$00,$ff,$28,$c2
        rts
route_01ac1a_p1:
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$26,$00,$ff,$1a,$12
        rts
route_01ac22:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ac22_p1
        move.w (sp)+,sr
        dc.b $42,$79,$00,$ff,$28,$ae
        rts
route_01ac22_p1:
        move.w (sp)+,sr
        dc.b $42,$79,$00,$ff,$19,$fe
        rts
route_01ac28:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ac28_p1
        move.w (sp)+,sr
        dc.b $42,$79,$00,$ff,$28,$9c
        rts
route_01ac28_p1:
        move.w (sp)+,sr
        dc.b $42,$79,$00,$ff,$19,$ec
        rts
route_01ac36:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ac36_p1
        move.w (sp)+,sr
        dc.b $33,$c0,$00,$ff,$29,$1e
        rts
route_01ac36_p1:
        move.w (sp)+,sr
        dc.b $33,$c0,$00,$ff,$1a,$6e
        rts
route_01ac3c:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ac3c_p1
        move.w (sp)+,sr
        dc.b $23,$ce,$00,$ff,$29,$16
        rts
route_01ac3c_p1:
        move.w (sp)+,sr
        dc.b $23,$ce,$00,$ff,$1a,$66
        rts
route_01ac42:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ac42_p1
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$02,$00,$ff,$29,$1c
        rts
route_01ac42_p1:
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$02,$00,$ff,$1a,$6c
        rts
route_01ac4a:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ac4a_p1
        move.w (sp)+,sr
        dc.b $13,$fc,$00,$01,$00,$ff,$29,$1a
        rts
route_01ac4a_p1:
        move.w (sp)+,sr
        dc.b $13,$fc,$00,$01,$00,$ff,$1a,$6a
        rts
route_01ac52:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ac52_p1
        move.w (sp)+,sr
        dc.b $13,$fc,$00,$06,$00,$ff,$29,$1b
        rts
route_01ac52_p1:
        move.w (sp)+,sr
        dc.b $13,$fc,$00,$06,$00,$ff,$1a,$6b
        rts
route_01ac6a:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ac6a_p1
        move.w (sp)+,sr
        dc.b $23,$c1,$00,$ff,$28,$e6
        rts
route_01ac6a_p1:
        move.w (sp)+,sr
        dc.b $23,$c1,$00,$ff,$1a,$36
        rts
route_01ac70:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ac70_p1
        move.w (sp)+,sr
        dc.b $23,$c2,$00,$ff,$28,$ea
        rts
route_01ac70_p1:
        move.w (sp)+,sr
        dc.b $23,$c2,$00,$ff,$1a,$3a
        rts
route_01ac76:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ac76_p1
        move.w (sp)+,sr
        dc.b $23,$fc,$00,$02,$80,$00,$00,$ff,$28,$ee
        rts
route_01ac76_p1:
        move.w (sp)+,sr
        dc.b $23,$fc,$00,$02,$80,$00,$00,$ff,$1a,$3e
        rts
route_01ac80:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ac80_p1
        move.w (sp)+,sr
        dc.b $23,$fc,$00,$11,$00,$00,$00,$ff,$29,$0e
        rts
route_01ac80_p1:
        move.w (sp)+,sr
        dc.b $23,$fc,$00,$11,$00,$00,$00,$ff,$1a,$5e
        rts
route_01cc42:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01cc42_p1
        move.w (sp)+,sr
        dc.b $08,$39,$00,$03,$00,$ff,$28,$d0
        rts
route_01cc42_p1:
        move.w (sp)+,sr
        dc.b $08,$39,$00,$03,$00,$ff,$1a,$20
        rts
route_01cc4c:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01cc4c_p1
        move.w (sp)+,sr
        dc.b $4a,$b9,$00,$ff,$28,$a8
        rts
route_01cc4c_p1:
        move.w (sp)+,sr
        dc.b $4a,$b9,$00,$ff,$19,$f8
        rts
route_01cc54:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01cc54_p1
        move.w (sp)+,sr
        dc.b $0c,$79,$00,$28,$00,$ff,$28,$e2
        rts
route_01cc54_p1:
        move.w (sp)+,sr
        dc.b $0c,$79,$00,$28,$00,$ff,$1a,$32
        rts
route_01cc5e:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01cc5e_p1
        move.w (sp)+,sr
        dc.b $30,$39,$00,$ff,$28,$ac
        rts
route_01cc5e_p1:
        move.w (sp)+,sr
        dc.b $30,$39,$00,$ff,$19,$fc
        rts
route_01cc6a:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01cc6a_p1
        move.w (sp)+,sr
        dc.b $4a,$39,$00,$ff,$27,$e9
        rts
route_01cc6a_p1:
        move.w (sp)+,sr
        dc.b $4a,$39,$00,$ff,$19,$8b
        rts
route_01cc72:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01cc72_p1
        move.w (sp)+,sr
        dc.b $4a,$39,$00,$ff,$27,$e5
        rts
route_01cc72_p1:
        move.w (sp)+,sr
        dc.b $4a,$39,$00,$ff,$19,$87
        rts
route_01cc7a:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01cc7a_p1
        move.w (sp)+,sr
        dc.b $30,$39,$00,$ff,$28,$a0
        rts
route_01cc7a_p1:
        move.w (sp)+,sr
        dc.b $30,$39,$00,$ff,$19,$f0
        rts
route_01cc88:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01cc88_p1
        move.w (sp)+,sr
        dc.b $30,$39,$00,$ff,$28,$a4
        rts
route_01cc88_p1:
        move.w (sp)+,sr
        dc.b $30,$39,$00,$ff,$19,$f4
        rts
route_01ccbc:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ccbc_p1
        move.w (sp)+,sr
        dc.b $4a,$39,$00,$ff,$27,$e7
        rts
route_01ccbc_p1:
        move.w (sp)+,sr
        dc.b $4a,$39,$00,$ff,$19,$89
        rts
route_01ccf4:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01ccf4_p1
        move.w (sp)+,sr
        dc.b $32,$39,$00,$ff,$29,$22
        rts
route_01ccf4_p1:
        move.w (sp)+,sr
        dc.b $32,$39,$00,$ff,$1a,$72
        rts
route_01cd04:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01cd04_p1
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$01,$00,$ff,$29,$1e
        rts
route_01cd04_p1:
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$01,$00,$ff,$1a,$6e
        rts
route_01cd0c:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01cd0c_p1
        move.w (sp)+,sr
        dc.b $33,$ee,$00,$16,$00,$ff,$29,$1c
        rts
route_01cd0c_p1:
        move.w (sp)+,sr
        dc.b $33,$ee,$00,$16,$00,$ff,$1a,$6c
        rts
route_01cd14:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01cd14_p1
        move.w (sp)+,sr
        dc.b $23,$ce,$00,$ff,$29,$16
        rts
route_01cd14_p1:
        move.w (sp)+,sr
        dc.b $23,$ce,$00,$ff,$1a,$66
        rts
route_01cd1a:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01cd1a_p1
        move.w (sp)+,sr
        dc.b $13,$fc,$00,$01,$00,$ff,$29,$1a
        rts
route_01cd1a_p1:
        move.w (sp)+,sr
        dc.b $13,$fc,$00,$01,$00,$ff,$1a,$6a
        rts
route_01cd22:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01cd22_p1
        move.w (sp)+,sr
        dc.b $13,$fc,$00,$06,$00,$ff,$29,$1b
        rts
route_01cd22_p1:
        move.w (sp)+,sr
        dc.b $13,$fc,$00,$06,$00,$ff,$1a,$6b
        rts
route_01cd3c:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_01cd3c_p1
        move.w P2+$8a,-(sp)
        move.w 2(sp),sr
        dc.b $33,$c1,$00,$ff,$29,$22
        move.w sr,-(sp)
        move.w 2(sp),P2+$8a
        move.w (sp)+,sr
        lea 4(sp),sp
        rts
route_01cd3c_p1:
        move.w (sp)+,sr
        dc.b $33,$c1,$00,$ff,$1a,$72
        rts
route_02077c:
        move.w sr,-(sp)
        bsr.w grab_lock
        btst #0,P2+$a1
        beq.w route_02077c_p1
        move.w (sp)+,sr
        dc.b $08,$f9,$00,$06,$00,$ff,$28,$ce
        rts
route_02077c_p1:
        move.w (sp)+,sr
        dc.b $08,$f9,$00,$06,$00,$ff,$1a,$1e
        rts
route_020784:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_020784_p1
        move.w (sp)+,sr
        dc.b $00,$39,$00,$0c,$00,$ff,$28,$d0
        rts
route_020784_p1:
        move.w (sp)+,sr
        dc.b $00,$39,$00,$0c,$00,$ff,$1a,$20
        rts
route_02078c:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_02078c_p1
        move.w (sp)+,sr
        dc.b $02,$39,$ff,$f3,$00,$ff,$28,$d1
        rts
route_02078c_p1:
        move.w (sp)+,sr
        dc.b $02,$39,$ff,$f3,$00,$ff,$1a,$21
        rts
route_020794:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_020794_p1
        move.w (sp)+,sr
        dc.b $51,$f9,$00,$ff,$29,$1b
        rts
route_020794_p1:
        move.w (sp)+,sr
        dc.b $51,$f9,$00,$ff,$1a,$6b
        rts
route_02079a:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_02079a_p1
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$02,$00,$ff,$28,$9c
        rts
route_02079a_p1:
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$02,$00,$ff,$19,$ec
        rts
route_0207a6:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_0207a6_p1
        move.w (sp)+,sr
        dc.b $0c,$79,$00,$03,$00,$ff,$28,$ae
        rts
route_0207a6_p1:
        move.w (sp)+,sr
        dc.b $0c,$79,$00,$03,$00,$ff,$19,$fe
        rts
route_0207c4:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_0207c4_p1
        move.w (sp)+,sr
        dc.b $33,$c0,$00,$ff,$28,$c2
        rts
route_0207c4_p1:
        move.w (sp)+,sr
        dc.b $33,$c0,$00,$ff,$1a,$12
        rts
route_0207ca:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_0207ca_p1
        move.w (sp)+,sr
        dc.b $42,$b9,$00,$ff,$29,$0a
        rts
route_0207ca_p1:
        move.w (sp)+,sr
        dc.b $42,$b9,$00,$ff,$1a,$5a
        rts
route_0207d0:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_0207d0_p1
        move.w (sp)+,sr
        dc.b $42,$b9,$00,$ff,$29,$0e
        rts
route_0207d0_p1:
        move.w (sp)+,sr
        dc.b $42,$b9,$00,$ff,$1a,$5e
        rts
route_020806:
        move.w sr,-(sp)
        bsr.w grab_unlock
        btst #0,P2+$a1
        beq.w route_020806_p1
        move.w (sp)+,sr
        dc.b $51,$f9,$00,$ff,$27,$e0
        rts
route_020806_p1:
        move.w (sp)+,sr
        dc.b $51,$f9,$00,$ff,$19,$82
        rts
route_02080c:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_02080c_p1
        move.w (sp)+,sr
        dc.b $51,$f9,$00,$ff,$27,$e5
        rts
route_02080c_p1:
        move.w (sp)+,sr
        dc.b $51,$f9,$00,$ff,$19,$87
        rts
route_020812:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_020812_p1
        move.w (sp)+,sr
        dc.b $08,$b9,$00,$06,$00,$ff,$28,$ce
        rts
route_020812_p1:
        move.w (sp)+,sr
        dc.b $08,$b9,$00,$06,$00,$ff,$1a,$1e
        rts
route_02081a:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_02081a_p1
        move.w (sp)+,sr
        dc.b $02,$39,$ff,$f3,$00,$ff,$28,$d0
        rts
route_02081a_p1:
        move.w (sp)+,sr
        dc.b $02,$39,$ff,$f3,$00,$ff,$1a,$20
        rts
route_020822:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_020822_p1
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$00,$00,$ff,$28,$c2
        rts
route_020822_p1:
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$00,$00,$ff,$1a,$12
        rts
route_02082a:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_02082a_p1
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$00,$00,$ff,$28,$9c
        rts
route_02082a_p1:
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$00,$00,$ff,$19,$ec
        rts
route_020a62:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_020a62_p1
        move.w (sp)+,sr
        dc.b $4a,$39,$00,$ff,$27,$e7
        rts
route_020a62_p1:
        move.w (sp)+,sr
        dc.b $4a,$39,$00,$ff,$19,$89
        rts
route_020a74:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_020a74_p1
        move.w (sp)+,sr
        dc.b $57,$79,$00,$ff,$29,$26
        rts
route_020a74_p1:
        move.w (sp)+,sr
        dc.b $57,$79,$00,$ff,$1a,$76
        rts
route_020a7e:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_020a7e_p1
        move.w (sp)+,sr
        dc.b $42,$79,$00,$ff,$29,$26
        rts
route_020a7e_p1:
        move.w (sp)+,sr
        dc.b $42,$79,$00,$ff,$1a,$76
        rts
route_020a86:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_020a86_p1
        move.w (sp)+,sr
        dc.b $41,$f9,$00,$ff,$28,$98
        rts
route_020a86_p1:
        move.w (sp)+,sr
        dc.b $41,$f9,$00,$ff,$19,$e8
        rts
route_020af8:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_020af8_p1
        move.w (sp)+,sr
        dc.b $33,$c0,$00,$ff,$28,$ae
        rts
route_020af8_p1:
        move.w (sp)+,sr
        dc.b $33,$c0,$00,$ff,$19,$fe
        rts
route_020b1c:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_020b1c_p1
        move.w (sp)+,sr
        dc.b $33,$c1,$00,$ff,$28,$c2
        rts
route_020b1c_p1:
        move.w (sp)+,sr
        dc.b $33,$c1,$00,$ff,$1a,$12
        rts
route_023b12:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_023b12_p1
        move.w (sp)+,sr
        dc.b $30,$39,$00,$ff,$28,$a0
        rts
route_023b12_p1:
        move.w (sp)+,sr
        dc.b $30,$39,$00,$ff,$19,$f0
        rts
route_023b2a:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_023b2a_p1
        move.w (sp)+,sr
        dc.b $08,$39,$00,$03,$00,$ff,$28,$d0
        rts
route_023b2a_p1:
        move.w (sp)+,sr
        dc.b $08,$39,$00,$03,$00,$ff,$1a,$20
        rts
route_023b36:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_023b36_p1
        move.w (sp)+,sr
        dc.b $0c,$79,$00,$14,$00,$ff,$28,$e2
        rts
route_023b36_p1:
        move.w (sp)+,sr
        dc.b $0c,$79,$00,$14,$00,$ff,$1a,$32
        rts
route_023b42:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_023b42_p1
        move.w (sp)+,sr
        dc.b $23,$ce,$00,$ff,$29,$16
        rts
route_023b42_p1:
        move.w (sp)+,sr
        dc.b $23,$ce,$00,$ff,$1a,$66
        rts
route_023b48:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_023b48_p1
        move.w (sp)+,sr
        dc.b $13,$fc,$00,$01,$00,$ff,$29,$1a
        rts
route_023b48_p1:
        move.w (sp)+,sr
        dc.b $13,$fc,$00,$01,$00,$ff,$1a,$6a
        rts
route_023b50:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_023b50_p1
        move.w (sp)+,sr
        dc.b $13,$fc,$00,$06,$00,$ff,$29,$1b
        rts
route_023b50_p1:
        move.w (sp)+,sr
        dc.b $13,$fc,$00,$06,$00,$ff,$1a,$6b
        rts
route_023b58:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_023b58_p1
        move.w (sp)+,sr
        dc.b $33,$fc,$a0,$32,$00,$ff,$29,$1e
        rts
route_023b58_p1:
        move.w (sp)+,sr
        dc.b $33,$fc,$a0,$32,$00,$ff,$1a,$6e
        rts
route_023b60:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_023b60_p1
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$02,$00,$ff,$29,$1c
        rts
route_023b60_p1:
        move.w (sp)+,sr
        dc.b $33,$fc,$00,$02,$00,$ff,$1a,$6c
        rts
route_023b7a:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_023b7a_p1
        move.w (sp)+,sr
        dc.b $23,$c1,$00,$ff,$28,$e6
        rts
route_023b7a_p1:
        move.w (sp)+,sr
        dc.b $23,$c1,$00,$ff,$1a,$36
        rts
route_023b80:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_023b80_p1
        move.w (sp)+,sr
        dc.b $23,$c2,$00,$ff,$28,$ea
        rts
route_023b80_p1:
        move.w (sp)+,sr
        dc.b $23,$c2,$00,$ff,$1a,$3a
        rts
route_023b86:
        move.w sr,-(sp)
        btst #0,P2+$a1
        beq.w route_023b86_p1
        move.w (sp)+,sr
        dc.b $23,$fc,$00,$02,$80,$00,$00,$ff,$28,$ee
        rts
route_023b86_p1:
        move.w (sp)+,sr
        dc.b $23,$fc,$00,$02,$80,$00,$00,$ff,$1a,$3e
        rts
        dcb.b $310000-*,0
; Darkened source tiles are derived from the user's original ROM by build.py.
