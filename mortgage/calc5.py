i=.07/12; idle=10e6*i; n=120
def pmt(P,i,n): return P*i/(1-(1+i)**-n)
A=pmt(10e6,i,n); pr=10e6/n
def run(kind,E,K):
    b=10e6; ip=0; m=0
    while b>0.5:
        m+=1; x=b*i; ip+=x+idle
        princ=(A-x) if kind=="ann" else pr
        if m<=K: princ+=E
        princ=min(princ,b); b-=princ
    return m,ip
print("no prepay: ann",round(run("ann",0,0)[1]),"diff",round(run("diff",0,0)[1]))
for kind in ("ann","diff"):
    for E in (200_000,300_000):
        for K in (24,36):
            m,ip=run(kind,E,K)
            print(f"{kind} extra {E:,} x{K}: closes in {m} mo ({m/12:.1f} y), overpay {ip:,.0f}, extra paid {E*K:,}")
