# SI Prefixes
import collections
data='''
24,yotta,Y
21,zetta,Z
18,exa,E
15,peta,P
12,tera,T
9,giga,G
6,mega,M
3,kilo,k
2,hecto,h
1,deka,da

-1,deci,d
-2,centi,c
-3,milli,m
-6,micro,u
-9,nano,n
-12,pico,p
-15,femto,f
-18,atto,a
-21,zepto,z
-24,yocto,y
'''


SIprefix = collections.namedtuple('SIprefix', 'exponent name symbol')
# Cleanup
clean_data = [tuple(i.strip().split(',')) for i in data.split('\n') if i.strip() !='']


# Duplicates of the mappings, keyed by different things
SIprefixes_exp = {e: SIprefix(exponent=e, name=n, symbol=sym) for e,n,sym in clean_data}
SIprefixes_sym = {sym: SIprefix(exponent=e, name=n, symbol=sym) for e,n,sym in clean_data}
SIprefixes_name = {n: SIprefix(exponent=e, name=n, symbol=sym) for e,n,sym in clean_data}
