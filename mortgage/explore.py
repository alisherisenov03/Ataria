def pmt(P,r,n):
    i=r/12; return P*i/(1-(1+i)**-n)
print("20M 7.5% 120:",pmt(20e6,.075,120)," 8%:",pmt(20e6,.08,120))
target=4685782.53
# Standard: annuity 20M @7.5%, L months, then deposit 10M repays principal, remaining rebuilt
for r in (.075,):
    p=pmt(20e6,r,120); i=r/12
    b=20e6; ip=0
    for L in range(1,121):
        x=b*i; ip+=x; b-=p-x
        if L in (12,24,36,48,60,72): print("L",L,"interest so far",round(ip),"bal",round(b),"bal-10M",round(b-10e6))
# interest only on 20M for L months then ...
# interest-only on 10M portion?: payment 237403 = ann on 20M. overpay 4.69M?
# try: total payments over 120 = pay*120 - 20M = ?
print(237403.54*120-20e6)
# guess: overpay = total interest where principal repaid by deposit at some month k: interest = sum over k months
p=pmt(20e6,.075,120); i=.075/12; b=20e6; ip=0
for k in range(1,121):
    x=b*i; ip+=x; b-=p-x
    if abs(ip-target)<30000: print("match k",k,ip)
# 8% row
p2=187994.26
for n in (120,):
    print("187994.26 implies rate on 20M 180m?")
import math
def solve_rate(P,pay,n):
    lo,hi=0,.5
    for _ in range(100):
        m=(lo+hi)/2
        if pmt(P,m,n)<pay: lo=m
        else: hi=m
    return m
for n in (120,150,180,240):
    print(n, solve_rate(20e6,187994.26,n), solve_rate(20e6,237403.54,n))
