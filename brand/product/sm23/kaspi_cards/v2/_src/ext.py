import cv2, numpy as np, sys
def ext(src, out, H, top, bottom_crop=0.0, dx=0):
    im=cv2.imread(src); h,w=im.shape[:2]
    im=im[:int(h*(1-bottom_crop))]; h=im.shape[0]
    if 'm09' in src: im=im[:, :int(w*0.92)]
    s=H/h; im=cv2.resize(im,(int(w*s),H),interpolation=cv2.INTER_AREA); h,w=im.shape[:2]
    S=900*2; scale=2; im=cv2.resize(im,(w*scale,h*scale)); h,w=im.shape[:2]; top*=scale
    left=(S-w)//2+dx*scale; right=S-w-left; bot=S-h-top
    big=cv2.copyMakeBorder(im,max(top,0),max(bot,0),left,right,cv2.BORDER_REPLICATE)
    if top<0: big=big[-top:]
    big=big[:S]
    blur=cv2.GaussianBlur(big,(0,0),40)
    m=np.zeros((S,S),np.float32); y0=max(top,0); m[y0:y0+h, left:left+w]=1
    m=cv2.GaussianBlur(cv2.erode(m,np.ones((61,61))),(0,0),25)[...,None]
    res=(big*m+blur*(1-m)).astype(np.uint8)
    noise=np.random.default_rng(1).normal(0,2.2,res.shape)
    res=np.clip(res+noise*(1-m),0,255).astype(np.uint8)
    cv2.imwrite(out,res,[cv2.IMWRITE_JPEG_QUALITY,93])
for name,H,top,dx in [('m02_open',640,265,0),('m09_grinder',660,245,0),('m10_slicer',680,225,0),('m11b_noodles',680,225,0),('m12_blender',680,225,40),('m01_front',640,250,0),('m06_low',640,150,170)]:
    ext(f'ph/{name}.jpg',f'x_{name}.jpg',H,top,dx=dx)
