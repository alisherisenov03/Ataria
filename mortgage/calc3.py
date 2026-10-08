def pmt(P,r,n):
    i=r/12; return P*i/(1-(1+i)**-n)
n=240
print("ann 7%",round(pmt(20e6,.07,n)),"ann 8.7%",round(pmt(20e6,.087,n)))
for r in (.07,.087):
  for k in (24,36):
    p=pmt(20e6,r,n); i=r/12; b=20e6; ip=0
    for _ in range(k):
        x=b*i; ip+=x; b-=p-x
    print(f"ANN r={r} k={k} pay {p:,.0f} interest {ip:,.0f} bal {b:,.0f} after-deposit {b-10e6:,.0f}")
  for k in (24,36):
    i=r/12; b=20e6; ip=0; pr=20e6/n; f=None
    for _ in range(k):
        x=b*i; ip+=x; f=f or pr+x; b-=pr; l=pr+x
    print(f"DIFF r={r} k={k} first {f:,.0f} last {l:,.0f} interest {ip:,.0f} bal {b:,.0f} after-deposit {b-10e6:,.0f}")
print("full 240m overpay diff7%:", sum(0 for _ in []) or round(20e6*.07/12*(n+1)/2))
