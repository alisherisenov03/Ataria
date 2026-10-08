import math
def pmt(P,r,n):
    i=r/12; return P*i/(1-(1+i)**-n)
def solve_n(P,r,pay):
    i=r/12; return -math.log(1-P*i/pay)/math.log(1+i)
print("n for 20M@7% annuity 176k:", solve_n(20e6,.07,176000))
for n in (120,144,180,240):
    d1=20e6/n+20e6*.07/12
    print(n,"ann",round(pmt(20e6,.07,n)),"diff first",round(d1))
# Altyn early closure after k months: interest paid + remaining balance
def ann_state(P,r,n,k):
    p=pmt(P,r,n); i=r/12; b=P; ip=0
    for _ in range(k):
        x=b*i; ip+=x; b-=p-x
    return p,ip,b
def diff_state(P,r,n,k):
    i=r/12; b=P; ip=0; pr=P/n; pays=[]
    for _ in range(k):
        x=b*i; ip+=x; b-=pr; pays.append(pr+x)
    return pays[0],pays[-1],ip,b
for n in (120,180):
  print("== Altyn 20M@7%, term",n)
  for k in (24,30,36):
    p,ip,b=ann_state(20e6,.07,n,k); print(" ann",k,"pay",round(p),"interest paid",round(ip),"balance",round(b),"balance-10M deposit",round(b-10e6))
    f,l,ip,b=diff_state(20e6,.07,n,k); print(" diff",k,"pay first/last",round(f),round(l),"interest paid",round(ip),"balance",round(b),"balance-10M",round(b-10e6))
# Otbasy variants
def sched(P,phases):
    tot=sum(m for m,_ in phases); b=P; paid=0; left=tot; res=[]
    for m,r in phases:
        p=pmt(b,r,left); i=r/12
        for _ in range(m): b-=p-b*i
        paid+=p*m; left-=m; res.append(round(p))
    return paid-P,res,b
print("== Otbasy")
for tail in (.05,.045,.035):
    for P in (10e6,20e6):
        o,res,b=sched(P,[(36,.085),(84,tail)]); print(f"P={P/1e6:.0f}M tail={tail}: overpay {o:,.0f} pays {res}")
# interest-only first 36 months then amortise 84m
for tail in (.05,.045,.035):
    io=10e6*.085/12*36; p=pmt(10e6,tail,84); print("IO 36m then",tail,"overpay",round(io+p*84-10e6), round(p))
# deposit repays at 36m: interest only 3y
print("3y interest on 10M @8.5%:", 10e6*.085*3)
# 3y at 8.5% annuity over 120 then deposit 10M closes remaining balance -> total interest
p=pmt(10e6,.085,120); i=.085/12; b=10e6; ip=0
for _ in range(36):
    x=b*i; ip+=x; b-=p-x
print("annuity10y, 36m interest",round(ip),"balance",round(b))
