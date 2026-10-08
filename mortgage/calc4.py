r=.07; i=r/12; n=120
def pmt(P,i,n): return P*i/(1-(1+i)**-n)
A=pmt(10e6,i,n); idle=10e6*i
print("annuity part",round(A),"+ interest on deposit-backed 10M",round(idle),"=",round(A+idle))
print("total overpay annuity:",round(A*n-10e6+idle*n))
pr=10e6/n; b=10e6; tot=0; first=None
for k in range(1,n+1):
    pay=pr+b*i+idle; tot+=pay; first=first or pay; b-=pr; last=pay
print("diff first/last",round(first),round(last),"overpay",round(tot-20e6+10e6) if False else round(tot-10e6))
def early(kind,k):
    b=10e6; ip=0
    for m in range(k):
        x=b*i; ip+=x+idle
        b-= (A-x) if kind=="ann" else pr
    return ip,b
for kind in ("ann","diff"):
    for k in (12,24,36):
        ip,b=early(kind,k); print(kind,k,"interest paid",round(ip),"out of pocket to close (balance of 10M part)",round(b))
