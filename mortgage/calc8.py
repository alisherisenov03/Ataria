def pmt(P,i,n): return P*i/(1-(1+i)**-n)
i=.07/12; idle=10e6*i; pr=10e6/120; A=pmt(10e6,i,120)
def run(kind,S,T,E=200_000):
    b=10e6; ip=0; m=0; paid=0; pays=[]
    while b>0.5:
        m+=1; x=b*i; ip+=x+idle
        base=(A-x) if kind=="ann" else pr
        extra=E if S<m<=S+T else 0
        princ=min(base+extra,b)
        pay=princ+x+idle; paid+=pay; pays.append(pay); b-=princ
    return m,ip,pays
for S in (24,36):
    for T in (24,36):
        ma,ia,pa=run("ann",S,T); md,idd,pd=run("diff",S,T)
        print(f"S{S} T{T}: ANN close {ma}m overpay {ia:,.0f} pay std {pa[0]:,.0f} extra {pa[S]:,.0f} | DIFF close {md}m overpay {idd:,.0f} pay std {pd[0]:,.0f}->{pd[S-1]:,.0f} extra {pd[S]:,.0f} | diff cheaper by {ia-idd:,.0f}")
