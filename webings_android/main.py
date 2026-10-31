"""The Path Of Webings — interface Android Kivy (vertical e responsiva)."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from functools import partial
from typing import Callable

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.utils import get_color_from_hex, platform
from kivy.properties import StringProperty, NumericProperty
from game_core import Player, GameEngine, PersistenceManager, ACTIVITIES, ROUTINES, MAX_ACTIONS, HAIRS, SKINS, STYLES, requirements_met, format_effects

BG='#0E1120'; PANEL='#1B2034'; CARD='#262C43'; ACCENT='#8979FF'; WHITE='#F7F7FF'; MUTED='#B7BDD5'; GREEN='#4ED5A0'; PINK='#F68EBD'; YELLOW='#F5C866'; PURPLE='#B49CFF'

def rgb(color): return get_color_from_hex(color)

def panel(widget, color=PANEL, radius=18):
    with widget.canvas.before:
        col=Color(*rgb(color)); shape=RoundedRectangle(pos=widget.pos,size=widget.size,radius=[dp(radius)])
    def update(*_): shape.pos=widget.pos; shape.size=widget.size
    widget.bind(pos=update,size=update)
    return widget

def txt(value, size=15, color=WHITE, bold=False, height=None, **kwargs):
    w=Label(text=str(value), font_size=sp(size), color=rgb(color), bold=bold, halign='left', valign='middle', size_hint_y=None, height=dp(height or max(27,size*1.7)), **kwargs)
    w.bind(width=lambda obj,val:setattr(obj,'text_size',(val-dp(4),None)))
    return w

def btn(value, callback, color=CARD, height=54, size=15):
    b=Button(text=value, size_hint_y=None,height=dp(height),background_normal='',background_down='',background_color=rgb(color),color=rgb(WHITE),font_size=sp(size),bold=True)
    b.bind(on_release=lambda *_:callback())
    return b

class Avatar(Widget):
    def __init__(self,skin,hair,style,**kwargs):
        super().__init__(**kwargs); self.skin=skin;self.hair=hair;self.style=style
        self.bind(pos=self.paint,size=self.paint);Clock.schedule_once(self.paint,0)
    def paint(self,*_):
        self.canvas.clear(); x,y=self.pos;s=min(self.width,self.height);cx=x+self.width/2;cy=y+self.height/2
        with self.canvas:
            Color(*rgb(CARD));Ellipse(pos=(cx-s*.48,cy-s*.48),size=(s*.96,s*.96))
            Color(*rgb(ACCENT));Ellipse(pos=(cx-s*.32,cy-s*.47),size=(s*.64,s*.37))
            if self.style in ('Longo','Cacheado'):
                Color(*rgb(self.hair));Ellipse(pos=(cx-s*.26,cy-s*.26),size=(s*.52,s*.67))
            Color(*rgb(self.skin));Ellipse(pos=(cx-s*.21,cy-s*.19),size=(s*.42,s*.52))
            Color(*rgb(self.hair))
            if self.style=='Raspado':Ellipse(pos=(cx-s*.19,cy+s*.26),size=(s*.38,s*.045))
            else:Ellipse(pos=(cx-s*.23,cy+s*.13),size=(s*.46,s*.20))
            Color(*rgb('#252331'))
            for dx in (-.085,.085):Ellipse(pos=(cx+s*dx-s*.018,cy+s*.05),size=(s*.036,s*.045))
            Color(*rgb('#945E62'));Line(points=[cx-s*.07,cy-s*.07,cx,cy-s*.10,cx+s*.07,cy-s*.07],width=max(1,s*.015))

class WebingsApp(App):
    title='The Path Of Webings'
    def build(self):
        Window.clearcolor=rgb(BG)
        if platform not in ('android','ios'):Window.size=(410,820)
        self.player=None;self.engine=None;self.modal=None
        self.skin=SKINS[2];self.hair='Preto';self.style='Curto'
        self.db=PersistenceManager(Path(self.user_data_dir)/'game_history.db')
        self.root_box=BoxLayout(orientation='vertical',padding=dp(12),spacing=dp(8))
        self.creator();return self.root_box
    def replace(self,widget):
        self.root_box.clear_widgets();self.root_box.add_widget(widget)
    def scroller(self):
        sc=ScrollView(do_scroll_x=False,bar_width=dp(3))
        body=BoxLayout(orientation='vertical',spacing=dp(12),padding=(dp(4),dp(8)),size_hint_y=None)
        body.bind(minimum_height=body.setter('height'));sc.add_widget(body)
        return sc,body
    def creator(self):
        sc,body=self.scroller()
        body.add_widget(txt('THE PATH OF WEBINGS',25,WHITE,True,52))
        body.add_widget(txt('Sua história começa aqui.',15,MUTED))
        card=panel(BoxLayout(orientation='vertical',spacing=dp(10),padding=dp(15),size_hint_y=None),PANEL)
        card.bind(minimum_height=card.setter('height'))
        self.avatar=Avatar(self.skin,HAIRS[self.hair],self.style,size_hint=(None,None),size=(dp(130),dp(130)))
        center=BoxLayout(size_hint_y=None,height=dp(140));center.add_widget(Widget());center.add_widget(self.avatar);center.add_widget(Widget());card.add_widget(center)
        card.add_widget(txt('IDENTIDADE',15,PURPLE,True))
        self.first=TextInput(hint_text='Nome',multiline=False,size_hint_y=None,height=dp(48),font_size=sp(16),background_color=rgb(CARD),foreground_color=rgb(WHITE),hint_text_color=rgb(MUTED),padding=[dp(12),dp(12)])
        self.last=TextInput(hint_text='Sobrenome',multiline=False,size_hint_y=None,height=dp(48),font_size=sp(16),background_color=rgb(CARD),foreground_color=rgb(WHITE),hint_text_color=rgb(MUTED),padding=[dp(12),dp(12)])
        card.add_widget(self.first);card.add_widget(self.last)
        card.add_widget(txt('Gênero',13,MUTED))
        self.gender=Spinner(text='Masculino',values=['Masculino','Feminino','Não-binário','Outro'],size_hint_y=None,height=dp(48),background_normal='',background_color=rgb(CARD));card.add_widget(self.gender)
        card.add_widget(txt('Tom de pele',13,MUTED))
        colors=GridLayout(cols=6,spacing=dp(5),size_hint_y=None,height=dp(45))
        for skin in SKINS:colors.add_widget(btn('●',partial(self.change_skin,skin),skin,45,23))
        card.add_widget(colors)
        card.add_widget(txt('Cor do cabelo',13,MUTED))
        self.hair_spinner=Spinner(text=self.hair,values=list(HAIRS),size_hint_y=None,height=dp(48),background_normal='',background_color=rgb(CARD))
        self.hair_spinner.bind(text=self.change_hair);card.add_widget(self.hair_spinner)
        card.add_widget(txt('Estilo do cabelo',13,MUTED))
        self.style_spinner=Spinner(text=self.style,values=STYLES,size_hint_y=None,height=dp(48),background_normal='',background_color=rgb(CARD))
        self.style_spinner.bind(text=self.change_style);card.add_widget(self.style_spinner)
        card.add_widget(txt('Traço de origem',13,MUTED))
        self.origin=Spinner(text='Nerd de TI',values=['Nerd de TI','Atleta da Turma','Extrovertido','Criador de Conteúdo'],size_hint_y=None,height=dp(48),background_normal='',background_color=rgb(CARD));card.add_widget(self.origin)
        body.add_widget(card)
        body.add_widget(btn('INICIAR NOVA VIDA',self.start,ACCENT,60,17))
        self.replace(sc)
    def change_skin(self,skin):self.skin=skin;self.avatar.skin=skin;self.avatar.paint()
    def change_hair(self,_,hair):self.hair=hair;self.avatar.hair=HAIRS[hair];self.avatar.paint()
    def change_style(self,_,style):self.style=style;self.avatar.style=style;self.avatar.paint()
    def start(self):
        a=self.first.text.strip();b=self.last.text.strip()
        if not a or not b or len(a)>35 or len(b)>35:return self.notice('Dados incompletos','Informe nome e sobrenome com até 35 caracteres.')
        self.player=Player(a,b,self.gender.text,self.skin,HAIRS[self.hair],self.style,self.origin.text)
        self.engine=GameEngine(self.player)
        self.player.log('Você nasceu. Uma nova história começa!')
        self.game()
    def game(self):
        p=self.player;assert p is not None
        sc,body=self.scroller()
        top=panel(BoxLayout(orientation='horizontal',padding=dp(10),spacing=dp(12),size_hint_y=None,height=dp(116)))
        top.add_widget(Avatar(p.pele,p.cabelo,p.estilo,size_hint=(None,None),size=(dp(88),dp(88))))
        col=BoxLayout(orientation='vertical');col.add_widget(txt(p.nome_completo,20,WHITE,True));col.add_widget(txt(f'{p.idade} ano(s) · {p.fase}',13,MUTED));col.add_widget(txt(f'◉ {p.seguidores:,} seguidores'.replace(',','.'),14,PURPLE,True));top.add_widget(col);body.add_widget(top)
        status=panel(BoxLayout(orientation='vertical',padding=dp(13),spacing=dp(6),size_hint_y=None,height=dp(230)))
        for key,label,color in [('hp','SAÚDE',GREEN),('disposicao','DISPOSIÇÃO',YELLOW),('felicidade','FELICIDADE',PINK),('dependencia','DEPENDÊNCIA',PURPLE)]:
            line=BoxLayout(size_hint_y=None,height=dp(24));line.add_widget(txt(label,12,MUTED,True));line.add_widget(txt(f'{getattr(p,key)}%',12,color,True,size_hint_x=.2));status.add_widget(line)
            bar=ProgressBar(max=100,value=getattr(p,key),size_hint_y=None,height=dp(9));status.add_widget(bar)
        body.add_widget(status)
        skills=panel(BoxLayout(orientation='vertical',padding=dp(12),size_hint_y=None,height=dp(72)))
        skills.add_widget(txt(f'FOCO {p.foco_efetivo}  ·  SANIDADE {p.sanidade_efetiva}',13,MUTED,True))
        skills.add_widget(txt(f'FORÇA {p.forca_efetiva}  ·  INTELIGÊNCIA {p.inteligencia_efetiva}',13,MUTED,True));body.add_widget(skills)
        body.add_widget(txt('✦ LINHA DO TEMPO',17,WHITE,True))
        for entry in p.historico_eventos[-25:][::-1]:
            lab=txt(entry,13,WHITE,height=0)
            lab.text_size=(Window.width-dp(75),None);lab.texture_update();lab.height=max(dp(52),lab.texture_size[1]+dp(20))
            frame=panel(BoxLayout(padding=dp(10),size_hint_y=None,height=lab.height),CARD,12);frame.add_widget(lab);body.add_widget(frame)
        body.add_widget(txt(f'ATIVIDADES · {p.acoes_ano}/{MAX_ACTIONS} neste ano',15,WHITE,True))
        grid=GridLayout(cols=2,spacing=dp(8),size_hint_y=None);grid.bind(minimum_height=grid.setter('height'))
        for name,spec in ACTIVITIES.items():
            available=not p.causa_morte and p.acoes_ano<MAX_ACTIONS and requirements_met(p,spec['requirements'])
            b=btn(name,partial(self.activity,name),CARD if available else '#343748',58,13);b.disabled=not available;grid.add_widget(b)
        body.add_widget(grid)
        self.replace(sc)
        footer=btn('+ IDADE  ·  DORMIR',self.sleep_menu,GREEN,64,18);footer.color=rgb(BG);self.root_box.add_widget(footer)
        if p.causa_morte:Clock.schedule_once(lambda _:self.death(),.15)
    def activity(self,name):
        try:self.engine.activity(name)
        except ValueError as e:return self.notice('Atividade indisponível',str(e))
        self.game()
    def popup(self,title,description,options):
        if self.modal:return
        outer=BoxLayout(orientation='vertical',spacing=dp(12),padding=dp(16))
        outer.add_widget(txt(title,20,WHITE,True,48))
        info=txt(description,14,MUTED,height=0);info.text_size=(min(Window.width-dp(85),dp(430)),None);info.texture_update();info.height=max(dp(60),info.texture_size[1]+dp(14));outer.add_widget(info)
        for name,callback,enabled in options:
            b=btn(name,lambda cb=callback:self.modal_action(cb),CARD,72,14);b.disabled=not enabled;outer.add_widget(b)
        outer.add_widget(Widget())
        content=panel(outer,PANEL)
        height=min(Window.height*.87,dp(150+len(options)*84)+info.height)
        self.modal=Popup(title='',separator_height=0,content=content,size_hint=(.94,None),height=height,auto_dismiss=False,background_color=(0,0,0,.75))
        self.modal.open()
    def modal_action(self,callback):
        if self.modal:self.modal.dismiss();self.modal=None
        callback()
    def notice(self,title,message):self.popup(title,message,[('ENTENDI',lambda:None,True)])
    def sleep_menu(self):
        if self.player.causa_morte:return
        self.popup('ROTINA NOTURNA','Como você deseja terminar este ano?',[(name+'\n'+format_effects(effects),partial(self.sleep,name),True) for name,effects in ROUTINES.items()])
    def sleep(self,routine):
        gate=self.engine.gate()
        if gate:
            title,passed,penalty=gate
            self.game()
            self.popup('DESAFIO · '+title,'Você superou o desafio!' if passed else 'Desafio não superado. '+format_effects(penalty),[('CONTINUAR',lambda:self.advance(routine) if not self.player.causa_morte else self.death(),True)])
        else:self.advance(routine)
    def advance(self,routine):
        event=self.engine.sleep(routine)
        self.game()
        if self.player.causa_morte:return
        if event:Clock.schedule_once(lambda _:self.event(event),.2)
    def event(self,event):
        p=self.player
        options=[]
        for option in event['options']:
            enabled=requirements_met(p,option.get('requirement',{}))
            options.append((option['text']+'\n'+format_effects(option.get('effects',{})),partial(self.choose,event,option),enabled))
        self.popup(event['title'],event['description'],options)
    def choose(self,event,option):
        self.engine.choose_event(event,option);self.game()
    def death(self):
        p=self.player
        if not p or not p.causa_morte or self.modal:return
        try:self.db.save(p);saved='Partida registrada no histórico.'
        except sqlite3.Error:saved='Não foi possível salvar a partida.'
        self.popup('CERTIDÃO DE ÓBITO',f'{p.nome_completo}\nIdade: {p.idade}\n{p.causa_morte}\nSeguidores: {p.seguidores}\n{p.badge}\nFases: {", ".join(p.fases_vividas)}\n{saved}',[('CRIAR NOVA VIDA',self.creator,True)])

if __name__=='__main__':WebingsApp().run()
