"""Original deterministic pixel rigs, raster atlases, scenery and PCM sound.

Run from anywhere with Python + pygame. No web access or image API is used here.
The sanctuary plate is the separately generated original image in assets/.
"""
import json
import math
import os
from pathlib import Path
import random
import struct
import wave

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

OUT = Path(__file__).resolve().parents[1] / "assets"
pygame.init()
pygame.display.set_mode((1, 1))


def poly(s, color, points, edge=(15, 25, 35), width=1):
    points = [(round(x), round(y)) for x, y in points]
    pygame.draw.polygon(s, color, points)
    if edge:
        pygame.draw.polygon(s, edge, points, width)


def line(s, color, a, b, w=1):
    pygame.draw.line(s, color, (round(a[0]), round(a[1])), (round(b[0]), round(b[1])), w)


def rect(s, color, box):
    pygame.draw.rect(s, color, tuple(round(v) for v in box))


def knight(state, frame):
    s = pygame.Surface((96, 96), pygame.SRCALPHA)
    t = frame / 8 * math.tau
    walk = state == "walk"
    bob = round(math.sin(t) * 1.2) if state in ("idle", "guard", "wedding") else 0
    y = 0 if walk else bob
    if state == "propose":
        y += min(11, frame * 3)
    if state == "hurt":
        y += round(math.sin(frame/7*math.pi)*3)
    armor, light, shade = (133, 166, 177), (219, 235, 220), (62, 91, 114)
    gold, dark = (222, 180, 87), (15, 25, 37)
    cape = (139, 40, 59) if state != "wedding" else (231, 223, 186)
    # Scalloped cloth silhouette, separate from the articulated plate armor.
    poly(s, cape, [(40, 48+y), (31, 53+y), (27+math.sin(t)*3, 78), (32, 86),
                   (38, 82), (43, 87), (48, 79), (45, 50+y)])
    line(s, (191, 65, 73) if state != "wedding" else light, (35, 56+y), (32, 78), 2)
    line(s, (88, 33, 54), (41, 58+y), (40, 79), 2)
    # Boots, articulated knees and greaves. Distinct eight-frame gait.
    for side in (-1, 1):
        stride = round(math.sin(t + (math.pi if side < 0 else 0)) * 6) if walk else side * 3
        x = 47 + side * 4
        knee = (x + stride*.4, 75+y*.2)
        foot = (x + stride, 87)
        if state == "propose" and side < 0:
            knee, foot = (36, 87), (32, 87)
        poly(s, shade, [(x-4, 66+y), (x+4, 66+y), (knee[0]+3, knee[1]),
                        (foot[0]+3, foot[1]), (foot[0]-4, foot[1]), (knee[0]-3, knee[1])])
        line(s, light, (knee[0], knee[1]+2), (foot[0], foot[1]-3), 2)
        rect(s, armor, (knee[0]-3, knee[1]-2, 6, 4))
        rect(s, dark, (foot[0]-4, foot[1]-1, 12, 3))
        rect(s, shade, (foot[0]-3, foot[1]-2, 10, 2))
    # Breastplate bevels, tassets, belt clasp, chain mail.
    poly(s, shade, [(39, 47+y), (53, 46+y), (58, 55+y), (54, 68+y), (38, 68+y), (35, 54+y)])
    poly(s, armor, [(40, 49+y), (50, 48+y), (54, 54+y), (50, 62+y), (39, 61+y)])
    line(s, light, (39, 51+y), (49, 50+y), 2)
    line(s, light, (38, 53+y), (38, 58+y))
    poly(s, gold, [(46, 53+y), (49, 57+y), (46, 61+y), (43, 57+y)])
    rect(s, dark, (38, 63+y, 17, 4))
    rect(s, gold, (44, 63+y, 5, 4))
    for i in range(3):
        poly(s, armor, [(37+i*6, 67+y), (42+i*6, 67+y), (43+i*6, 73+y), (37+i*6, 72+y)])
        rect(s, light, (38+i*6, 68+y, 3, 1))
    # Sword arm / animated blade, gold cross guard and bright double edge.
    angle = -.9
    if state == "attack":
        angle = -2.2 + min(frame / 5, 1) * 3.0
    if state == "victory":
        angle = -1.8 + math.sin(t)*.06
    hand = (58, 58+y)
    if state == "propose":
        hand = (65, 65+y-5)
    elif state == "victory":
        hand = (65, 41+y)
        angle = -1.4 + math.sin(t)*.06
    poly(s, shade, [(52, 49+y), (58, 50+y), (63, 60+y), (hand[0], hand[1]+4), (55, 59+y)])
    rect(s, light, (54, 50+y, 5, 3))
    if state == "propose":
        line(s, armor, (57, 61+y), hand, 4)
        pygame.draw.circle(s, gold, (66, round(hand[1])-3), 3, 1)
        rect(s, (167, 251, 243), (65, hand[1]-7, 3, 3))
    elif state != "death":
        vx, vy = math.cos(angle), math.sin(angle)
        hx, hy = hand
        tip = (hx + vx*31, hy + vy*31)
        poly(s, armor, [(hx-vy*2, hy+vx*2), (tip[0]-vx*4-vy*2, tip[1]-vy*4+vx*2), tip,
                        (tip[0]-vx*4+vy*2, tip[1]-vy*4-vx*2), (hx+vy*2, hy-vx*2)])
        line(s, light, hand, tip)
        line(s, gold, (hx-vy*6, hy+vx*6), (hx+vy*6, hy-vx*6), 2)
        line(s, (93, 61, 44), hand, (hx-vx*7, hy-vy*7), 3)
        pygame.draw.circle(s, gold, (round(hx-vx*7), round(hy-vy*7)), 2)
    # Shield in foreground: heraldic enamel, raised rim, studs and crest.
    sx = 34 if state != "guard" else 58
    sy = 58+y
    poly(s, gold, [(sx-9, sy-4), (sx+8, sy-4), (sx+8, sy+9), (sx, sy+19), (sx-9, sy+9)])
    poly(s, (41, 83, 103), [(sx-6, sy-1), (sx+5, sy-1), (sx+5, sy+8), (sx, sy+15), (sx-6, sy+8)], None)
    line(s, light, (sx-7, sy-2), (sx+5, sy-2))
    line(s, gold, (sx-4, sy+5), (sx+3, sy+5), 2)
    line(s, gold, (sx, sy+1), (sx, sy+11), 2)
    # Visored helmet, cheek guard, eyes, steel highlights, plume.
    poly(s, shade, [(37, 28+y), (48, 25+y), (56, 30+y), (57, 44+y), (51, 50+y), (39, 47+y), (34, 37+y)])
    poly(s, armor, [(39, 29+y), (48, 27+y), (53, 31+y), (53, 37+y), (37, 37+y), (37, 33+y)], None)
    line(s, light, (39, 29+y), (47, 28+y), 2)
    rect(s, light, (38, 31+y, 2, 5))
    poly(s, (29, 44, 58), [(37, 38+y), (57, 36+y), (57, 41+y), (39, 43+y)], None)
    rect(s, (134, 234, 224), (48, 38+y, 5, 1))
    poly(s, armor, [(39, 43+y), (56, 41+y), (53, 47+y), (42, 48+y)])
    for x in (44, 47, 50):
        line(s, dark, (x, 44+y), (x, 46+y))
    poly(s, cape, [(41, 27+y), (42, 20+y), (49, 17+y), (57, 18+y), (64, 24+y), (55, 23+y), (48, 27+y)])
    line(s, (227, 115, 99) if state != "wedding" else gold, (45, 22+y), (55, 20+y))
    if state == "wedding":
        for x in (40, 47, 53):
            rect(s, gold, (x, 25+y, 3, 4))
        rect(s, (246, 221, 189), (40, 53+y, 14, 3))
    if state == "hurt":
        tint = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        tint.fill((100, 15, 10, 0))
        # Retain opaque silhouette while tinting only existing raster pixels.
        s.fill((80, 0, 0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    if state == "death":
        a = min(1, frame / 6)
        turned = pygame.transform.rotate(s, -90*a)
        turned = turned.subsurface(turned.get_bounding_rect()).copy()
        s = pygame.Surface((96, 96), pygame.SRCALPHA)
        s.blit(turned, (48-turned.get_width()//2, 89-turned.get_height()))
        if frame>4:
            line(s, light, (60,88), (87,88), 2)
            line(s, gold, (63,85), (63,90), 2)
    return s


def dragon(state, frame):
    s = pygame.Surface((256, 208), pygame.SRCALPHA)
    t = frame / 8 * math.tau
    moving = state == "walk"
    breath = round(math.sin(t)*2)
    dead = state == "death"
    yoff = round(frame * 3) if dead else breath
    # A rig drawn facing right; nose is at x230, tail starts x15.
    skin, shade, bright = (42, 105, 104), (27, 62, 76), (90, 156, 139)
    pale, dark, gold = (196, 189, 143), (14, 26, 37), (243, 194, 87)
    def p(color, points, edge=dark, width=1):
        poly(s, color, [(x, y+yoff) for x, y in points], edge, width)
    def l(color, a, b, w=1):
        line(s, color, (a[0], a[1]+yoff), (b[0], b[1]+yoff), w)
    tail = math.sin(t)*8
    p(shade, [(116, 153), (85, 151), (61, 166), (39, 166+tail), (20, 156+tail), (11, 136+tail),
              (15, 167+tail), (35, 182+tail), (66, 185), (112, 172)], width=2)
    l(bright, (27, 170+tail), (54, 175), 2)
    for x, y in [(31, 171+tail), (46, 177+tail), (63, 177), (80, 166), (95, 159)]:
        p(pale, [(x-4, y), (x, y-11), (x+4, y-2)])
    # Far wing membrane: finger bones frame ribbed, torn, shaded fabric.
    flap = math.sin(t)*5 if not dead else frame*2
    p((72, 55, 74), [(108, 136), (64, 98+flap), (37, 36+flap), (69, 48+flap), (97, 76+flap),
                     (111, 54+flap), (133, 32+flap), (137, 76), (160, 99), (154, 140)], width=2)
    p((123, 75, 91), [(113, 128), (74, 94+flap), (47, 47+flap), (81, 65+flap), (111, 97)], None)
    p((89, 61, 81), [(113, 120), (112, 75+flap), (130, 44+flap), (128, 91)], None)
    for a,b in [((112,134),(40,38+flap)), ((112,134),(130,36+flap)), ((112,134),(138,77))]:
        l(shade,a,b,4)
        l(bright,(a[0]-1,a[1]-2),(b[0]-1,b[1]-2),1)
    for i in range(5):
        l((146,86,101),(60+i*8,66+i*11+flap*.5),(87+i*5,90+i*6))
    p(pale, [(34, 36+flap), (37, 22+flap), (44, 39+flap)])
    # Back haunch and rear feet.
    stride = round(math.sin(t)*7) if moving else 0
    p(shade, [(93, 135), (79, 154), (83, 179), (73+stride, 191), (104+stride, 193), (112, 161)])
    for x in (77, 86, 95):
        p(pale, [(x+stride,190), (x+stride-3,196), (x+stride+5,195)])
    # Belly / torso and serpentine raised neck.
    p(skin, [(80, 143), (84, 122), (101, 106), (134, 106), (156, 124), (165, 147),
             (155, 172), (128, 185), (99, 179), (84, 164)], width=2)
    p(bright, [(92, 125), (105, 114), (130, 115), (140, 123), (112, 126), (96, 144)], None)
    p(shade, [(86, 147), (104, 156), (142, 150), (159, 144), (153, 168), (127, 179), (101, 173)], None)
    p(skin, [(140, 151), (142, 122), (157, 107), (164, 87), (182, 78), (197, 87),
             (188, 113), (179, 137), (164, 162)], width=2)
    p(bright, [(148, 139), (153, 120), (168, 109), (171, 93), (180, 90), (175, 119), (160, 146)], None)
    p(pale, [(174, 103), (188, 100), (179, 126), (169, 148), (153, 165), (129, 177),
             (131, 164), (154, 143), (165, 122)], None)
    for i in range(8):
        yy = 115+i*7
        xx = 174 - i*4.5
        l((119, 132, 116), (xx-6, yy), (xx+7, yy+2))
    # Pixel clusters on skin, generated with a fixed seed, never visual noise per frame.
    rng = random.Random(55)
    for _ in range(175):
        x,y = rng.randrange(82, 184), rng.randrange(100, 173)
        yy = y+yoff
        if 0 <= yy < 208 and s.get_at((x, yy))[:3] in (skin, shade, bright):
            c = bright if rng.random()<.55 else shade
            line(s, c, (x,yy), (x+2,yy+1))
    # Ordered overlapping scale plates: dark lower edges and single-pixel gleams.
    for row in range(9):
        for col in range(12):
            x=85+col*7+(3 if row%2 else 0)
            y=116+row*6+yoff
            if 0<=y<204 and s.get_at((x,y))[:3] in (skin,shade,bright):
                if all(s.get_at((xx,y+2))[:3] in (skin,shade,bright) for xx in (x,x+4)):
                    line(s,(29,78,85),(x,y+1),(x+2,y+3))
                    line(s,(29,78,85),(x+2,y+3),(x+4,y+1))
                    rect(s,(108,165,142) if col%3==0 else (68,131,121),(x+1,y,2,1))
    # Back spines.
    for x,y in [(87,128),(96,115),(110,109),(126,109),(144,120),(153,111),(159,96)]:
        p(pale, [(x-4,y), (x,y-13), (x+6,y+1)])
        l((237,216,161),(x,y-10),(x+2,y-2))
    # Near leg / claw: separate sweeping silhouette.
    claw = (frame*5 if frame<4 else (7-frame)*5) if state=="claw" else 0
    p(skin, [(145, 140), (159, 150), (164+claw, 169), (181+claw, 181),
             (179+claw, 193), (150, 193), (141, 180), (132, 158)], width=2)
    l(bright,(147,148),(153+claw,173),3)
    for x in (156,165,174):
        p(pale, [(x+claw,185), (x+claw+8,195), (x+claw-1,194)])
    # Head, jaw, horn fans, brow and readable glowing eye.
    headlow = frame*2 if dead else 0
    hy = -2 if state.startswith("windup") else headlow
    jaw = 0
    if state in ("fire", "roar", "windup_fire", "windup_roar"):
        jaw = (10+round(math.sin(t)*2)) if not state.startswith("windup") else frame//2
    p(shade, [(174, 91+hy), (195, 87+hy), (218, 99+hy), (232, 99+hy), (231, 109+hy+jaw),
              (215, 116+hy+jaw), (190, 109+hy+jaw)], width=2)
    if jaw:
        p((40,23,42), [(192,97+hy),(231,97+hy),(229,108+hy+jaw),(211,111+hy+jaw)],None)
        p((182,78,93), [(213,108+hy+jaw),(230,105+hy+jaw),(225,111+hy+jaw)],None)
    p(skin, [(163, 88+hy), (170, 70+hy), (189, 69+hy), (202, 79+hy), (209, 88+hy),
             (229, 89+hy), (237, 96+hy), (231, 102+hy), (206, 100+hy), (190, 95+hy), (181, 105+hy)], width=2)
    p(bright,[(171,77+hy),(184,74+hy),(199,83+hy),(191,87+hy),(175,85+hy)],None)
    l(bright,(209,91+hy),(230,93+hy),2)
    for x,y in [(173,82),(181,80),(186,92),(201,93),(210,95),(218,95)]:
        l((105,159,138),(x,y+hy),(x+2,y+hy))
    for a,b in [((153,58),(158,62)),((158,65),(164,69)),((183,57),(188,60))]:
        l((134,143,124),a,b)
    p(pale, [(169,76+hy),(151,64+hy),(147,46+hy),(155,54+hy),(180,71+hy)])
    p(pale, [(185,73+hy),(181,50+hy),(188,41+hy),(187,55+hy),(196,76+hy)])
    p((111,150,136), [(168,91+hy),(148,86+hy),(156,101+hy),(175,106+hy)])
    l(dark,(188,86+hy),(201,89+hy),3)
    if frame != 7 or state not in ("idle", "walk"):
        l(gold,(190,87+hy),(199,88+hy),2)
        rect(s,dark,(195,86+hy+yoff,2,4))
        rect(s,(255,242,174),(191,86+hy+yoff,2,1))
    l(dark,(229,95+hy),(232,95+hy),2)
    for x in (207,217,226):
        p((243,232,191),[(x,101+hy),(x+2,105+hy),(x+3,101+hy)],None)
    if state=="roar":
        for a,b in [((207,99),(202,93)),((208,100),(198,100)),((209,102),(201,107))]:
            l((222,208,176),a,b)
        rect(s,(248,145,157),(225,111+yoff,5,4))
    if state=="wedding":
        # A pixel veil, flower crown, necklace and blush, all on the same rig.
        p((202,220,211), [(170,68),(180,63),(195,68),(169,98),(153,125),(162,84)],None)
        for x,y in [(170,69),(177,66),(185,66),(192,70)]:
            pygame.draw.circle(s,(231,153,166),(x,y+yoff),4)
            rect(s,(255,229,183),(x-1,y-1+yoff,2,2))
        l(gold,(176,112),(165,135),2)
        p(gold,[(163,131),(167,136),(163,141),(159,136)])
        l((190,105,126),(196,96),(201,97),2)
    if dead:
        # Progressive collapse; feet stay on the floor and the long neck falls.
        a = frame / 7
        s2 = pygame.Surface((256,208),pygame.SRCALPHA)
        compressed = pygame.transform.scale(s,(256,round(208*(1-a*.54))))
        bounds=compressed.get_bounding_rect()
        s2.blit(compressed,(0,196-bounds.bottom))
        s=s2
        if frame>5:
            line(s,dark,(191,149),(199,153),2)
            line(s,dark,(191,153),(199,149),2)
    return s


def wedding_background():
    s=pygame.Surface((640,360))
    # Dusk garden with tiled distant mountains, clouds and hanging lights.
    for y in range(360):
        f=y/360
        rect(s,(int(38+28*f),int(56+32*f),int(82+26*f)),(0,y,640,1))
    rng=random.Random(731)
    for _ in range(110):
        x,y=rng.randrange(640),rng.randrange(10,150)
        rect(s,(151,181,184),(x,y,1,1))
    for off,c in [(0,(49,75,90)),(60,(34,66,77))]:
        poly(s,c,[(0,230),(0,180+off),(80,81+off),(150,190),(235,103+off),(340,207),
                  (423,86+off),(530,179),(590,130+off),(640,190),(640,280)],None)
    rect(s,(36,65,63),(0,246,640,114))
    for y in range(250,360,9):
        for x in range(-20,660,24):
            xx=x+(12 if y//9%2 else 0)
            rect(s,rng.choice([(69,89,85),(76,96,87),(62,82,80)]),(xx,y,22,7))
    poly(s,(178,143,115),[(180,360),(229,251),(401,251),(464,360)],None)
    # Ceremonial arch of stone and roses.
    for x in (218,411):
        rect(s,(193,187,153),(x,146,12,120))
        rect(s,(232,219,174),(x,146,3,120))
        rect(s,(168,177,143),(x-7,257,26,10))
    pygame.draw.arc(s,(209,205,166),(216,75,208,157),0,math.pi,12)
    for i in range(31):
        a=i/30*math.pi
        x,y=round(320+101*math.cos(a)),round(151-74*math.sin(a))
        pygame.draw.circle(s,(44,111,78),(x,y),7)
        pygame.draw.circle(s,rng.choice([(226,149,151),(243,211,171),(187,117,148)]),(x,y),4)
        rect(s,(255,230,187),(x-1,y-1,2,2))
    for x in (72,131,504,567):
        line(s,(115,125,107),(x,210),(x,267),2)
        for dx in (-7,0,7):
            pygame.draw.circle(s,(245,188,124),(x+dx,212+abs(dx)//2),3)
    for x in range(20,640,26):
        y=round(44+math.sin(x/640*math.pi)*24)
        line(s,(109,127,114),(x-26,y-3),(x,y))
        rect(s,(248,211,147),(x,y,3,5))
    # Foreground flowerbeds.
    for _ in range(210):
        x=rng.randrange(640)
        if 160<x<470:
            continue
        y=rng.randrange(272,358)
        line(s,(47,112,80),(x,y),(x,y-7))
        pygame.draw.circle(s,rng.choice([(219,141,154),(229,211,153),(156,180,211)]),(x,y-8),2)
    pygame.image.save(s,str(OUT/'wedding.png'))


def escape_background():
    s=pygame.Surface((640,360))
    rng=random.Random(101)
    for y in range(360):
        rect(s,(22+y//30,34+y//16,55+y//12),(0,y,640,1))
    pygame.draw.circle(s,(226,215,172),(120,61),22)
    pygame.draw.circle(s,(33,45,67),(129,56),21)
    for _ in range(130):
        rect(s,(149,169,177),(rng.randrange(640),rng.randrange(130),1,1))
    for offset,c in [(0,(40,65,78)),(50,(28,53,65))]:
        poly(s,c,[(0,269),(0,180),(70,111+offset),(167,188),(256,104+offset),
                  (363,196),(429,150),(550,236),(640,250),(640,300)],None)
    for x in range(0,430,21):
        y=rng.randrange(161,224)
        h=rng.randrange(40,92)
        line(s,(25,44,51),(x,y),(x,y+h),3)
        for j in range(5):
            poly(s,(29+j*2,60+j*2,64),[(x,y+j*11),(x-11-j*2,y+25+j*10),(x+11+j*2,y+25+j*10)],None)
    poly(s,(52,63,71),[(408,268),(421,164),(462,112),(519,86),(577,120),(640,152),(640,287)],None)
    for _ in range(230):
        x,y=rng.randrange(420,640),rng.randrange(128,269)
        rect(s,rng.choice([(69,78,81),(44,56,65),(84,87,81)]),(x,y,rng.randrange(2,8),2))
    pygame.draw.ellipse(s,(11,24,35),(464,149,137,202))
    rect(s,(11,24,35),(464,220,137,55))
    pygame.draw.arc(s,(101,111,103),(456,141,153,212),0,math.pi,7)
    rect(s,(40,60,58),(0,268,640,92))
    for y in range(272,360,8):
        for x in range(-10,640,22):
            xx=x+(11 if y//8%2 else 0)
            rect(s,rng.choice([(56,77,69),(67,84,72),(45,67,64)]),(xx,y,20,6))
    for _ in range(160):
        x,y=rng.randrange(640),rng.choice([264,265,268,342,350])
        line(s,(69,102,74),(x,y),(x+rng.randrange(-3,4),y-rng.randrange(2,9)))
    # A moonlit signpost, deliberately pointing away from the boss.
    rect(s,(99,84,63),(196,211,4,57))
    poly(s,(137,118,80),[(174,214),(181,207),(218,207),(218,222),(181,222)])
    line(s,(215,191,128),(183,214),(208,214),2)
    pygame.image.save(s,str(OUT/'escape.png'))


def wave_file(name, duration, fn):
    rate=22050
    samples=bytearray()
    for i in range(round(duration*rate)):
        t=i/rate
        v=max(-1,min(1,fn(t,duration)))
        samples.extend(struct.pack('<h',round(v*24000)))
    with wave.open(str(OUT/'audio'/f'{name}.wav'),'wb') as w:
        w.setparams((1,2,rate,0,'NONE','not compressed'))
        w.writeframes(samples)


def sound_assets():
    (OUT/'audio').mkdir(exist_ok=True)
    rng=random.Random(2)
    wave_file('sword',.22,lambda t,d: rng.uniform(-1,1)*.4*math.sin(math.pi*t/d)*(1-t/d))
    wave_file('hit',.24,lambda t,d: (rng.uniform(-.4,.4)+math.sin(t*520*math.exp(-t*10))*.7)*math.exp(-t*19))
    wave_file('guard',.35,lambda t,d: (math.sin(t*7300)+math.sin(t*4930))*.3*math.exp(-t*16))
    wave_file('heal',.65,lambda t,d: math.sin(math.tau*(450*t+550*t*t))*.25*math.sin(math.pi*t/d))
    wave_file('fire',.85,lambda t,d: (rng.uniform(-.5,.5)+math.sin(t*450)*.25)*math.sin(math.pi*t/d))
    wave_file('claw',.22,lambda t,d: rng.uniform(-1,1)*.6*math.exp(-t*12))
    # A local synthesized comic formant glide; deliberately a tiny monster "meow".
    wave_file('roar',.8,lambda t,d: sum(math.sin(math.tau*(530*t-220*t*t)*k)/k for k in (1,2,3,5))*.2*math.sin(math.pi*t/d))
    wave_file('victory',1.8,lambda t,d: math.sin(math.tau*[261.63,329.63,392,523.25][min(3,int(t*3))]*t)*.22*math.sin(math.pi*t/d))
    def music(t,d,wedding=False):
        chords = [(130.81,164.81,196),(110,130.81,164.81),(146.83,174.61,220),(98,123.47,146.83)]
        chord=chords[int(t//4)%4]
        pad=sum(math.sin(math.tau*f*t) for f in chord)*.035
        beat=t%(.25 if wedding else .5)
        note=chord[int(t*(4 if wedding else 2))%3]*(4 if wedding else 2)
        bell=math.sin(math.tau*note*beat)*math.exp(-beat*(9 if wedding else 7))*.09
        # Edge envelope avoids clicks on the seamlessly repeated 16-second loop.
        return (pad+bell)*min(1,t*3,(d-t)*3)
    wave_file('ambient',16,lambda t,d:music(t,d))
    wave_file('wedding',16,lambda t,d:music(t,d,True))


def main():
    OUT.mkdir(exist_ok=True)
    manifest={}
    specifications={
        'knight': (knight,(96,96),['idle','walk','attack','guard','hurt','death','propose','victory','wedding']),
        'dragon': (dragon,(256,208),['idle','walk','windup_claw','windup_fire','windup_roar','claw','fire','roar','death','wedding'])}
    for actor,(draw,size,states) in specifications.items():
        manifest[actor]={}
        for state in states:
            sheet=pygame.Surface((size[0]*8,size[1]),pygame.SRCALPHA)
            for i in range(8):
                sheet.blit(draw(state,i),(i*size[0],0))
            name=f'{actor}_{state}.png'
            pygame.image.save(sheet,str(OUT/name))
            manifest[actor][state]={'file':name,'size':size,'count':8,
                                    'fps':17.4 if actor=='knight' and state=='attack' else 8 if state=='death' else 10,
                                    'loop':state not in ('attack','death','propose')}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    wedding_background()
    escape_background()
    sound_assets()
    print('Generated 152 original raster frames, wedding/escape scenery and 10 WAVs.')


if __name__=='__main__':
    main()
    pygame.quit()
