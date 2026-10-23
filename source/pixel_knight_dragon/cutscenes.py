import math
import pygame
from .settings import GROUND, GOLD, TEXT


class Cutscene:
    """Four timed, separately staged pixel cinematics; simulation stops on entry."""
    def __init__(self,kind,encounter,world,audio):
        self.kind,self.enc,self.world,self.audio=kind,encounter,world,audio
        self.time=0.
        self.flags=set()
        self.start_x=encounter.knight.x
        audio.music('wedding' if kind=='love' else 'ambient')

    def update(self,dt):
        self.time+=dt
        if self.kind=='love' and self.time>3.8:
            self.world.confetti(dt)
        if self.kind=='slayer' and .8<self.time<3:
            self.world.burst(530,235,GOLD,2,80)
        sound={'slayer':'victory','fallen':'roar','love':'heal','escape':'roar'}[self.kind]
        if self.time>.5 and 'sound' not in self.flags:
            self.audio.play(sound)
            self.flags.add('sound')

    def draw(self,s,ui):
        t,w,k,d=self.time,self.world,self.enc.knight,self.enc.dragon
        if self.kind=='love' and t>=3.8:
            self.wedding(s,ui)
        elif self.kind=='escape' and t>=2.8:
            self.exterior(s,ui)
        else:
            w.background(s)
            if self.kind=='slayer':
                w.actor(s,'dragon','death',max(0,t-.3),d.x,GROUND,d.facing)
                x=k.x+(min(t,2)*17 if k.x<d.x-75 else 0)
                w.actor(s,'knight','victory' if t>1.4 else 'idle',t,x,GROUND,1)
                if t>1.3:
                    ui.bubble(s,'Сокровища? Уже мои.',x,GROUND-109)
                if t>2:
                    for i in range(9):
                        phase=(t*.7+i*.11)%1
                        xx=530+(x-530)*phase
                        yy=235-60*math.sin(phase*math.pi)
                        pygame.draw.circle(s,GOLD,(int(xx),int(yy)),2)
            elif self.kind=='fallen':
                w.actor(s,'knight','death',t*.85,k.x,GROUND,k.facing)
                w.actor(s,'dragon','roar',t,d.x,GROUND,d.facing)
                if 1<t<4.8:
                    ui.bubble(s,'МЯУ. Следующий!',d.x,GROUND-151)
                ui.dim(s,min(92,int(t*15)))
            elif self.kind=='love':
                x=d.x-114
                w.actor(s,'knight','propose',t,x,GROUND,1)
                w.actor(s,'dragon','idle' if t<1.7 else 'wedding',t,d.x,GROUND,-1)
                if t<2:
                    ui.bubble(s,'Дракон, выйдешь за меня?',x+7,GROUND-109)
                else:
                    ui.bubble(s,'Да! Мяу!',d.x,GROUND-150)
                    w.heart(s,d.x-70,140-math.sin(t*3)*4,2)
            else:
                x=self.start_x-t*90
                w.actor(s,'dragon','roar',t,d.x,GROUND,-1)
                w.actor(s,'knight','walk',t,x,GROUND,-1)
                ui.bubble(s,'Я просто проверю выход!',max(115,x),GROUND-104)
        w.foreground(s,ui)
        # Shot borders make room for titles without replacing the actual scene.
        if t<3:
            pygame.draw.rect(s,(8,14,22),(0,0,640,13))
            pygame.draw.rect(s,(8,14,22),(0,347,640,13))
        title_time=6.8 if self.kind=='love' else 4.5 if self.kind=='escape' else 3.2
        if t>=title_time:
            ui.ending(s,self.kind,t)
        else:
            ui.panel(s,(368,332,258,23))
            ui.text(s,'Esc — пропустить кат-сцену',497,335,12,(211,222,213),True)
        # Short fade through warm light between proposal and ceremony.
        if self.kind=='love' and 3.45<t<4.15:
            a=int((1-min(1,abs(t-3.8)/.35))*220)
            veil=pygame.Surface((640,360),pygame.SRCALPHA)
            veil.fill((246,224,187,a))
            s.blit(veil,(0,0))

    def wedding(self,s,ui):
        w,t=self.world,self.time
        w.background(s,True)
        # Guests are miniature raster sprites, seated on each side of the aisle.
        for i,x in enumerate((105,148,503,548)):
            guest=w.res.sprite('knight','idle',t+i,1 if x<320 else -1)
            guest=pygame.transform.scale(guest,(58,58))
            s.blit(guest,(x-29,264-53))
        # Officiant behind the happy couple, liturgical book and lectern.
        w.actor(s,'knight','wedding',t,325,254,1)
        pygame.draw.polygon(s,(73,45,58),[(308,224),(323,228),(338,224),(338,239),(323,243),(308,239)])
        pygame.draw.line(s,GOLD,(323,229),(323,241))
        for i in range(3):
            pygame.draw.line(s,(212,201,160),(311,228+i*3),(320,230+i*3))
            pygame.draw.line(s,(212,201,160),(326,230+i*3),(335,228+i*3))
        w.actor(s,'dragon','wedding',t,434,GROUND,-1)
        w.actor(s,'knight','wedding',t,274,GROUND,1)
        # Wedding rings and floating hearts keep the ceremony animated.
        pygame.draw.circle(s,GOLD,(300,221),4,1)
        pygame.draw.circle(s,GOLD,(306,221),4,1)
        for i in range(6):
            phase=(t*.18+i*.18)%1
            w.heart(s,273+i*21+math.sin(t+i)*4,216-phase*90,1 if i%2 else 1.5)
        if t<6.8:
            ui.bubble(s,'Объявляю вас рыцарем и драконом!',320,30)
            ui.bubble(s,'Согласна. Мяу.',446,111)

    def exterior(self,s,ui):
        w,t=self.world,self.time
        s.blit(w.res.escape,(0,0))
        # The boss remains visible inside its cave, framed by the entrance.
        dragon=w.res.sprite('dragon','roar',t,-1)
        dragon=pygame.transform.scale(dragon,(128,104))
        s.blit(dragon,(461,161))
        x=390-(t-2.8)*57
        if x<-30:
            x=-30
        w.actor(s,'knight','walk',t*1.4,x,GROUND,-1)
        for i in range(5):
            p=(t*3+i*.2)%1
            pygame.draw.rect(s,(135,139,111),(round(x+14+p*36),round(GROUND-2-p*7),3,2))
        if t<7.7:
            ui.bubble(s,'Тактическое отступление!',max(140,x),145)
            ui.bubble(s,'Мяу?..',538,133)
