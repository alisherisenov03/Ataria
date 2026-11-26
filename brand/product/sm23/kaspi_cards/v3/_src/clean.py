import cv2, numpy as np, sys
SRC='../kaspi_dl/img_%s.jpg'
IDS=['160418103','161349441','162539180','182253245','182253247','182253250','162539186','162539187','162539189']
# rect in 900-space: (x0,y0,x1,y1,mode,arg)  mode: 'v' bright>arg ; 'all' full rect ; 'fill' solid color
C={
1:[(0,0,688,146,'blk',0),(0,146,385,226,'blk',0),(385,146,610,214,'blk',0),(0,212,372,606,'blk',0),(0,600,372,705,'blk',0),(0,705,352,880,'blk',0),(330,795,375,850,'v',70),(395,204,612,228,'w',0)],
2:[(0,0,900,666,'blk',0),(15,655,95,705,'all',0),(475,655,555,705,'all',0),(440,600,462,730,'fill',0)],
3:[(55,112,288,242,'v',95),(462,368,618,438,'all',0),(305,500,725,598,'v',150)],
4:[(28,22,540,152,'v',100),(28,155,412,278,'v',135),(322,505,472,606,'v',115)],
5:[(30,15,800,105,'v',110)],
6:[(745,444,900,488,'v',150)],
7:[(25,22,636,198,'v',60),(28,222,335,478,'sv',60)],
8:[(32,28,490,200,'tx',0),(160,170,315,280,'v',170),(62,420,262,470,'v',150),(32,695,250,825,'tx',0),(295,812,835,892,'v',160)],
9:[(110,22,805,145,'tx',0)],
}
def mask_for(img,r):
    x0,y0,x1,y1,m,a=r; h,w=img.shape[:2]; s=w/900
    X0,Y0,X1,Y1=[int(round(v*s)) for v in (x0,y0,x1,y1)]
    M=np.zeros((h,w),np.uint8); sub=img[Y0:Y1,X0:X1]
    hsv=cv2.cvtColor(sub,cv2.COLOR_BGR2HSV)
    if m=='v': k=(hsv[...,2]>a)
    elif m=='w': k=(hsv[...,2]>45)&(hsv[...,1]<70)
    elif m=='sv': k=(hsv[...,2]>a)|((hsv[...,1]>110)&(hsv[...,2]>70))
    elif m=='tx':  # white or gold/cream text
        b,g,rr=[sub[...,i].astype(int) for i in range(3)]
        k=((hsv[...,2]>185)&(hsv[...,1]<60))|((rr>170)&(g>130)&(b<170)&(rr-b>45))
    else: k=np.ones(sub.shape[:2],bool)
    M[Y0:Y1,X0:X1]=k.astype(np.uint8)*255
    return M,(X0,Y0,X1,Y1),m
for n in map(int,sys.argv[1:]):
    img=cv2.imread(SRC%IDS[n-1]); s=img.shape[1]/900
    tot=np.zeros(img.shape[:2],np.uint8)
    for r in C.get(n,[]):
        M,(X0,Y0,X1,Y1),m=mask_for(img,r)
        if m=='blk':
            F=np.zeros(img.shape[:2],np.float32); F[Y0:Y1,X0:X1]=1
            F=np.clip(cv2.GaussianBlur(F,(0,0),4*s)*2,0,1)[...,None]
            # keep products: only darken where already dark-ish
            v=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)[...,2]
            Y1b=min(h0:=img.shape[0],Y1+int(12*s)); X1b=min(img.shape[1],X1+int(12*s))
            ring=np.concatenate([img[Y1:Y1b,X0:X1].reshape(-1,3),img[Y0:Y1,X1:X1b].reshape(-1,3)]) if (Y1b>Y1 or X1b>X1) else img[Y0:Y1,X0:X1].reshape(-1,3)
            col=np.percentile(img[Y0:Y1,X0:X1].reshape(-1,3),25,axis=0)
            col=np.minimum(col,30)
            img=(img*(1-F)+col[None,None,:]*F).astype(np.uint8) ; continue
        if m=='fill': img[Y0:Y1,X0:X1]=(6,6,6) if n==2 else img[Y0:Y1,X0:X1]; continue
        tot|=M
    tot=cv2.dilate(tot,np.ones((int(7*s),int(7*s)),np.uint8))
    out=cv2.inpaint(img,tot,int(9*s),cv2.INPAINT_TELEA) if tot.any() else img
    cv2.imwrite(f'c{n}.jpg',out,[cv2.IMWRITE_JPEG_QUALITY,95])
    print(n,'ok')
