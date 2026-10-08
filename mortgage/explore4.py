def pmt(P,r,n):
    i=r/12; return P*i/(1-(1+i)**-n)
# 36-month screenshot checks
p=pmt(10e6,.08,36); print("Zhenil2 36: ann10M",round(p,2),"+66666.67 =",round(p+10e6*.08/12,2),"int",round(p*36-10e6+10e6*.08/12*36,2))
print("Standard 36: ann 20M 7.5%",round(pmt(20e6,.075,36),2), "int",round(pmt(20e6,.075,36)*36-20e6,2))
print("Zhenil 8.5 interest-only:",20e6*.085/12, 20e6*.085/12*36)
# 120-month screenshot Zhenil2: 
p=pmt(10e6,.08,120); print("Zhenil2 120: ann10M",round(p,2),"+idle",round(p+66666.67,2))
i=.08/12;b=10e6;ip=0
for m in range(1,121):
    x=b*i; ip+=x; b-=p-x
    if m in (36,):
        print("36m: int on 10M part",round(ip,2),"bal",round(b,2),"idle int",round(66666.67*36,2),"total",round(ip+66666.67*36,2))
        ip36=ip;b36=b
target=4876705.20
print("target",target)
print("ip36 + housing?", round(target-ip36-66666.67*36,2))
# Standard 120: 
print("Std120 target 4685782.53; Std 36 target 13240152.28")
# solve for Std: what's 13240152.28 - 2396477?
print(13240152.28-(pmt(20e6,.075,36)*36-20e6))
# Zhenil 8.5% target 6709650.78 minus interest-only 5.1M
print(6709650.78-5.1e6)
def hl(P,s,n): return pmt(P,s,n)*n-P
for s in (.035,.04,.045,.05):
    for n in (84,120):
        print(s,n,"10M housing overpay",round(hl(10e6,s,n)),"; 20M",round(hl(20e6,s,n)))
