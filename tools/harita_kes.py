import numpy as np
from PIL import Image
from scipy import ndimage as nd
SRC='/home/user/acipayam-site/static/img/acipayam-map.webp'
im=Image.open(SRC).convert('RGB'); a=np.asarray(im).astype(float)
lum=a.mean(2)
light=nd.binary_closing(lum>150,iterations=6)
lab,n=nd.label(light); m=lab==(1+int(np.argmax(nd.sum(light,lab,range(1,n+1)))))
m=nd.binary_fill_holes(m)
m=nd.binary_erosion(m,iterations=5)          # noktalı kırmızı sınırın içine çekil
f=nd.gaussian_filter(m.astype(float),4)       # kenarı yumuşat (pürüzleri al)
K=3
H,W=m.shape
F=np.asarray(Image.fromarray(f.astype('float32'),'F').resize((W*K,H*K),Image.BICUBIC))
inside=F>0.5
dout=nd.distance_transform_edt(~inside)
S=3.2*K
stroke=(~inside)&(dout<=S)
big=np.asarray(im.resize((W*K,H*K),Image.BICUBIC)).astype(np.uint8)
rgba=np.zeros((H*K,W*K,4),np.uint8)
din0=nd.distance_transform_edt(inside)
b=big.astype(int); red=(b[...,0]>b[...,1]+70)&(b[...,0]>b[...,2]+30)
yak=inside&(din0<=10*K)&red
yak=nd.binary_dilation(yak,iterations=2*K)&inside&(din0<=12*K)
lil=np.median(big[inside&(din0>20*K)&(~red)][::50],axis=0).astype(np.uint8)
big=big.copy(); big[yak]=lil
rgba[inside,:3]=big[inside]; rgba[inside,3]=255
rgba[stroke,:3]=(79,31,117); rgba[stroke,3]=255
# içte ince açık çizgi: sınıra canlılık
din=nd.distance_transform_edt(inside)
hl=inside&(din<=1.2*K)
rgba[hl,:3]=(0.55*rgba[hl,:3]+0.45*255).astype(np.uint8)
out=Image.fromarray(rgba,'RGBA').resize((W,H),Image.LANCZOS)
out=out.crop((137,107,1353,1548))
out.save('/home/user/acipayam-site/static/img/acipayam-harita.webp',quality=90,method=6)
bg=Image.new('RGBA',out.size,(255,255,255,255)); bg.alpha_composite(out); bg=bg.convert('RGB'); pass
print(out.size)
