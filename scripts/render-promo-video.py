#!/usr/bin/env python3
"""Fliqlo Ubuntu: deterministic 16s product film from actual project screenshots.

HTML-timeline-inspired frames, Pillow + FFmpeg. No proprietary Hyperframes assets,
no API calls, no external footage, no third-party music or packaged fonts.
"""
import subprocess, wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'docs'/'assets'; OUT=ROOT/'docs'/'media'
W,H,FPS,SECONDS=1280,720,24,16
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONTS={}
def f(sz,bold=False):
    key=(sz,bold)
    if key not in FONTS:FONTS[key]=ImageFont.truetype(BOLD if bold else FONT,sz)
    return FONTS[key]
def s(x):
    x=max(0,min(1,x));return x*x*(3-2*x)
def emerge(t,a,b):return s((t-a)/max(.001,b-a))
def vis(t,a,b,fade=.45):return min(emerge(t,a,a+fade),1-emerge(t,b-fade,b))
def text(img,st,xy,size=24,color=(238,241,250),alpha=255,bold=False,anchor='la'):
    if alpha<=0:return
    ImageDraw.Draw(img,'RGBA').text(xy,st,font=f(size,bold),fill=(*color,int(alpha)),anchor=anchor)
def box(img,b,r,fill,outline=None,width=1):
    ImageDraw.Draw(img,'RGBA').rounded_rectangle(tuple(map(int,b)),radius=r,fill=fill,outline=outline,width=width)
def bg(top,bottom):
    y=np.linspace(0,1,H)[:,None,None]
    arr=(np.array(top)[None,None,:]*(1-y)+np.array(bottom)[None,None,:]*y)
    arr=np.broadcast_to(arr,(H,W,3)).astype('uint8')
    return Image.fromarray(arr.copy(),'RGB').convert('RGBA')
BASE=[bg((10,13,21),(11,14,25)),bg((9,11,17),(7,8,14)),
      bg((16,20,34),(12,14,23)),bg((13,19,29),(9,11,19)),
      bg((9,12,21),(6,9,17))]
THEMES=['classic','ocean','rose','ivory','forest','amber']
PICS={name:Image.open(ASSETS/f'theme-{name}.png').convert('RGB') for name in THEMES}
SHOTS={name:Image.open(ASSETS/name).convert('RGB') for name in
 ('appearance-clock-face.png','appearance-background.png','appearance-dark.png')}
ACCENT={'classic':(208,214,238),'ocean':(125,211,247),'rose':(245,160,198),
        'ivory':(237,220,177),'forest':(133,236,184),'amber':(239,185,105)}

def logo(img,alpha=255):
    box(img,(70,43,108,81),8,(33,38,52,int(alpha)))
    text(img,'9',(79,50),18,alpha=alpha,bold=True)
    ImageDraw.Draw(img,'RGBA').line((70,62,108,62),fill=(5,8,15,alpha),width=2)
    text(img,'FLIQLO  /  UBUNTU',(124,61),15,(197,208,239),alpha,bold=True,anchor='lm')

def image_card(img,src,x,y,w,h,alpha=1,r=20):
    if alpha<=0:return
    layer=src.resize((int(w),int(h)),Image.Resampling.LANCZOS).convert('RGBA')
    mask=Image.new('L',layer.size,0)
    ImageDraw.Draw(mask).rounded_rectangle((0,0,w-1,h-1),radius=r,fill=int(alpha*255))
    layer.putalpha(mask)
    img.alpha_composite(layer,(int(x),int(y)))
    ImageDraw.Draw(img,'RGBA').rounded_rectangle((int(x),int(y),int(x+w),int(y+h)),radius=r,
            outline=(117,132,172,int(120*alpha)),width=2)

def scene0(t):
    im=BASE[0].copy();p=vis(t,0,3.1)
    logo(im,int(255*emerge(t,.1,.6)))
    text(im,'A DIFFERENT KIND OF IDLE SCREEN',(76,168),17,(181,192,231),int(255*emerge(t,.35,1)),True)
    text(im,'TIME.',(72,260+30*(1-emerge(t,.2,1))),110,alpha=int(255*emerge(t,.2,1)),bold=True)
    text(im,'BEAUTIFULLY',(76,380+26*(1-emerge(t,.55,1.35))),75,(190,199,242),int(255*emerge(t,.55,1.35)),True)
    text(im,'CONSIDERED.',(77,477+22*(1-emerge(t,.8,1.5))),76,alpha=int(255*emerge(t,.8,1.5)),bold=True)
    ImageDraw.Draw(im,'RGBA').line((80,630,1200,630),fill=(126,143,201,int(80*p)),width=1)
    text(im,'THE FLIP-CLOCK FEELING, REIMAGINED FOR GNOME.',(80,666),16,(154,163,193),int(255*p))
    return im

def scene1(t):
    im=BASE[1].copy();p=vis(t,3.0,7.15);logo(im,int(255*p))
    text(im,'01    THE ORIGINAL FEELING',(76,126),15,(173,190,240),int(255*p),True)
    text(im,'A moment of calm.',(73,190),61,alpha=int(255*emerge(t,3.2,3.95)),bold=True)
    text(im,'An iconic display. A seamless Ubuntu experience.',(78,242),20,(155,164,184),int(235*p))
    offset=40*(1-emerge(t,3.12,4.0))
    image_card(im,PICS['classic'],181,287+offset,918,395,p,22)
    text(im,'SPLIT-FLAP MOTION   /   NATIVE GTK   /   GNOME WAYLAND',(78,689),13,(156,166,195),int(225*p),True)
    return im

def scene2(t):
    im=BASE[2].copy();p=vis(t,7.0,11.6);logo(im,int(255*p))
    text(im,'02    YOUR CLOCK, YOUR COLORS',(76,124),15,(177,192,239),int(255*p),True)
    text(im,'One clock. Endless character.',(70,185),51,alpha=int(255*emerge(t,7.1,7.7)),bold=True)
    text(im,'Customize cards, digits and every shade in between.',(75,235),19,(160,170,196),int(245*p))
    names=['ocean','rose','ivory','forest','amber']
    idx=min(len(names)-1,max(0,int((t-7.1)/.8)))
    name=names[idx]
    image_card(im,PICS[name],66,284,817,379,p,18)
    for j,n in enumerate(names):
        y=298+j*70;active=j==idx
        box(im,(913,y,1201,y+58),12,(37,44,64,int((230 if active else 145)*p)),
            (144,161,204,int((155 if active else 60)*p)))
        box(im,(929,y+13,959,y+45),7,(*ACCENT[n],int(245*p)))
        text(im,n.title(),(975,y+18),20,(241,245,252) if active else (164,170,189),int(255*p),True)
        if active:text(im,'ACTIVE',(1124,y+22),11,(177,194,247),int(255*p),True)
    return im

def scene3(t):
    im=BASE[3].copy();p=vis(t,11.35,14.2,.35);logo(im,int(255*p))
    text(im,'03    PERSONAL TO THE LAST PIXEL',(76,121),15,(180,196,236),int(255*p),True)
    text(im,'Make it your own.',(73,193),62,alpha=int(255*p),bold=True)
    text(im,'Card colors. 20 backgrounds. One simple place to customize.',(76,246),20,(170,184,205),int(235*p))
    image_card(im,SHOTS['appearance-clock-face.png'],97,295,465,390,p,17)
    image_card(im,PICS['ocean'],605,331,561,315,p,17)
    text(im,'REAL NATIVE GTK SETTINGS',(710,674),12,(178,195,226),int(255*p),True)
    return im

def scene4(t):
    im=BASE[4].copy();p=vis(t,14.0,16.01,.3)
    image_card(im,PICS['classic'],413,62,456,251,p,16)
    text(im,'F L I Q L O',(642,390),62,(241,243,250),int(255*p),True,anchor='mm')
    text(im,'U B U N T U',(643,446),23,(177,193,240),int(255*p),True,anchor='mm')
    text(im,'TIME, BEAUTIFULLY CONSIDERED.',(642,518),24,(201,211,235),int(255*p),anchor='mm')
    text(im,'FREE · OPEN SOURCE · MADE FOR GNOME',(640,663),14,(150,165,201),int(230*p),True,anchor='mm')
    return im

SCENES=[(0,3.1,scene0),(3,7.15,scene1),(7,11.6,scene2),(11.35,14.2,scene3),(14.0,16.01,scene4)]
def render_at(t):
    active=[(a,b,fn) for a,b,fn in SCENES if a<=t<b]
    if not active:return BASE[4].convert('RGB')
    if len(active)==1:return active[0][2](t).convert('RGB')
    a,b,fn=active[0];c,d,gn=active[1]
    return Image.blend(fn(t),gn(t),s((t-c)/(b-c))).convert('RGB')

def sound(path):
    fs=24000;n=int(fs*SECONDS);tt=np.arange(n)/fs
    audio=np.zeros(n,dtype=float)
    for freq,amplitude in [(110,.022),(164.8,.015),(220,.01),(261.6,.007)]:
        audio+=amplitude*np.sin(2*np.pi*freq*tt)
    audio*=np.sin(np.pi*tt/SECONDS)**.8
    for at in [3.7,7.7,8.5,9.3,10.1,11.7,14.4]:
        pos=int(at*fs);u=np.arange(int(.08*fs))/fs
        audio[pos:pos+len(u)]+=.043*np.exp(-u*55)*np.sin(2*np.pi*140*u)
    with wave.open(str(path),'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(fs)
        wav.writeframes(np.int16(np.clip(audio,-1,1)*32767).tobytes())

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    poster=OUT/'fliqlo-ubuntu-poster.jpg';render_at(4.0).save(poster,quality=91,optimize=True)
    silent=OUT/'video.tmp.mp4';audio=OUT/'sound.tmp.wav'
    sound(audio)
    ffmpeg=['ffmpeg','-hide_banner','-loglevel','error','-y',
       '-f','rawvideo','-vcodec','rawvideo','-s',f'{W}x{H}','-pix_fmt','rgb24',
       '-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','veryfast',
       '-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',str(silent)]
    proc=subprocess.Popen(ffmpeg,stdin=subprocess.PIPE)
    try:
        for i in range(int(FPS*SECONDS)):
            proc.stdin.write(render_at(i/FPS).tobytes())
    finally:proc.stdin.close()
    if proc.wait():raise RuntimeError('Failed to encode video')
    final=OUT/'fliqlo-ubuntu-teaser.mp4'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(silent),'-i',str(audio),
        '-c:v','copy','-c:a','aac','-b:a','112k','-shortest','-movflags','+faststart',str(final)],check=True)
    silent.unlink();audio.unlink()
    assert final.stat().st_size>100_000
    print(f'Created {final} ({final.stat().st_size} bytes), poster {poster.stat().st_size} bytes')

if __name__=='__main__':main()
