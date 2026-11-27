
from PIL import Image, ImageDraw, ImageFont
import math
INTER="/usr/share/fonts/opentype/inter/"
P=(79,31,117); PD=(42,15,63); GO=(231,196,110); W=(255,255,255); CR=(248,242,250); PK=(247,208,222); PK2=(205,95,140); BR=(100,55,38); GR=(120,160,95)
S=512; K=4
def base(bg=P):
    N=S*K; im=Image.new("RGB",(N,N),bg); d=ImageDraw.Draw(im)
    for i in range(N):
        a=max(0,1-i/N)*22; d.line((0,i,N,i),fill=tuple(min(255,int(c+a)) for c in bg))
    return im,d
def petal_pts(cx,cy,ang,L,Wd):
    half=[]
    for k in range(0,91):
        t=k/90; x=L*(0.08+0.92*t)
        y=(Wd/2)*(math.sin(math.pi*0.5*min(1,t/0.62))**0.9 if t<0.62 else math.cos(math.pi*0.5*(t-0.62)/0.38)**0.55*0.98+0.02)
        half.append((x,y))
    tipx=L; notch=(L*0.93,0)
    right=half; left=[(x,-y) for x,y in reversed(half)]
    poly=[(L*0.08,0)]+right+[notch]+left
    ca,sa=math.cos(ang),math.sin(ang)
    return [((cx+x*ca-y*sa)*K,(cy+x*sa+y*ca)*K) for x,y in poly]
def flower(d,cx,cy,R,fill,center,out=None,ow=0,rot=-90,stam=True):
    for k in range(5):
        a=math.radians(rot+k*72); d.polygon(petal_pts(cx,cy,a,R,R*0.95),fill=fill,outline=out,width=ow*K if out else 0)
    r=R*0.2; d.ellipse(((cx-r)*K,(cy-r)*K,(cx+r)*K,(cy+r)*K),fill=center)
    if stam:
        for k in range(16):
            a=k*2*math.pi/16+0.1; L=R*(0.36 if k%2 else 0.44); x2,y2=cx+L*math.cos(a),cy+L*math.sin(a)
            d.line((cx*K,cy*K,x2*K,y2*K),fill=PK2 if center!=PK2 else BR,width=2*K); d.ellipse(((x2-6)*K,(y2-6)*K,(x2+6)*K,(y2+6)*K),fill=GO)
def fin(im): return im.resize((S,S),Image.LANCZOS)
def ctext(d,t,f,fill,y):
    bb=d.textbbox((0,0),t,font=f); d.text(((S*K-(bb[2]-bb[0]))/2-bb[0],y*K-bb[1]),t,font=f,fill=fill)

import base64, io, sys
from pathlib import Path
ACP = Path(__file__).resolve().parents[1]
def dal(pad=0.0):
    im,d=base(PD)
    sc=1-2*pad; o=S*pad
    T=lambda x,y:((o+x*sc)*K,(o+y*sc)*K)
    d.line(T(60,470)+T(450,70),fill=BR,width=round(18*K*sc)); d.line(T(265,265)+T(360,330),fill=BR,width=round(10*K*sc))
    flower(d,o+185*sc,o+300*sc,112*sc,CR,PK2,(220,190,200),2); flower(d,o+350*sc,o+165*sc,92*sc,PK,BR,(235,170,190),2,rot=-60)
    cx,cy,r=o+365*sc,o+335*sc,20*sc; d.ellipse(((cx-r)*K,(cy-r)*K,(cx+r)*K,(cy+r)*K),fill=PK2)
    d.polygon(petal_pts(o+115*sc,o+400*sc,math.radians(160),62*sc,40*sc),fill=GR)
    return im.resize((S,S),Image.LANCZOS)
if __name__ == "__main__":
    v = sys.argv[1]; big = dal(); mask = dal(0.1)
    for f in (ACP / "static/img").glob("uygulama*-*.png"): f.unlink()
    for n in (180, 192, 512): big.resize((n, n), Image.LANCZOS).save(ACP / f"static/img/uygulama{v}-{n}.png")
    mask.save(ACP / f"static/img/uygulama{v}-512m.png")
    b = io.BytesIO(); big.resize((128, 128), Image.LANCZOS).save(b, "PNG")
    (ACP / "static/img/favicon.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 128 128"><image width="128" height="128" xlink:href="data:image/png;base64,{base64.b64encode(b.getvalue()).decode()}"/></svg>')
