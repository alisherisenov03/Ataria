def pmt(P,r,n):
    i=r/12; return P*i/(1-(1+i)**-n)
for P in (10e6,20e6):
    p=pmt(P,.04,120); print(f"P={P/1e6:.0f}M 4% 120m: pay {p:,.2f} overpay {p*120-P:,.2f}")
# promzaim 36m @8.5% (annuity over 120) then refinance remaining into 4% housing loan 84m
i=.085/12; p=pmt(10e6,.085,120); b=10e6; ip=0
for _ in range(36):
    x=b*i; ip+=x; b-=p-x
p2=pmt(b,.04,84)
print("phase1 interest",round(ip),"balance",round(b),"phase2 pay",round(p2),"phase2 interest",round(p2*84-b),"total overpay",round(ip+p2*84-b))
# interest-only 36m @8.5% then 4% 84m on 10M
io=10e6*.085/12*36; p3=pmt(10e6,.04,84); print("IO then 4%/84m:",round(io+p3*84-10e6),round(p3))
# 3 more rates for completeness on 10M balance-based variant
for r in (.05,.045,.04,.035):
    p2=pmt(b,r,84); print(r,round(ip+p2*84-b))
