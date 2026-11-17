"""KartIQ divide-and-conquer checks: Merge Sort, Quick Sort, Binary Search, Strassen."""
import math, random, json, sys
sys.setrecursionlimit(20000)
random.seed(2026)
OUT = {}

# ---------------- Module 1: stable merge sort with trace
def merge_sort(a, trace, depth=0, cnt=None):
    n = len(a)
    if n <= 1: return a
    mid = n // 2
    L = merge_sort(a[:mid], trace, depth + 1, cnt)
    R = merge_sort(a[mid:], trace, depth + 1, cnt)
    out, i, j, c = [], 0, 0, 0
    while i < len(L) and j < len(R):
        c += 1
        if L[i][0] <= R[j][0]:          # <= : left (earlier arrival) wins ties -> stable
            out.append(L[i]); i += 1
        else:
            out.append(R[j]); j += 1
    out += L[i:] + R[j:]
    trace.append((list(L), list(R), list(out), c)); cnt[0] += c
    return out
orders = [(105,"O1"),(102,"O2"),(105,"O3"),(101,"O4"),(102,"O5"),(103,"O6")]
tr, cnt = [], [0]
res = merge_sort(orders, tr, 0, cnt)
fm = lambda l: "[" + ", ".join("%s:%d"%(o,t) for t,o in l) + "]"
print("== Module 1: merge sort trace (every merge) ==")
for k,(L,R,o,c) in enumerate(tr,1):
    print("merge %d: %s + %s -> %s  (%d comparisons)"%(k,fm(L),fm(R),fm(o),c))
print("sorted:", fm(res), " total comparisons =", cnt[0])
OUT["m1"] = [[fm(L),fm(R),fm(o),c] for L,R,o,c in tr]; OUT["m1_total"]=cnt[0]; OUT["m1_sorted"]=fm(res)
n=10_000_000; lg=math.log2(n)
print("n=1e7: log2 n = %.4f ; worst comparisons n*log2n - n + 1 = %.4e ; best ~ (n/2)log2 n = %.4e"%(lg, n*lg-n+1, n/2*lg))
print("memory: 1e7 orders x 16 B = %d MB ; merge buffer another %d MB"%(n*16//10**6, n*16//10**6))
OUT["m1_num"]={"lg":lg,"worst":n*lg-n+1,"best":n/2*lg}
# verify formula on powers of two
for k in (4,8,10):
    N=2**k; a=[(random.random(),i) for i in range(N)]; c=[0]; merge_sort(a,[],0,c)
    assert c[0] <= N*math.log2(N)-N+1
# ---------------- Module 2: Quick sort (Hoare partition, first pivot) trace
def hoare_trace(a):
    a=list(a); p=a[0]; i,j=0,len(a); steps=[("pivot = %d"%p, list(a))]
    while True:
        i+=1
        while i<len(a) and a[i]<p: i+=1
        j-=1
        while a[j]>p: j-=1
        steps.append(("i stops at index %d (%d >= pivot), j stops at index %d (%d <= pivot)"%(i,a[i] if i<len(a) else -1,j,a[j]), list(a)))
        if i>=j: break
        a[i],a[j]=a[j],a[i]; steps.append(("swap a[%d] and a[%d]"%(i,j), list(a)))
    a[0],a[j]=a[j],a[0]; steps.append(("i >= j : swap pivot with a[%d] -> pivot in final place (index %d)"%(j,j), list(a)))
    return a,j,steps
sc=[42,17,63,8,55,29]
a,pos,steps=hoare_trace(sc)
print("\n== Module 2: one Hoare partition on", sc, "==")
for s,l in steps: print("%-78s %s"%(s,l))
OUT["m2"]=[[s,str(l)] for s,l in steps]; OUT["m2_pos"]=pos
def qs(a,lo,hi,cnt,mode):
    if lo>=hi: return
    if mode=="m3":
        mid=(lo+hi)//2
        trio=sorted([(a[lo],lo),(a[mid],mid),(a[hi],hi)]); cnt[0]+=3
        k=trio[1][1]; a[lo],a[k]=a[k],a[lo]
    p=a[lo]; i,j=lo,hi+1
    while True:
        i+=1
        while i<=hi and (cnt.__setitem__(0,cnt[0]+1) or a[i]<p): i+=1
        j-=1
        while (cnt.__setitem__(0,cnt[0]+1) or a[j]>p): j-=1
        if i>=j: break
        a[i],a[j]=a[j],a[i]
    a[lo],a[j]=a[j],a[lo]
    qs(a,lo,j-1,cnt,mode); qs(a,j+1,hi,cnt,mode)
print("\n== Quick sort comparisons on NEARLY SORTED data (1% of neighbours swapped) ==")
print("%6s %14s %12s %14s %12s"%("n","first pivot","n(n-1)/2","median-of-3","n*log2 n"))
rows=[]
for n in (500,1000,2000,4000):
    base=list(range(n))
    for _ in range(max(1,n//100)):
        k=random.randrange(n-1); base[k],base[k+1]=base[k+1],base[k]
    c1=[0]; a=list(base); qs(a,0,n-1,c1,"first"); assert a==sorted(base)
    c2=[0]; a=list(base); qs(a,0,n-1,c2,"m3"); assert a==sorted(base)
    rows.append([n,c1[0],n*(n-1)//2,c2[0],int(n*math.log2(n))])
    print("%6d %14d %12d %14d %12d"%tuple(rows[-1]))
OUT["m2_rows"]=rows
n=100000
print("n=100000: worst n(n-1)/2 = %d ; best/median-of-3 ~ n log2 n = %d"%(n*(n-1)//2,int(n*math.log2(n))))
OUT["m2_100k"]=[n*(n-1)//2,int(n*math.log2(n))]
# ---------------- Module 3: binary search
def bs_plain(a,key):
    lo,hi,c=0,len(a)-1,0
    while lo<=hi:
        mid=(lo+hi)//2; c+=1
        if a[mid]==key: return mid,c
        elif a[mid]<key: lo=mid+1
        else: hi=mid-1
    return -1,c
def bs_first(a,key):
    lo,hi,ans,c=0,len(a)-1,-1,0
    while lo<=hi:
        mid=(lo+hi)//2; c+=1
        if a[mid]==key: ans=mid; hi=mid-1      # keep looking LEFT
        elif a[mid]<key: lo=mid+1
        else: hi=mid-1
    return ans,c
ts=[t for t,_ in res]
print("\n== Module 3: sorted timestamps", ts, "==")
b3=[]
for key in (102,105,101,104):
    p=bs_plain(ts,key); f=bs_first(ts,key)
    print("key %d: plain -> index %s (%d cmp) | first-occurrence -> index %s (%d cmp)"%(key,p[0],p[1],f[0],f[1]))
    b3.append([key,p[0],p[1],f[0],f[1]])
OUT["m3"]=b3
print("max comparisons n=1e7:", math.floor(math.log2(10**7))+1)
for _ in range(500):
    arr=sorted(random.randint(0,30) for _ in range(random.randint(0,40))); k=random.randint(-1,31)
    assert bs_first(arr,k)[0]==(arr.index(k) if k in arr else -1)
# ---------------- Module 4: Strassen
A=[[1,7],[3,5]]; B=[[1,3],[7,5]]
a11,a12,a21,a22=A[0][0],A[0][1],A[1][0],A[1][1]; b11,b12,b21,b22=B[0][0],B[0][1],B[1][0],B[1][1]
M1=(a11+a22)*(b11+b22); M2=(a21+a22)*b11; M3=a11*(b12-b22); M4=a22*(b21-b11)
M5=(a11+a12)*b22; M6=(a21-a11)*(b11+b12); M7=(a12-a22)*(b21+b22)
C=[[M1+M4-M5+M7,M3+M5],[M2+M4,M1-M2+M3+M6]]
conv=[[sum(A[i][k]*B[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
print("\n== Module 4: Strassen on the 2x2 sample ==")
print("M1..M7 =",M1,M2,M3,M4,M5,M6,M7); print("Strassen C =",C," conventional C =",conv, " equal:",C==conv)
OUT["m4"]=[M1,M2,M3,M4,M5,M6,M7]; OUT["m4_C"]=C
def madd(X,Y,s=1): return [[x+s*y for x,y in zip(r,q)] for r,q in zip(X,Y)]
def conv_mul(X,Y,cnt):
    n=len(X); cnt[0]+=n**3
    return [[sum(X[i][k]*Y[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
def strassen(X,Y,cnt,cut=1):
    n=len(X)
    if n<=cut: return conv_mul(X,Y,cnt)
    h=n//2
    sub=lambda M,r,c:[row[c:c+h] for row in M[r:r+h]]
    X11,X12,X21,X22=sub(X,0,0),sub(X,0,h),sub(X,h,0),sub(X,h,h)
    Y11,Y12,Y21,Y22=sub(Y,0,0),sub(Y,0,h),sub(Y,h,0),sub(Y,h,h)
    m1=strassen(madd(X11,X22),madd(Y11,Y22),cnt,cut); m2=strassen(madd(X21,X22),Y11,cnt,cut)
    m3=strassen(X11,madd(Y12,Y22,-1),cnt,cut); m4=strassen(X22,madd(Y21,Y11,-1),cnt,cut)
    m5=strassen(madd(X11,X12),Y22,cnt,cut); m6=strassen(madd(X21,X11,-1),madd(Y11,Y12),cnt,cut)
    m7=strassen(madd(X12,X22,-1),madd(Y21,Y22),cnt,cut)
    C11=madd(madd(m1,m4),madd(m5,m7,-1),-1); C12=madd(m3,m5); C21=madd(m2,m4); C22=madd(madd(m1,m2,-1),madd(m3,m6))
    return [r1+r2 for r1,r2 in zip(C11,C12)]+[r1+r2 for r1,r2 in zip(C21,C22)]
N=16; X=[[random.randint(-9,9) for _ in range(N)] for _ in range(N)]; Y=[[random.randint(-9,9) for _ in range(N)] for _ in range(N)]
c1=[0]; c2=[0]; c3=[0]
ref=conv_mul(X,Y,c1); s=strassen(X,Y,c2,1); h=strassen(X,Y,c3,4)
print("16x16 check: Strassen == conventional:",s==ref," hybrid(cutoff 4) ==:",h==ref)
print("scalar multiplications n=16: conventional %d, Strassen %d (=7^4), hybrid cutoff 4: %d"%(c1[0],c2[0],c3[0]))
assert c2[0]==7**4 and s==ref and h==ref
n=1024; conv_m=n**3; st=7**10
print("n=1024: conventional n^3 = %d ; Strassen 7^10 = %d ; ratio %.3f (%.2fx fewer)"%(conv_m,st,st/conv_m,conv_m/st))
adds_conv=n*n*(n-1); adds_st=6*(7**10-n*n)
print("additions: conventional %d ; Strassen 6(7^10 - n^2) = %d"%(adds_conv,adds_st))
print("total arithmetic: conventional %d ; Strassen %d ; saving only %.1f %%"%(conv_m+adds_conv,st+adds_st,100*(1-(st+adds_st)/(conv_m+adds_conv))))
hy={}
for cut in (64,128,256):
    lv=int(math.log2(n//cut)); hy[cut]=(7**lv)*cut**3
    print("hybrid cutoff %3d: %d Strassen levels, %d x %d^3 = %d multiplications (%.1f %% of conventional)"%(cut,lv,7**lv,cut,hy[cut],100*hy[cut]/conv_m))
OUT["m4_num"]={"conv":conv_m,"st":st,"adds_conv":adds_conv,"adds_st":adds_st,"hy":{str(k):v for k,v in hy.items()},"tot_conv":conv_m+adds_conv,"tot_st":st+adds_st}
print("exponent log2(7) = %.4f"%math.log2(7))
json.dump(OUT,open("c3.json","w"),indent=1)
