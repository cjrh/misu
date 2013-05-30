# coding=utf8
import collections
import copy
import traceback
Ustruct = collections.namedtuple('Ustruct','m kg s A K ca mole')

from struct import pack, unpack
'''
>>> v=pack('bbbbbbb', 1,-1,1,0,0,4,0)
>>> u=pack('bbbbbbb', -3,2,2,0,3,0,8)
>>> u
'\xfd\x02\x02\x00\x03\x00\x08'
>>> v
'\x01\xff\x01\x00\x00\x04\x00'
>>> w=pack(fmt, *[x+y for x,y in zip(unpack(fmt, u), unpack(fmt, v))])
>>> w
'\xfe\x01\x03\x00\x03\x04\x08'
>>> unpack(fmt, w)
(-2, 1, 3, 0, 3, 4, 8)
'''

symbols = ['m', 'kg', 's', 'A', 'K', 'ca', 'mole']

class FloatWithUnits(float):
    fmt = 'f' * len(symbols)
    emptyunpacked = [0 for i in symbols]
    emptystruct = pack(fmt, *emptyunpacked)
    def __new__(self, value, valdict=None):
        return float.__new__(self, value)
    def __init__(self, value, valdict=None):
        lst=[0]*len(symbols)  # new list!
        if valdict:
            for k in valdict:
                lst[symbols.index(k)] = valdict[k]
        self.u = pack(self.fmt, *lst)
    def units(self):
        return Ustruct._make(unpack(self.fmt,self.u))
    def __str__(self):
        #import pdb; pdb.set_trace()
        ut = self.units()._asdict()
        text = ' '.join(['{}^{}'.format(k,v) for k, v in ut.items() if v != 0])
        return '{} {}'.format(self.real, text)
    def hasunits(self, other):
        return isinstance(other, FloatWithUnits)
    def checkunits(self, other):
        if not isinstance(other, FloatWithUnits):
            raise Exception('Incompatible types: {} and {}'.format(type(self), type(other)))
    def sameunits(self, other):
        if not self.u == other.u:
            raise Exception('Incompatible units: {} and {}'.format(self, other))
    def __add__(self, other):
        self.hasunits(other)
        self.sameunits(other)
        ans = FloatWithUnits(super(FloatWithUnits, self).__add__(other))
        ans.u = copy.copy(self.u)
        return ans
    def __sub__(self, other):
        self.hasunits(other)
        self.sameunits(other)
        ans = FloatWithUnits(super(FloatWithUnits, self).__sub__(other))
        ans.u = copy.copy(self.u)
        return ans
    def unpack_or_default(self, other):
        if self.hasunits(other):
            return unpack(self.fmt, other.u)
        else:
            return copy.copy(self.emptyunpacked)
    def __mul__(self, other):
        ans = FloatWithUnits(super(FloatWithUnits, self).__mul__(other))
        uvals = self.unpack_or_default(other)
        ans.u = pack(self.fmt, *[x+y for x,y in zip(unpack(self.fmt, self.u), uvals)])
        return ans
    def __rmul__(self, other):
        return self.__mul__(other)
    def __div__(self, other):
        #import pdb; pdb.set_trace()
        ans = FloatWithUnits(super(FloatWithUnits, self).__div__(other))
        uvals = self.unpack_or_default(other)
        ans.u = pack(self.fmt, *[x-y for x,y in zip(unpack(self.fmt, self.u), uvals)])
        return ans
    def __rdiv__(self, other):
        #import pdb; pdb.set_trace()
        ans = FloatWithUnits(FloatWithUnits(other).__div__(self))
        uvals = self.unpack_or_default(other)
        ans.u = pack(self.fmt, *[y-x for x,y in zip(unpack(self.fmt, self.u), uvals)])
        return ans
    def __truediv__(self, other):
        ans = FloatWithUnits(super(FloatWithUnits, self).__truediv__(other))
        uvals = self.unpack_or_default(other)
        ans.u = pack(self.fmt, *[x-y for x,y in zip(unpack(self.fmt, self.u), uvals)])
        return ans
    def __rtruediv__(self, other):           # -*- coding: utf-8 -*-
        return self.__truediv__(other)
    def __pow__(self, other):
        ans = FloatWithUnits(super(FloatWithUnits, self).__pow__(other))
        uvals = [other for x in symbols]
        ans.u = pack(self.fmt, *[x*y for x,y in zip(unpack(self.fmt, self.u), uvals)])
        return ans

# Population of units data
dimensionless = FloatWithUnits(1.0)

# SI base units
'''
for sym in symbols:
    exec('{0} = FloatWithUnits(1.0, dict({0}=1.0))'.format(sym))
    print eval(sym), eval(sym).units()
'''

m = FloatWithUnits(1.0, dict(m=1.0))
kg = FloatWithUnits(1.0, dict(kg=1.0))
s = FloatWithUnits(1.0, dict(s=1.0))
A = FloatWithUnits(1.0, dict(A=1.0))
K = FloatWithUnits(1.0, dict(K=1.0))
ca = FloatWithUnits(1.0, dict(ca=1.0))
mole = FloatWithUnits(1.0, dict(mole=1.0))

# Derived units (definitions)

# SI Prefixes
                                                           # -*- coding: utf-8 -*-
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
clean_data = [tuple(i.strip().split(',')) for i in data.split('\n') if i.strip() !='']
SIprefixes = {e: SIprefix(exponent=e, name=n, symbol=sym) for e,n,sym in clean_data}
print SIprefixes

class SIprefix(object):
    def __init__(self, exponent, name, symbol):
        self.exponent=exponent
        self.name=name
        self.symbol=symbol

if __name__ == '__main__':

    print
    print '*'*80
    print
    # Testing                                     # -*- coding: utf-8 -*-
    def test(text):
        try:
            print '{:50}: {}'.format(text, eval(text))
        except:
            print
            print 'Trying: ' + text
            print traceback.print_exc(0)
            print

    a = 2.5 * kg / s
    b = 34.67 * kg / s

    test('a')
    test('b')
    test('a+b')
    test('a-b')
    test('a*b')
    test('a/b')

    test('2.0 * m + 3.0 * kg')
    test('2.0 * kg / s * 3.0')
    test('2.0 * 3.0 * kg / s')

    test('(1.0/m)**0.5') 

    test('((kg ** 2.0)/(m))**0.5')
    test('(1.56724 * (kg ** 2.0)/(m * (s**2.0)))**0.5')

