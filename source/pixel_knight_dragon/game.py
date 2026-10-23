import argparse
import os
from pathlib import Path
import sys
import pygame
from .combat import Encounter
from .cutscenes import Cutscene
from .resources import Resources, Audio
from .settings import WINDOW, WIDTH, HEIGHT, FPS, GROUND, GOLD, TEXT
from .world import World
from .ui import UI


class Game:
    def __init__(self):
        pygame.mixer.pre_init(22050,-16,1,512)
        pygame.init()
        pygame.display.set_caption('Рыцарь и Дракон · Забытый чертог')
        self.window=pygame.display.set_mode(WINDOW,pygame.RESIZABLE)
        self.canvas=pygame.Surface((WIDTH,HEIGHT))
        self.res=Resources()
        icon=self.res.sprite('knight','idle',0).subsurface((27,15,41,59)).copy()
        pygame.display.set_icon(icon)
        self.audio=Audio()
        self.world=World(self.res)
        self.ui=UI(self.res)
        self.enc=Encounter()
        self.scene=None
        self.state='menu'
        self.previous='menu'
        self.running=True
        self.selected=0
        self.seen=set()
        self.fullscreen=False
        self.audio.music('ambient')

    def start(self):
        self.enc=Encounter()
        self.world=World(self.res)
        self.scene=None
        self.state='play'
        self.audio.music('ambient')

    def command(self,action):
        if action in ('play','restart'):
            self.start()
        elif action=='quit':
            self.running=False
        elif action=='help':
            self.previous=self.state
            self.state='help'
        elif action=='back':
            self.state=self.previous
        elif action=='resume':
            self.state='play'
        elif action=='menu':
            self.state='menu'
            self.audio.music('ambient')

    def handle(self,event):
        if event.type==pygame.QUIT:
            self.running=False
        elif event.type==pygame.WINDOWFOCUSLOST and self.state=='play':
            self.state='pause'
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            self.command(self.ui.click(event.pos,self.window.get_size()))
        elif event.type==pygame.KEYDOWN:
            key=event.key
            if key==pygame.K_m:
                self.audio.toggle()
            elif key==pygame.K_F11:
                self.fullscreen=not self.fullscreen
                self.window=pygame.display.set_mode((0,0) if self.fullscreen else WINDOW,
                                                    pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE)
            elif self.state=='menu':
                if key in (pygame.K_DOWN,pygame.K_s):
                    self.selected=(self.selected+1)%3
                elif key in (pygame.K_UP,pygame.K_w):
                    self.selected=(self.selected-1)%3
                elif key in (pygame.K_RETURN,pygame.K_SPACE):
                    self.command(('play','help','quit')[self.selected])
                elif key==pygame.K_ESCAPE:
                    self.running=False
            elif self.state=='help':
                if key in (pygame.K_ESCAPE,pygame.K_RETURN):
                    self.command('back')
            elif self.state=='pause':
                if key in (pygame.K_ESCAPE,pygame.K_RETURN):
                    self.state='play'
            elif self.state=='scene':
                if key==pygame.K_ESCAPE:
                    self.scene.time=max(self.scene.time,8.6)
                elif key==pygame.K_RETURN and self.scene.time>8.5:
                    self.start()
            elif self.state=='play':
                if key==pygame.K_ESCAPE:
                    self.state='pause'
                else:
                    action={pygame.K_j:'attack',pygame.K_k:'guard',pygame.K_h:'heal',
                            pygame.K_e:'interact',pygame.K_SPACE:'jump'}.get(key)
                    if action:
                        self.enc.action(action)

    def update(self,dt,direction=None):
        if self.state!='pause':
            self.world.update(dt)
        if self.state=='play':
            if direction is None:
                keys=pygame.key.get_pressed()
                direction=int(keys[pygame.K_d] or keys[pygame.K_RIGHT])-int(keys[pygame.K_a] or keys[pygame.K_LEFT])
            self.enc.update(dt,direction)
            self.process_events()
            if self.enc.ending:
                self.scene=Cutscene(self.enc.ending,self.enc,self.world,self.audio)
                self.seen.add(self.enc.ending)
                self.state='scene'
        elif self.state=='scene':
            self.scene.update(dt)

    def process_events(self):
        w=self.world
        for kind,x,y,value in self.enc.events:
            if kind in ('hit_knight','hit_dragon','blocked'):
                blocked=kind=='blocked'
                color=(133,225,214) if blocked else (248,200,119) if kind=='hit_dragon' else (238,113,100)
                w.burst(x,y,color,18,110)
                w.text(x,y-20,f'−{value}' + ('  ЩИТ' if blocked else ''),color)
                w.shake=3 if blocked else 5
                self.audio.play('guard' if blocked else 'hit')
            elif kind=='heal':
                w.burst(x,y,(103,222,157),22,60)
                w.text(x,y-10,f'+{value} HP',(142,240,173))
                self.audio.play('heal')
            elif kind=='message':
                w.text(x,y,value,TEXT)
            elif kind in ('sword','guard','fire','claw','roar'):
                self.audio.play(kind)
                if kind=='fire':
                    w.shake=2
        self.enc.events.clear()

    def draw_play(self,s):
        w,k,d=self.world,self.enc.knight,self.enc.dragon
        w.background(s)
        w.telegraph(s,d)
        alpha=min(255,round(self.enc.age*240))
        w.actor(s,'dragon',d.state,d.anim_time,d.x,d.y,d.facing,alpha,d.hurt_time>0)
        w.actor(s,'knight',k.state,k.anim_time,k.x,k.y,k.facing,alpha,k.hurt_time>0)
        if k.attack_time and .10<.46-k.attack_time<.29:
            slash=pygame.Surface((128,96),pygame.SRCALPHA)
            pygame.draw.arc(slash,(248,224,170,210),(9,6,108,82),-.55,1.05,2)
            pygame.draw.arc(slash,(172,235,223,120),(13,9,101,76),-.4,.95,1)
            if k.facing<0:
                slash=pygame.transform.flip(slash,True,False)
            s.blit(slash,(round(k.x)-60,round(k.y)-75))
        if k.shield:
            pygame.draw.arc(s,(118,223,221),(round(k.x)-20,round(k.y)-53,40,51),-1.2,1.2,1)
        w.dragon_effect(s,d)
        w.foreground(s,self.ui)
        self.ui.hud(s,self.enc,w.time,paused=self.state=='pause')

    def draw(self):
        s,w,u=self.canvas,self.world,self.ui
        u.begin_frame()
        if self.state in ('menu','help'):
            w.background(s)
            w.actor(s,'dragon','idle',w.time,484,GROUND,-1)
            w.actor(s,'knight','idle',w.time,352,GROUND,1)
            u.dim(s,36)
            if self.state=='menu':
                u.menu(s,self.selected,self.seen)
            else:
                u.help(s)
        elif self.state in ('play','pause'):
            self.draw_play(s)
            if self.state=='pause':
                u.pause(s)
        elif self.state=='scene':
            self.scene.draw(s,u)
        if self.audio.muted:
            u.text(s,'Звук выключен',586,344,10,(205,215,207),True)
        win_w,win_h=self.window.get_size()
        scale=min(win_w/WIDTH,win_h/HEIGHT)
        # Nearest-neighbour only. Integer 2x at the default 1280x720.
        size=(max(1,int(WIDTH*scale)),max(1,int(HEIGHT*scale)))
        scaled=pygame.transform.scale(s,size)
        self.window.fill((5,10,17))
        ox=(win_w-size[0])//2
        oy=(win_h-size[1])//2
        if w.shake>0 and self.state=='play':
            ox+=w.rng.randint(-round(w.shake),round(w.shake))
            oy+=w.rng.randint(-round(w.shake),round(w.shake))
        self.window.blit(scaled,(ox,oy))
        # Keep the original pixel world sharp, but draw legible, antialiased
        # Cyrillic directly at the window's resolution (1280x720 by default).
        letters=u.text_layer if size==u.text_layer.get_size() else pygame.transform.smoothscale(u.text_layer,size)
        self.window.blit(letters,(ox,oy))
        pygame.display.flip()

    def run(self,frames=None):
        clock=pygame.time.Clock()
        n=0
        while self.running:
            dt=min(clock.tick(FPS)/1000,.1)
            for event in pygame.event.get():
                self.handle(event)
            self.update(dt)
            self.draw()
            n+=1
            if frames and n>=frames:
                break
        pygame.quit()


def smoke(output):
    """Render real screens through SDL, including all cinematics and local audio."""
    game=Game()
    output.mkdir(parents=True,exist_ok=True)
    def capture(name):
        game.draw()
        pygame.image.save(game.window,str(output/f'{name}.png'))
    capture('01-menu')
    game.command('help')
    capture('02-controls')
    game.start()
    for _ in range(120):
        game.update(1/60,1)
    capture('03-play')
    game.enc.knight.x=game.enc.dragon.x-112
    game.enc.action('attack')
    for _ in range(12):
        game.update(1/60,0)
    capture('04-combat')
    game.state='pause'
    capture('05-pause')
    for kind in ('slayer','fallen','love','escape'):
        game.start()
        game.enc.finish(kind)
        game.update(0,0)
        for _ in range(320):
            game.update(1/60,0)
        capture('06-'+kind+'-scene')
        for _ in range(250):
            game.update(1/60,0)
        capture('07-'+kind+'-ending')
        game.command('restart')
        assert game.state=='play' and game.enc.knight.health==100 and game.enc.dragon.health==200
    pygame.quit()
    print('PASS: menu, controls, combat, pause, all four animated endings and restart rendered.')


def main():
    parser=argparse.ArgumentParser(description='Рыцарь и Дракон — отдельная пиксельная игра')
    parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--capture-dir',type=Path,default=Path.cwd()/'screenshots')
    parser.add_argument('--frames',type=int)
    args=parser.parse_args()
    if args.smoke:
        smoke(args.capture_dir)
    else:
        Game().run(args.frames)
