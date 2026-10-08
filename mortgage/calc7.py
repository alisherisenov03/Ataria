def pmt(P,r,n):
    i=r/12; return P*i/(1-(1+i)**-n)
# --- Otbasy: promzaim 20M @8.5% 36m interest-only, then housing 10M @5%
io=20e6*.085/12
print("promzaim interest-only pay",round(io,2),"x36 =",round(io*36))
for n in (84,120):
    p=pmt(10e6,.05,n); print(f"housing 10M@5% {n}m: pay {p:,.0f} overpay {p*n-10e6:,.0f} total {io*36+p*n-10e6:,.0f}")
for rent in (250_000,):
    for mo in (6,12):
        print("rent",mo,"mo =",rent*mo)
# alt B: annuity-style promzaim (principal on 10M only) then housing 10M@5%
i=.085/12; A=pmt(10e6,.085,120); b=10e6; ip=0
for _ in range(36):
    x=b*i; ip+=x; b-=A-x
idle=10e6*.085/12*36
print("alt B pay",round(A+10e6*i),"promzaim overpay",round(ip+idle),"balance",round(b))
p=pmt(10e6,.05,84); print("alt B + housing 10M@5% 84m total",round(ip+idle+p*84-10e6))
# --- Altyn diff 10y no prepay
r=.07; i=r/12; idle=10e6*i; pr=10e6/120
b=10e6; tot=0; first=None
for m in range(1,121):
    pay=pr+b*i+idle; tot+=pay; first=first or pay; last=pay; b-=pr
print("Altyn diff 10y: first",round(first),"last",round(last),"overpay",round(tot-10e6))
# --- Altyn: standard diff for S months, then +200k extra for T months
def run(S,T,E=200_000):
    b=10e6; ip=0; m=0; paid=[]
    while b>0.5:
        m+=1; x=b*i; ip+=x+idle
        princ=pr
        if S<m<=S+T: princ+=E
        princ=min(princ,b)
        paid.append(princ+x+idle + (E if (S<m<=S+T) else 0) if False else None)
        b-=princ
    return m,ip
for S in (24,36):
    for T in (24,36):
        m,ip=run(S,T); 
        # monthly payment during extra phase approx
        print(f"standard {S}m then +200k x{T}m: closes in {m} mo ({m/12:.1f}y) overpay {ip:,.0f}")
# pay amounts at start of extra phase
for S in (24,36):
    b=10e6-pr*S; print(S,"pay before extra",round(pr+b*i+idle),"during extra first month",round(pr+b*i+idle+200000))
