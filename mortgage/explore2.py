def pmt(P,r,n):
    i=r/12; return P*i/(1-(1+i)**-n)
def phase1(P,r,pay,L):
    i=r/12; b=P; ip=0
    for _ in range(L):
        x=b*i; ip+=x; b-=pay-x
    return ip,b
def solve(P,n,target_int):
    lo,hi=0.0001,.3
    for _ in range(100):
        m=(lo+hi)/2
        if pmt(P,m,n)*n-P<target_int: lo=m
        else: hi=m
    return m
for name,r,pay,target in (("Standard 7.5",.075,237403.54,4685782.53),("Zhenil2 8",.08,187994.26,4876705.20)):
    for L in (24,36,48):
        ip,b=phase1(20e6,r,pay,L)
        rem=b-10e6
        if rem<=0: print(name,L,"loan closed by deposit",round(ip)); continue
        need=target-ip
        s=solve(rem,120-L,need) if need>0 else None
        print(name,"L",L,"int1",round(ip),"bal",round(b),"rem after deposit",round(rem),"need2",round(need),"implied s",s)
# interest-only 8.5% on 20M 36m
print(20e6*.085/12, 20e6*.085/12*36)
# total months fully if payment 187994.26 @8%: loan term
import math
i=.08/12
print("n for 20M pay 187994.26:", -math.log(1-20e6*i/187994.26)/math.log(1+i))
