import math
import pygame
from .settings import GOLD, TEXT, MUTED, TEAL, INK


class UI:
    def __init__(self,res):
        self.res=res
        self.buttons=[]
        # World pixels remain 640x360. Text is rendered independently at 2x
        # resolution, so Cyrillic strokes are never reduced to a pixel font.
        self.text_layer=pygame.Surface((1280,720),pygame.SRCALPHA)

    def begin_frame(self):
        self.buttons.clear()
        self.text_layer.fill((0,0,0,0))

    def measure(self,text,size=12,bold=None):
        bold=size>=18 if bold is None else bold
        w,h=self.res.font(size*2,bold).size(text)
        return w/2,h/2

    def text(self,s,text,x,y,size=12,color=TEXT,center=False,alpha=255,bold=None):
        bold=size>=18 if bold is None else bold
        font=self.res.font(size*2,bold)
        img=font.render(text,True,color)
        px=round(x*2-img.get_width()/2) if center else round(x*2)
        py=round(y*2)
        shadow=font.render(text,True,(4,10,17))
        shadow.set_alpha(round(alpha*.8))
        self.text_layer.blit(shadow,(px+1,py+2))
        img.set_alpha(alpha)
        self.text_layer.blit(img,(px,py))
        return img.get_width()/2

    def panel(self,s,box,accent=GOLD):
        r=pygame.Rect(box)
        self.text_layer.fill((0,0,0,0),(r.x*2,r.y*2,r.w*2,r.h*2))
        layer=pygame.Surface(r.size,pygame.SRCALPHA)
        layer.fill((10,20,29,230))
        s.blit(layer,r)
        pygame.draw.rect(s,(65,80,85),r,1)
        for x,y in (r.topleft,(r.right-4,r.top),(r.left,r.bottom-4),(r.right-4,r.bottom-4)):
            pygame.draw.rect(s,accent,(x,y,4,4),1)

    def button(self,s,label,box,action,selected=False):
        r=pygame.Rect(box)
        mouse=pygame.mouse.get_pos()
        surface=pygame.display.get_surface()
        w,h=surface.get_size()
        scale=min(w/640,h/360)
        mouse=((mouse[0]-(w-640*scale)/2)/scale,(mouse[1]-(h-360*scale)/2)/scale)
        selected=selected or r.collidepoint(mouse)
        pygame.draw.rect(s,(53,71,74) if selected else (20,35,43),r)
        pygame.draw.rect(s,GOLD if selected else (74,89,90),r,1)
        height=self.measure(label,14,True)[1]
        self.text(s,label,r.centerx,r.y+(r.h-height)/2,14,GOLD if selected else TEXT,True,bold=True)
        if selected:
            self.text(s,'›',r.x+10,r.y+6,18,GOLD)
        self.buttons.append((r,action))

    def click(self,pos,window_size):
        w,h=window_size
        scale=min(w/640,h/360)
        p=((pos[0]-(w-640*scale)/2)/scale,(pos[1]-(h-360*scale)/2)/scale)
        return next((a for r,a in reversed(self.buttons) if r.collidepoint(p)),None)

    def health(self,s,actor,box,color):
        r=pygame.Rect(box)
        self.panel(s,r)
        self.text(s,actor.name,r.x+10,r.y+5,13,bold=True)
        self.text(s,f'{actor.health} / {actor.max_health}',r.right-78,r.y+7,12,MUTED)
        bar=pygame.Rect(r.x+10,r.y+27,r.w-20,8)
        pygame.draw.rect(s,(31,42,47),bar)
        fill=round((bar.w-2)*actor.health/actor.max_health)
        if fill:
            pygame.draw.rect(s,color,(bar.x+1,bar.y+1,fill,6))
            pygame.draw.line(s,tuple(min(255,c+35) for c in color),(bar.x+1,bar.y+1),(bar.x+fill,bar.y+1))
        for i in range(1,10):
            pygame.draw.line(s,(23,38,43),(bar.x+i*bar.w//10,bar.y+1),(bar.x+i*bar.w//10,bar.y+6))

    def hud(self,s,enc,time,paused=False):
        k,d=enc.knight,enc.dragon
        self.health(s,k,(14,12,213,44),(74,169,143))
        self.health(s,d,(413,12,213,44),(188,81,76))
        self.text(s,'ЗАБЫТЫЙ',320,17,10,GOLD,True)
        self.text(s,'ЧЕРТОГ',320,31,12,TEXT,True)
        self.panel(s,(14,308,612,38))
        for i in range(3):
            x=25+i*15
            c=(112,210,164) if i<k.zelka else (52,69,72)
            pygame.draw.rect(s,(175,158,111),(x+2,317,4,3))
            pygame.draw.rect(s,c,(x,321,8,12),1)
            pygame.draw.rect(s,c,(x+2,326,4,5))
        self.text(s,'H',76,319,12,MUTED)
        self.text(s,f'{k.gold} G',106,319,13,GOLD)
        self.text(s,'Щит поднят' if k.shield else 'K: щит',178,319,12,TEAL if k.shield else MUTED)
        self.text(s,'J: меч   E: предложение   Esc: пауза',320,319,12,TEXT)
        if paused:
            return
        if d.phase=='windup':
            label={'fire':'ОГОНЬ: прыгайте или отойдите','claw':'КОГТИ: прыгайте или поднимите щит','roar':'Змейка набирает воздух...'}[d.action]
            self.panel(s,(170,68,300,26),(230,142,92))
            self.text(s,label,320,73,13,(247,201,135),True)
        elif d.phase=='active' and d.action=='roar':
            self.bubble(s,'МЯУ!',d.x,d.y-153)
        if abs(k.x-d.x)<123:
            self.panel(s,(160,280,320,23))
            self.text(s,'E — предложить руку и сердце',320,283,13,(244,211,151),True)
        elif k.x<83:
            self.panel(s,(35,280,310,23))
            self.text(s,'Выход слева. E — сбежать',190,283,13,GOLD,True)
        elif enc.age<6:
            self.panel(s,(146,280,348,23))
            self.text(s,'A / D — идти    Пробел — прыгать    H — зелье',320,283,13,TEXT,True)

    def bubble(self,s,text,x,y):
        width=self.measure(text,13)[0]+20
        x=max(width/2+5,min(635-width/2,x))
        self.panel(s,(x-width/2,y,width,26))
        self.text(s,text,x,y+4,13,TEXT,True)
        pygame.draw.polygon(s,GOLD,[(int(x)-3,int(y)+26),(int(x)+3,int(y)+26),(int(x),int(y)+30)])

    def menu(self,s,selected=0,seen=()):
        self.panel(s,(28,30,286,294))
        self.text(s,'ПИКМИ 2000  /  ЗМЕЙКА',50,45,12,GOLD)
        self.text(s,'РЫЦАРЬ',49,69,33,TEXT)
        self.text(s,'И ДРАКОН',49,105,33,TEXT)
        pygame.draw.line(s,GOLD,(51,152),(287,152))
        self.text(s,'Сталь, пламя и неожиданный роман.',50,162,12,MUTED)
        for i,(label,action) in enumerate([('Играть','play'),('Управление','help'),('Выход','quit')]):
            self.button(s,label,(51,191+i*37,239,31),action,selected==i)
        self.text(s,f'Открыто концовок: {len(seen)} из 4',171,304,12,MUTED,True)
        self.text(s,'ЗАБЫТЫЙ ЧЕРТОГ',475,71,11,GOLD,True)
        self.text(s,'Enter — начать   M — звук   F11 — полный экран',320,338,12,MUTED,True)

    def help(self,s):
        self.panel(s,(80,25,480,310))
        self.text(s,'УПРАВЛЕНИЕ',320,43,21,GOLD,True)
        rows=[('A / D или стрелки','Двигаться влево и вправо'),('Пробел','Прыгнуть, чтобы избежать атаки'),
              ('J','Ударить мечом вблизи: 25 урона'),('K','Щит: следующий удар вдвое слабее'),
              ('H','Выпить зелье: +30 здоровья, всего 3 зелья'),('E','Сделать предложение рядом с драконом'),
              ('Выход слева','Выйти из пещеры и сбежать'),('Esc / M / F11','Пауза / звук / полный экран')]
        for i,(key,value) in enumerate(rows):
            self.text(s,key,98,81+i*24,12,TEAL,bold=True)
            self.text(s,value,225,81+i*24,12,TEXT)
        self.text(s,'Метка на земле предупреждает об атаке дракона.',320,275,12,GOLD,True)
        self.button(s,'Назад',(235,298,170,27),'back')

    def pause(self,s):
        self.dim(s,160)
        self.panel(s,(192,82,256,193))
        self.text(s,'ПАУЗА',320,100,24,GOLD,True)
        for i,(label,action) in enumerate([('Продолжить','resume'),('Начать заново','restart'),('Главное меню','menu')]):
            self.button(s,label,(215,142+i*39,210,31),action)

    def dim(self,s,alpha):
        layer=pygame.Surface((640,360),pygame.SRCALPHA)
        layer.fill((5,11,20,alpha))
        s.blit(layer,(0,0))
        self.text_layer.fill((255,255,255,255-alpha),special_flags=pygame.BLEND_RGBA_MULT)

    def ending(self,s,kind,time):
        titles={'slayer':'УБИЙЦА ДРАКОНА','fallen':'ПИКМИ НЕ ВЫЖИЛ','love':'ЛЮБОВЬ ПОБЕДИЛА','escape':'ТРУСЛИВЫЙ ПИКМИ'}
        subtitles={'slayer':'+500 золота · у сокровищ новый хозяин.',
                   'fallen':'Змейка поставила точку. Мяу.',
                   'love':'Пока смерть не разлучит… или следующий квест.',
                   'escape':'Иногда лучшие доспехи — быстрые ноги.'}
        self.panel(s,(80,15,480,76))
        self.text(s,'КОНЦОВКА',320,23,12,GOLD,True)
        self.text(s,titles[kind],320,42,22,TEXT,True)
        self.text(s,subtitles[kind],320,70,12,MUTED,True)
        if time>8.5:
            self.button(s,'Начать заново',(135,310,182,32),'restart')
            self.button(s,'Главное меню',(327,310,178,32),'menu')
            self.text(s,'Enter — начать заново',320,343,11,MUTED,True)
