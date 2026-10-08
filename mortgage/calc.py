def pmt(P, r, n):
    i = r/12
    return P*i/(1-(1+i)**-n)

def schedule(P, phases):
    """phases: list of (months, annual_rate); annuity recalculated at phase start over remaining months."""
    total_n = sum(m for m,_ in phases); bal=P; paid=0; out=[]; left=total_n
    for m, r in phases:
        pay = pmt(bal, r, left); i=r/12
        for _ in range(m):
            bal -= pay - bal*i
        paid += pay*m; left -= m
        out.append((m, r, pay, max(bal,0)))
    return paid, out

def diff(P, r, n):
    bal=P; paid=0; first=None
    for k in range(n):
        pr=P/n; pay=pr+bal*r/12; paid+=pay; bal-=pr
        if first is None: first=pay; 
    return paid, first, pay

price=20_000_000; down=10_000_000; n=120
print("== Otbasy: 10M loan, 36m @8.5% then 84m @5% (annuity)")
for tail in (0.05,0.035):
    paid,ph=schedule(10_000_000,[(36,0.085),(84,tail)])
    print(tail, [(m,r,round(p),round(b)) for m,r,p,b in ph], "paid",round(paid),"overpay",round(paid-10_000_000))
paid,ph=schedule(10_000_000,[(120,0.085)]); print("flat 8.5%:",round(ph[0][2]),round(paid-10e6))
print("== Altyn: 20M @7% 120m, 10M deposit-guarantee held")
p=pmt(20e6,.07,120); print(round(p), round(p*120), round(p*120-20e6))
p10=pmt(10e6,.07,120); print("10M@7%:",round(p10), round(p10*120-10e6))
d=diff(20e6,.07,120); print("diff 20M:",[round(x) for x in d], round(d[0]-20e6))
# deposit income 0.1% simple
print("deposit income 10 y @0.1%:", round(10e6*((1+0.001/12)**120-1)))
# screenshot check
import math
lo,hi=0,.5
for _ in range(100):
    mid=(lo+hi)/2
    if pmt(20e6,mid,120)<174442: lo=mid
    else: hi=mid
print("rate implied by 174442 on 20M:",mid)
lo,hi=0,.5
for _ in range(100):
    mid=(lo+hi)/2
    if pmt(10e6,mid,120)<174442: lo=mid
    else: hi=mid
print("rate implied by 174442 on 10M:",mid)
