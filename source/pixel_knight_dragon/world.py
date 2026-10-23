import math
import random
from dataclasses import dataclass
import pygame
from .settings import WIDTH, HEIGHT, GROUND, GOLD


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: tuple
    size: int = 2
    gravity: float = 100


class World:
    def __init__(self, resources):
        self.res = resources
        self.time = 0.
        self.rng = random.Random(719)
        self.particles = []
        self.floaters = []
        self.shake = 0.
        self.glows = {}
        self.embers = [(self.rng.randrange(640), self.rng.randrange(310), self.rng.uniform(.4,1.3)) for _ in range(32)]
        self.fire_layer = pygame.Surface((640,360),pygame.SRCALPHA)

    def glow(self, target, pos, color, radius):
        key = color, radius
        if key not in self.glows:
            s = pygame.Surface((radius*2,radius*2))
            for r in range(radius,0,-2):
                f=(1-r/radius)**2*.33
                pygame.draw.circle(s,tuple(round(c*f) for c in color),(radius,radius),r)
            self.glows[key]=s
        target.blit(self.glows[key],(int(pos[0])-radius,int(pos[1])-radius),special_flags=pygame.BLEND_RGB_ADD)

    def burst(self, x,y,color,count=14,speed=90):
        for _ in range(count):
            a=self.rng.uniform(-math.pi,0)
            v=self.rng.uniform(.3,1)*speed
            self.particles.append(Particle(x,y,math.cos(a)*v,math.sin(a)*v,
                                           self.rng.uniform(.3,.8),color,self.rng.choice((1,2,3))))

    def text(self,x,y,value,color):
        self.floaters.append([x,y,str(value),color,1.35])

    def update(self,dt):
        self.time+=dt
        self.shake=max(0,self.shake-dt*18)
        for p in self.particles:
            p.life-=dt
            p.x+=p.vx*dt
            p.y+=p.vy*dt
            p.vy+=p.gravity*dt
        self.particles=[p for p in self.particles if p.life>0]
        for f in self.floaters:
            f[1]-=dt*19
            f[4]-=dt
        self.floaters=[f for f in self.floaters if f[4]>0]

    def background(self,target,wedding=False):
        target.blit(self.res.wedding if wedding else self.res.cave,(0,0))
        t=self.time
        if not wedding:
            for x,y in ((107,171),(442,169)):
                self.glow(target,(x,y),(255,151,54),37+int(math.sin(t*5+x)*2))
                for i in range(4):
                    dx=math.sin(t*9+i*2+x)*2
                    pygame.draw.polygon(target,(255,137+25*i,52+i*24),
                                        [(x-3+dx,y+3),(x+3+dx,y+3),(x+math.sin(t*12+i)*2,y-6-i*2)])
            for x,y in ((550,166),(617,135),(413,235)):
                self.glow(target,(x,y),(41,205,223),22+int(math.sin(t*2+x)*3))
            for x,y,speed in self.embers:
                xx=(x+math.sin(t*.4+x)*6)%640
                yy=(y-t*7*speed)%300
                color=(154,149,113) if speed<.9 else (223,166,87)
                target.fill(color,(round(xx),round(yy),1,1))
            if math.sin(t*1.2)>0.92:
                for x,y in ((566,238),(587,221),(611,233)):
                    pygame.draw.line(target,(255,229,148),(x-2,y),(x+2,y))
                    pygame.draw.line(target,(255,229,148),(x,y-2),(x,y+2))

    def actor(self,target,actor,state,time,x,y,facing=1,alpha=255,flash=False):
        sprite=self.res.sprite(actor,state,time,facing)
        if alpha!=255 or flash:
            sprite=sprite.copy()
            if flash:
                sprite.fill((65,33,24,0),special_flags=pygame.BLEND_RGBA_ADD)
            sprite.set_alpha(alpha)
        origin=(48,88) if actor=='knight' else (128,196)
        shadow=pygame.Surface((80 if actor=='knight' else 158,12),pygame.SRCALPHA)
        pygame.draw.ellipse(shadow,(4,10,19,110),shadow.get_rect())
        target.blit(shadow,(round(x-shadow.get_width()/2),GROUND-4))
        target.blit(sprite,(round(x-origin[0]),round(y-origin[1])))

    def telegraph(self,target,d):
        if d.phase!='windup' or d.action=='roar':
            return
        box=d.attack_hitbox
        layer=pygame.Surface((640,360),pygame.SRCALPHA)
        color=(238,117,71) if d.action=='fire' else (232,181,102)
        pygame.draw.rect(layer,(*color,35),(box.x,GROUND-5,box.width,8))
        for x in range(box.left,box.right,10):
            pygame.draw.line(layer,(*color,130),(x,GROUND),(x+4,GROUND-4))
        target.blit(layer,(0,0))
        self.glow(target,(d.x+d.facing*74,d.y-100),(255,103,39),30)

    def dragon_effect(self,target,d):
        if d.phase!='active':
            return
        if d.action=='fire':
            layer=self.fire_layer
            layer.fill((0,0,0,0))
            x,y=d.x+d.facing*83,d.y-93
            for j,c in enumerate(((221,55,39,170),(255,126,43,225),(255,220,111,250))):
                length=(154-j*15)*min(1,d.phase_time*12)
                end=x+d.facing*length
                wave=math.sin(self.time*33+j)*5
                pygame.draw.polygon(layer,c,[(x,y-3),(end,y+20-j*4+wave),(end+d.facing*12,y+59-j*6),
                                             (x+d.facing*30,y+26)])
            for i in range(18):
                p=(self.time*2.8+i*.057)%1
                xx=x+d.facing*(p*165)
                yy=y+p*46+math.sin(p*28+i)*8
                pygame.draw.rect(layer,(255,206,86,200),(round(xx),round(yy),3,2))
            target.blit(layer,(0,0))
            self.glow(target,(x+d.facing*70,y+32),(255,107,37),60)
        elif d.action=='claw':
            layer=self.fire_layer
            layer.fill((0,0,0,0))
            for i in range(3):
                r=pygame.Rect(d.x-118 if d.facing<0 else d.x+25,d.y-69+i*8,95,49)
                pygame.draw.arc(layer,(255,224,158,220),r,.3,2.7,2)
            target.blit(layer,(0,0))

    def foreground(self,target,ui=None):
        for p in self.particles:
            target.fill(p.color,(round(p.x),round(p.y),p.size,p.size))
        for x,y,value,color,life in self.floaters:
            if ui is not None:
                size=14 if len(value)<12 else 12
                width=ui.measure(value,size)[0]
                ui.text(target,value,max(4+width/2,min(636-width/2,x)),y,size,color,True,
                        alpha=min(255,round(life*340)))
                continue
            font=self.res.font(13 if len(value)<12 else 11)
            img=font.render(value,True,color)
            img.set_alpha(min(255,round(life*340)))
            target.blit(img,(round(max(4,min(636-img.get_width(),x-img.get_width()/2))),round(y)))

    def confetti(self,dt):
        for _ in range(max(1,round(dt*120))):
            self.particles.append(Particle(self.rng.randrange(150,550),-2,self.rng.uniform(-16,16),
                                           self.rng.uniform(20,40),7,self.rng.choice(
                                               [(232,163,172),(242,209,125),(147,212,181)]),2,5))

    def heart(self,target,x,y,size=1):
        points=[(0,1),(1,0),(3,0),(4,1),(5,0),(7,0),(8,1),(8,3),(4,7),(0,3)]
        pygame.draw.polygon(target,(237,136,160),[(round(x+a*size),round(y+b*size)) for a,b in points])
