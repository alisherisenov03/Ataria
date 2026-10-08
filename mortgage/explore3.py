def pmt(P,r,n):
    i=r/12; return P*i/(1-(1+i)**-n)
def ph1(P,r,pay,L):
    i=r/12;b=P;ip=0
    for _ in range(L):
        x=b*i; ip+=x; b-=pay-x
    return ip,b
target=4685782.53
pay=237403.54
for L in (36,):
  ip,b=ph1(20e6,.075,pay,L)
  for g in (0,.01,.02):
    dep=10e6*(1+g)**(L/12)
    rem=b-dep
    for s in (.035,.04,.045,.05):
      for n2 in (120-L,120):
        p=pmt(rem,s,n2); tot=ip+p*n2-rem
        if abs(tot-target)<20000: print("MATCH g",g,"s",s,"n2",n2,round(tot))
# interest-only promzaim variant standard? 
print("done")
# Annuity 8.5% on 20M, 120 months
for r in (.085,):
    for P in (10e6,20e6):
        p=pmt(P,r,120); print(P/1e6,"M @8.5% annuity:",round(p),"overpay full term",round(p*120-P))
# annuity on 20M @8.5%, deposit 10M repays at month L: interest paid & remaining
p=pmt(20e6,.085,120); i=.085/12; b=20e6; ip=0
for m in range(1,121):
    x=b*i; ip+=x; b-=p-x
    if m in (36,):
        print("m",m,"interest",round(ip),"bal",round(b),"bal-10M",round(b-10e6))
        rem=b-10e6
        for s in (.035,.04,.045,.05):
            p2=pmt(rem,s,84); print(" then",s,"84m pay",round(p2),"total overpay",round(ip+p2*84-rem))
# Altyn-like structure at 8.5%: interest on 20M, principal of 10M annuity
A=pmt(10e6,.085,120)+10e6*.085/12; print("alt-structure pay",round(A),"overpay",round(pmt(10e6,.085,120)*120-10e6+10e6*.085/12*120))
