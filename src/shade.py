"""Deterministic indexed-color dimming of the original P2 art, no generation."""
ART_SOURCE = 0xC0000
ART_END = 0x10F100
ART_TARGET = 0x310000
# Original palette indices. Transparency stays zero; cool effect colors stay
# unchanged. Warm body highlights use an existing darker shade at 25% density.
DARKER = (0,1,1,9,3,5,6,7,8,8,9,11,12,12,14,13)
BAYER = ((0,8,2,10),(12,4,14,6),(3,11,1,9),(15,7,13,5))

def shade_art(source):
    assert len(source) >= ART_END
    art = bytearray(source[ART_SOURCE:ART_END])
    for i, value in enumerate(art):
        pixel = i % 32
        y = pixel // 4
        x = (pixel % 4) * 2
        hi, lo = value >> 4, value & 15
        if BAYER[y % 4][x % 4] < 4: hi = DARKER[hi]
        if BAYER[y % 4][(x + 1) % 4] < 4: lo = DARKER[lo]
        art[i] = (hi << 4) | lo
    return bytes(art)
