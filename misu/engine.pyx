# -*- coding: utf-8 -*-
# cython: profile=True
"""
Created on Wed Sep 04 22:15:13 2013

@author: Caleb Hattingh
"""

cimport cython
import numpy as np
cimport numpy as np
from cpython.array cimport array, copy


cdef class Quantity
cdef class QuantityNP


class EIncompatibleUnits(Exception):
    pass


class ESignatureAlreadyRegistered(Exception):
    pass


ctypedef fused Quant:
    Quantity
    QuantityNP


ctypedef fused Qnumber:
    Quantity
    QuantityNP
    int
    double
    float


ctypedef fused magtype:
    int
    double
    float
    np.ndarray


cdef inline int isQuantity(var):
    ''' Checks whether var is an instance of type 'Quantity'.
    Returns True or False.'''
    return isinstance(var, Quantity)


cdef inline int isQuantityT(Quant var):
    ''' SPECIALIZED VERSION
    Checks whether var is an instance of type 'Quantity' or
    'QuantityNP'. Returns True or False.'''
    return isinstance(var, Quantity) or isinstance(var, QuantityNP)


ctypedef double[7] uarray


cdef inline void copyunits(Quant source, Quant dest):
    ''' Cython limitations require that both source and dest are the same
    type. '''
    cdef int i
    for i from 0 <= i < 7:
        dest.unit[i] = source.unit[i]


QuantityType = {}
cpdef addType(Quantity q, str name):
    if q.unit_as_tuple() in QuantityType:
        raise Exception('This unit def already registered, owned by: {}'.format(
            QuantityType[q.unit_as_tuple()]))
    QuantityType[q.unit_as_tuple()] = name


@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline Quantity assertQuantity(x):
    if isQuantity(x):
        return x
    else:
        return Quantity.__new__(Quantity, x)


cdef list symbols = ['m', 'kg', 's', 'A', 'K', 'ca', 'mole']


cdef inline sameunits(Quant self, Quant other):
    cdef int i
    for i from 0 <= i < 7:
        if self.unit[i] != other.unit[i]:
            raise EIncompatibleUnits(
                'Incompatible units: {} and {}'.format(self, other))


cdef inline sameunitsp(double self[7], double other[7]):
    cdef int i
    for i from 0 <= i < 7:
        if self[i] != other[i]:
            raise EIncompatibleUnits('Incompatible units: TODO')


cdef class _UnitRegistry:
    cdef dict _representation_cache
    cdef dict _symbol_cache

    # For defined quantities, e.g. LENGTH, MASS etc.
    cdef dict _unit_by_name # A name can mean only one unit
    cdef dict _name_by_unit # One unit type can have multiple names, so the
                            # values are lists.

    def __cinit__(self):
        self._symbol_cache = {}
        self._inverse_symbol_cache = {} # This one is keyed by quantity, with
        self._representation_cache = {} # ... a list of symbols as value.
        self._unit_by_name = {}
        self._name_by_unit = {}

    def add(self, str symbols, Quantity quantity, str quantity_name = None):
        # Split up the string of symbols
        cdef list symbols_list = [
            s.strip() for s in symbols.strip().split(' ') if s.strip() != '']
        # Populating the registry dicts.
        cdef tuple quantity_as_tuple = quantity.as_tuple()
        if not quantity_as_tuple in self._inverse_symbol_cache:
            # Prepare the inverse symbol cache.
            self._inverse_symbol_cache[quantity_as_tuple] = []

        # Add the list of symbols. We can use this dict to find all the
        # allowed symbols for a given quantity. For example, 'm metre metres'
        # if we have a quantity and can find it in the inverse symbol cache,
        # we will be able to see that each of 'm', 'metre' and 'metres' are
        # valid symbols for this quantity definition.
        self._inverse_symbol_cache[quantity_as_tuple] += symbols_list

        # Add each of the symbols to the symbols dict.  The same quantity is
        # simply repeated. The symbols dict is the opposite of the inverse
        # symbol cache. Given a (string) symbol, we can immediately find
        # the quantity object that the symbol maps to.
        for s in symbols_list:
            if s in symbols_list:
                raise Exception('Symbol "{}" already created!'.format(s))
            self._symbol_cache[s] = quantity
            # Inject the symbol into the module namespace.
            exec('global {s}; {s} = quantity'.format(s=s))

        # Use the first symbol to populate the representation dict.
        # Note that the representation dict is keyed by the unit tuple.
        # It is basically a reverse lookup, which returns the symbol string
        # to use for representation.
        cdef tuple unit = quantity.unit_as_tuple()
        # Only add if not already added.  Can always be changed manually
        # later.
        if not unit in self._representation_cache:
            self._representation_cache[unit] = symbols_list[0]

        if quantity_name != None:
            self.define(quantity, quantity_name)

    cpdef int defined(self, Quant q):
        ''' Given a quantity, will return a boolean value indicating
        whether the unit string of the given quantity has been defined
        as a known quantity, like LENGTH or MASS. '''
        cdef tuple unit = q.unit_as_tuple()
        return unit in self._name_by_unit

    cpdef str describe(self, Quant q):
        ''' If the units of the given quantity have been defined as a
        quantity, the string describing the quantity will be returned here,
        otherwise an exception will be raised. '''
        cdef tuple unit = q.unit_as_tuple()
        try:
            return self._name_by_unit[unit]
        except:
            raise Exception('The units have not been defined as a quantity.')

    def define(self, Quant q, str quantity_name):
        cdef tuple unit = q.unit_as_tuple()
        if quantity_name != None:
            name = quantity_name.replace(' ', '_').upper()
            if name in self._unit_by_name:
                raise Exception('This name has already been defined.')
            if unit in self._name_by_unit:
                raise Exception('This unit has already been defined as "{}"'.format(name))
            self._unit_by_name[name] = unit
            self._name_by_unit[unit] = name

    def set_represent(self, tuple unit, as_quantity=None, symbol='',
        convert_function=None, format_spec='.4g'):
        ''' The given unit tuple will always be presented in the units
        of "as_quantity", and with the overridden symbol "symbol" if
        given. '''

    def __getattr__(self, name):
        ''' Will return a unit string representing a defined quantity. '''
        try:
            return self._unit_by_name[name]
        except:
            raise Exception('Quantity type "{}" not defined.'.format(name))


RepresentCache = {}


# The unit registry is a lookup list where you can find a specific
# UnitDefinition from a particular symbol.  Note that multiple entries
# in the UnitRegistry can point to the same unit definition, because
# there can be many synonyms for a particular unit, e.g.
# s, sec, secs, seconds
UnitRegistry = {}
class UnitDefinition(object):
    def __init__(self, symbols, quantity, notes):
        self.symbols = [s.strip() for s in symbols.strip().split(' ') if s.strip() != '']
        self.quantity = quantity
        self.notes = notes
        for s in self.symbols:
            try:
                UnitRegistry[s] = self
                exec('global {s}; {s} = quantity'.format(s=s))
            except:
                print 'Error create UnitRegistry entry for symbol: {}'.format(s)


cdef array _nou  = array('d', [0,0,0,0,0,0,0])


@cython.freelist(8)
cdef class Quantity:
    cdef readonly double magnitude
    cdef uarray unit
    __array_priority__ = 20.0

    def __cinit__(self, double magnitude):
        self.magnitude = magnitude
        #self.stddev = 0
        self.unit[:] = [0,0,0,0,0,0,0]

#    def __array_wrap__(array, context=None):
#        return

    cdef inline tuple unit_as_tuple(self):
        return tuple(self.units())

    def setValDict(self, dict valdict):
        cdef int i
        cdef list values
        values = [valdict.get(s) or 0 for s in symbols]
        for i from 0 <= i < 7:
            self.unit[i] = values[i]

    def setValDict2(self, **kwargs):
        cdef int i
        cdef list values
        values = [kwargs.get(s) or 0 for s in symbols]
        for i from 0 <= i < 7:
            self.unit[i] = values[i]

    def getunit(self):
        cdef list out
        cdef int i
        out = [0.0]*7
        for i from 0 <= i < 7:
            out[i] = self.unit[i]
        return out

    def setunit(self, list unit):
        cdef int i
        for i from 0 <= i < 7:
            self.unit[i] = unit[i]

    def selfPrint(self):
        dict_contents = ','.join(['{}={}'.format(s,v) for s,v in dict(zip(symbols, self.units())).iteritems() if v != 0.0])
        return 'Quantity({}, dict({}))'.format(self.magnitude, dict_contents)

    def setRepresent(self, as_unit=None, symbol='',
        convert_function=None, format_spec='.4g'):
        '''By default, the target representation is arrived by dividing
        the current unit MAGNITUDE by the target unit MAGNITUDE, and
        appending the desired representation symbol.

        However, if a conversion_function is supplied, then INSTEAD the
        conversion function will be called so:

            output_magnitude = conversion_function(self.magnitude)
            output_symbol = symbol

            result = '{} {}'.format(output_magnitude, output_symbol)

        The intention of the function argument is to allow
        non-proportional conversion, typically temperature but also things
        like barg, bara, etc.

        Note that if a convert_function is supplied, the as_unit arg
        is IGNORED.'''
        if not (as_unit or convert_function):
            raise Exception('Either a target unit or a conversion function must be supplied.')

        if convert_function == None:
            def proportional_conversion(instance, _):
                return instance.convert(as_unit)
            convert_function = proportional_conversion
        RepresentCache[self.unit_as_tuple()] = dict(
            convert_function=convert_function,
            symbol=symbol,
            format_spec=format_spec)

    def units(self):
        cdef list out = []
        cdef int i
        for i in range(7):
            out.append(self.unit[i])
        return out

    cpdef tuple as_tuple(self):
        return (self.magnitude, self.unit_as_tuple())

    def _unitString(self):
        if self.unit_as_tuple() in RepresentCache:
            r = RepresentCache[self.unit_as_tuple()]
            ret = '{}'.format(r['symbol'])
            return ret
        else:
            text = ' '.join(['{}^{}'.format(k,v) for k, v in zip(symbols, self.units()) if v != 0])
            ret = '{}'.format(text)
            return ret

    def _getmagnitude(self):
        if self.unit_as_tuple() in RepresentCache:
            r = RepresentCache[self.unit_as_tuple()]
            return r['convert_function'](self, self.magnitude)
        else:
            return self.magnitude

    def _getsymbol(self):
        if self.unit_as_tuple() in RepresentCache:
            r = RepresentCache[self.unit_as_tuple()]
            return r['symbol']
        else:
            return self._unitString()

    def _getRepresentTuple(self):
        if self.unit_as_tuple() in RepresentCache:
            r = RepresentCache[self.unit_as_tuple()]
            mag = r['convert_function'](self, self.magnitude)
            symbol = r['symbol']
            format_spec = r['format_spec']
        else:
            mag = self.magnitude
            symbol = self._unitString()
            format_spec = ''
        # Temporary fix for a numpy display issue
        if not type(mag) in [float, int]:
            format_spec = ''
        return mag, symbol, format_spec

    def __str__(self):
        mag, symbol, format_spec = self._getRepresentTuple()
        number_part = format(mag, format_spec)
        if symbol == '':
            return number_part
        else:
            return ' '.join([number_part, symbol])

    def __repr__(self):
        return str(self)

#    cdef inline sameunits(Quant self, Quant other):
#        cdef int i
#        for i from 0 <= i < 7:
#            if self.unit[i] != other.unit[i]:
#                raise EIncompatibleUnits('Incompatible units: {} and {}'.format(self, other))

    def __add__(x, y):
        cdef QuantityNP xqn
        cdef QuantityNP yqn
        cdef QuantityNP ansn

        cdef Quantity xq
        cdef Quantity yq
        cdef Quantity ans

        cdef int i

        if isinstance(x, np.ndarray) or isinstance(y, np.ndarray) \
            or isinstance(x, QuantityNP) or isinstance(y, QuantityNP):
            xqn = assertQuantityNP(x)
            yqn = assertQuantityNP(y)
            return xqn + yqn
        else:
            xq = assertQuantity(x)
            yq = assertQuantity(y)
            ans = Quantity.__new__(Quantity, xq.magnitude + yq.magnitude)
            sameunits(xq, yq)
            for i from 0 <= i < 7:
                ans.unit[i] = xq.unit[i]
            return ans

    def __sub__(x, y):
        cdef QuantityNP xqn
        cdef QuantityNP yqn
        cdef QuantityNP ansn

        cdef Quantity xq
        cdef Quantity yq
        cdef Quantity ans

        cdef int i

        if isinstance(x, np.ndarray) or isinstance(y, np.ndarray) \
            or isinstance(x, QuantityNP) or isinstance(y, QuantityNP):
            xqn = assertQuantityNP(x)
            yqn = assertQuantityNP(y)
            return xqn - yqn
        else:
            xq = assertQuantity(x)
            yq = assertQuantity(y)
            ans = Quantity.__new__(Quantity, xq.magnitude - yq.magnitude)
            sameunits(xq, yq)
            for i from 0 <= i < 7:
                ans.unit[i] = xq.unit[i]
            return ans

    def unpack_or_default(self, other):
        try:
            return other.unit
        except:
            return _nou

    def __mul__(x, y):
        cdef QuantityNP xqn
        cdef QuantityNP yqn
        cdef QuantityNP ansn

        cdef Quantity xq
        cdef Quantity yq
        cdef Quantity ans

        cdef int i

        if isinstance(x, np.ndarray) or isinstance(y, np.ndarray) \
            or isinstance(x, QuantityNP) or isinstance(y, QuantityNP):
            xqn = assertQuantityNP(x)
            yqn = assertQuantityNP(y)
            ansn = QuantityNP.__new__(QuantityNP, xqn.magnitude * yqn.magnitude)
            for i from 0 <= i < 7:
                ansn.unit[i] = xqn.unit[i] + yqn.unit[i]
            return ansn
        else:
            xq = assertQuantity(x)
            yq = assertQuantity(y)
            ans = Quantity.__new__(Quantity, xq.magnitude * yq.magnitude)
            for i from 0 <= i < 7:
                ans.unit[i] = xq.unit[i] + yq.unit[i]
            return ans

    def __div__(x,y):
        cdef Quantity xq = assertQuantity(x)
        cdef Quantity yq = assertQuantity(y)
        cdef Quantity ans = Quantity.__new__(Quantity, xq.magnitude / yq.magnitude)
        cdef int i
        for i from 0 <= i < 7:
            ans.unit[i] = xq.unit[i] - yq.unit[i]
        return ans

    def __truediv__(x, y):
        cdef Quantity xq = assertQuantity(x)
        cdef Quantity yq = assertQuantity(y)
        cdef Quantity ans = Quantity.__new__(Quantity, xq.magnitude / yq.magnitude)
        cdef int i
        for i from 0 <= i < 7:
            ans.unit[i] = xq.unit[i] - yq.unit[i]
        return ans

    def __pow__(x, y, z):
        cdef Quantity xq = assertQuantity(x)
        assert not isQuantity(y), 'The exponent must not be a quantity!'
        cdef Quantity ans = Quantity.__new__(Quantity, xq.magnitude ** y)
        cdef int i
        for i from 0 <= i < 7:
            ans.unit[i] = xq.unit[i] * y
        return ans

    def __neg__(self):
        cdef Quantity ans = Quantity.__new__(Quantity, -self.magnitude)
        cdef int i
        for i from 0 <= i < 7:
            ans.unit[i] = self.unit[i]
        return ans

    def __cmp__(x, y):
        cdef Quantity xq = assertQuantity(x)
        cdef Quantity yq = assertQuantity(y)
        sameunits(xq, yq)
        if xq.magnitude < yq.magnitude:
            return -1
        elif xq.magnitude == yq.magnitude:
            return 0
        elif xq.magnitude > yq.magnitude:
            return 1
        else:
            raise Exception('Impossible.')

    def __richcmp__(x, y, int op):
        """
        <   0
        ==  2
        >   4
        <=  1
        !=  3
        >=  5
        """
        cdef Quantity xq = assertQuantity(x)
        cdef Quantity yq = assertQuantity(y)
        sameunits(xq, yq)
        if op == 0:
            return xq.magnitude > yq.magnitude
        elif op == 1:
            return xq.magnitude <= yq.magnitude
        elif op == 2:
            return xq.magnitude == yq.magnitude
        elif op == 3:
            return xq.magnitude != yq.magnitude
        elif op == 4:
            return xq.magnitude > yq.magnitude
        elif op == 5:
            return xq.magnitude >= yq.magnitude

    def convert(self, Quantity target_unit):
        assert isQuantity(target_unit), 'Target must be a quantity.'
        sameunits(self, target_unit)
        return self.magnitude / target_unit.magnitude

    def unitCategory(self):
        if self.unit_as_tuple() in QuantityType:
            return QuantityType[self.unit_as_tuple()]
        else:
            msg = 'The collection of units: "{}" has not been defined as a category yet.'
            raise Exception(msg.format(str(self)))

    def __format__(self, format_spec):
        # Ignore the stored format_spec, use the given one.
        mag, symbol, stored_format_spec = self._getRepresentTuple()
        if format_spec == '':
            format_spec = stored_format_spec
        number_part = format(mag, format_spec)
        if symbol == '':
            return number_part
        else:
            return ' '.join([number_part, symbol])

    def __float__(self):
        assert self.unitCategory() == 'Dimensionless', 'Must be dimensionless for __float__()'
        return self.magnitude

    def __rshift__(self, other):
        return self.convert(other)


cdef inline int isQuantityNP(var):
    ''' checks whether var is an instance of type 'Quantity'.
    Returns True or False.'''
    return isinstance(var, QuantityNP)


cdef inline QuantityNP assertQuantityNP(x):
    cdef QuantityNP out
    cdef list a
    if isinstance(x, QuantityNP):
        return x
    elif isinstance(x, Quantity):
        out = QuantityNP.__new__(QuantityNP, np.array(x.magnitude))
        a = x.getunit()
        out.setunit(a)
        return out
    else:
        return QuantityNP.__new__(QuantityNP, x)

@cython.freelist(8)
cdef class QuantityNP:
    cdef readonly np.ndarray magnitude
    cdef double unit[7]
    __array_priority__ = 20.0

    def __cinit__(self, np.ndarray magnitude):
        self.magnitude = magnitude
        self.unit[:] = [0,0,0,0,0,0,0]

    #def __array__(self, dtype=None):
    #    return self.magnitude

    ## We have to disable this for now. ufuncs in danger of giving the wrong
    ## answer.
    #def __getattr__(self, name):
    #    ''' All member lookup not found here get passed to the magnitude value. '''
    #    return getattr(self.magnitude, name)

    #def __dir__(self):
    #    return dir(self.magnitude)

#    def __array_wrap__(self, array, context=None):
#        print self
#        print array
#
#        cdef QuantityNP ans = assertQuantityNP(array)
#        cdef int i
#        for i from 0 <= i < 7:
#            ans.unit[i] = self.unit[i]
#        return ans

    def __getitem__(self, val):
        cdef int i
        cdef Quantity ansq
        if type(val)==int:
            ansq = Quantity.__new__(Quantity, self.magnitude[val])
            for i from 0 <= i < 7:
                ansq.unit[i] = self.unit[i]
            return ansq
        cdef QuantityNP ans = QuantityNP.__new__(QuantityNP, self.magnitude[val])
        copyunits(self, ans)
        return ans

    cdef inline tuple unit_as_tuple(self):
        return tuple(self.units())

    def setValDict(self, dict valdict):
        cdef int i
        cdef list values
        values = [valdict.get(s) or 0 for s in symbols]
        for i from 0 <= i < 7:
            self.unit[i] = values[i]

    def setValDict2(self, **kwargs):
        cdef int i
        cdef list values
        values = [kwargs.get(s) or 0 for s in symbols]
        for i from 0 <= i < 7:
            self.unit[i] = values[i]

    def getunit(self):
        cdef list out
        cdef int i
        out = []*7
        for i from 0 <= i < 7:
            out[i] = self.unit[i]
        return out

    def setunit(self, list unit):
        cdef int i
        for i from 0 <= i < 7:
            self.unit[i] = unit[i]

    def selfPrint(self):
        dict_contents = ','.join(['{}={}'.format(s,v) for s,v in dict(zip(symbols, self.units())).iteritems() if v != 0.0])
        return 'Quantity({}, dict({}))'.format(self.magnitude, dict_contents)

    def setRepresent(self, as_unit=None, symbol='',
        convert_function=None, format_spec='.4g'):
        '''By default, the target representation is arrived by dividing
        the current unit MAGNITUDE by the target unit MAGNITUDE, and
        appending the desired representation symbol.

        However, if a conversion_function is supplied, then INSTEAD the
        conversion function will be called so:

            output_magnitude = conversion_function(self.magnitude)
            output_symbol = symbol

            result = '{} {}'.format(output_magnitude, output_symbol)

        The intention of the function argument is to allow
        non-proportional conversion, typically temperature but also things
        like barg, bara, etc.

        Note that if a convert_function is supplied, the as_unit arg
        is IGNORED.'''
        if not (as_unit or convert_function):
            raise Exception('Either a target unit or a conversion function must be supplied.')

        if convert_function == None:
            def proportional_conversion(instance, _):
                return instance.convert(as_unit)
            convert_function = proportional_conversion
        RepresentCache[self.unit_as_tuple()] = dict(
            convert_function=convert_function,
            symbol=symbol,
            format_spec=format_spec)

    def units(self):
        cdef list out = []
        cdef int i
        for i in range(7):
            out.append(self.unit[i])
        return out

    def _unitString(self):
        if self.unit_as_tuple() in RepresentCache:
            r = RepresentCache[self.unit_as_tuple()]
            ret = '{}'.format(r['symbol'])
            return ret
        else:
            text = ' '.join(['{}^{}'.format(k,v) for k, v in zip(symbols, self.units()) if v != 0])
            ret = '{}'.format(text)
            return ret

    def _getmagnitude(self):
        if self.unit_as_tuple() in RepresentCache:
            r = RepresentCache[self.unit_as_tuple()]
            return r['convert_function'](self, self.magnitude)
        else:
            return self.magnitude

    def _getsymbol(self):
        if self.unit_as_tuple() in RepresentCache:
            r = RepresentCache[self.unit_as_tuple()]
            return r['symbol']
        else:
            return self._unitString()

    def _getRepresentTuple(self):
        if self.unit_as_tuple() in RepresentCache:
            r = RepresentCache[self.unit_as_tuple()]
            mag = r['convert_function'](self, self.magnitude)
            symbol = r['symbol']
            format_spec = r['format_spec']
        else:
            mag = self.magnitude
            symbol = self._unitString()
            format_spec = ''
        # Temporary fix for a numpy display issue
        if not type(mag) in [float, int]:
            format_spec = ''
        return mag, symbol, format_spec

    def __str__(self):
        mag, symbol, format_spec = self._getRepresentTuple()
        number_part = format(mag, format_spec)
        if symbol == '':
            return number_part
        else:
            return ' '.join([number_part, symbol])

    def __repr__(self):
        return str(self)

    def __add__(x, y):
        cdef QuantityNP xq = assertQuantityNP(x)
        cdef QuantityNP yq = assertQuantityNP(y)
        sameunits(xq, yq)
        cdef QuantityNP ans = QuantityNP.__new__(QuantityNP, xq.magnitude + yq.magnitude)
        cdef int i
        for i from 0 <= i < 7:
            ans.unit[i] = xq.unit[i]
        return ans

    def __sub__(x, y):
        cdef QuantityNP xq = assertQuantityNP(x)
        cdef QuantityNP yq = assertQuantityNP(y)
        sameunits(xq, yq)
        cdef QuantityNP ans = QuantityNP.__new__(QuantityNP, xq.magnitude - yq.magnitude)
        cdef int i
        for i from 0 <= i < 7:
            ans.unit[i] = xq.unit[i]
        return ans

    def unpack_or_default(self, other):
        try:
            return other.unit
        except:
            return _nou

    def __mul__(x, y):
        cdef QuantityNP xq = assertQuantityNP(x)
        cdef QuantityNP yq = assertQuantityNP(y)
        cdef QuantityNP ans = QuantityNP.__new__(QuantityNP, xq.magnitude * yq.magnitude)
        cdef int i
        for i from 0 <= i < 7:
            ans.unit[i] = xq.unit[i] + yq.unit[i]
        return ans

    def __div__(x,y):
        cdef QuantityNP xq = assertQuantityNP(x)
        cdef QuantityNP yq = assertQuantityNP(y)
        cdef QuantityNP ans = QuantityNP.__new__(QuantityNP, xq.magnitude / yq.magnitude)
        cdef int i
        for i from 0 <= i < 7:
            ans.unit[i] = xq.unit[i] - yq.unit[i]
        return ans

    def __truediv__(x, y):
        cdef QuantityNP xq = assertQuantityNP(x)
        cdef QuantityNP yq = assertQuantityNP(y)
        cdef QuantityNP ans = QuantityNP.__new__(QuantityNP, xq.magnitude / yq.magnitude)
        cdef int i
        for i from 0 <= i < 7:
            ans.unit[i] = xq.unit[i] - yq.unit[i]
        return ans

    def __pow__(x, y, z):
        cdef QuantityNP xq = assertQuantityNP(x)
        assert not isQuantityNP(y), 'The exponent must not be a quantity!'
        cdef QuantityNP ans = QuantityNP.__new__(QuantityNP, xq.magnitude ** y)
        cdef int i
        for i from 0 <= i < 7:
            ans.unit[i] = xq.unit[i] * y
        return ans

    def __neg__(self):
        cdef QuantityNP ans = QuantityNP.__new__(QuantityNP, -self.magnitude)
        cdef int i
        for i from 0 <= i < 7:
            ans.unit[i] = self.unit[i]
        return ans

    def __cmp__(x, y):
        cdef QuantityNP xq = assertQuantityNP(x)
        cdef QuantityNP yq = assertQuantityNP(y)
        sameunits(xq, yq)
        if xq.magnitude < yq.magnitude:
            return -1
        elif xq.magnitude == yq.magnitude:
            return 0
        elif xq.magnitude > yq.magnitude:
            return 1
        else:
            raise Exception('Impossible.')

    def convert(self, Quantity target_unit):
        assert isQuantity(target_unit), 'Target must be a quantity.'
        # Because of how fused types work, I have to manufacture
        # the comparison
        sameunitsp(self.unit, target_unit.unit)
        return self.magnitude / target_unit.magnitude

    def unitCategory(self):
        if self.unit_as_tuple() in QuantityType:
            return QuantityType[self.unit_as_tuple()]
        else:
            msg = 'The collection of units: "{}" has not been defined as a category yet.'
            raise Exception(msg.format(str(self)))

    def __format__(self, format_spec):
        # Ignore the stored format_spec, use the given one.
        mag, symbol, stored_format_spec = self._getRepresentTuple()
        if format_spec == '':
            format_spec = stored_format_spec
        number_part = format(mag, format_spec)
        if symbol == '':
            return number_part
        else:
            return ' '.join([number_part, symbol])

    def __float__(self):
        assert self.unitCategory() == 'Dimensionless', 'Must be dimensionless for __float__()'
        return self.magnitude

    def __rshift__(self, other):
        return self.convert(other)

    def copy(self):
        cdef QuantityNP ans = QuantityNP.__new__(QuantityNP, self.magnitude)
        cdef int i
        for i from 0 <= i < 7:
            ans.unit[i] = self.unit[i]
        return ans


if __name__ == '__main__':
#    m = Quantity(1.0, {'m':1.0}, 'Length')
#    kg = Quantity(1.0, {'kg':1.0}, 'Mass')
#    rho = 1000*kg/m**3
#    print rho
    for i in xrange(100000):
        m = Quantity(1.0, {'m':1.0}, 'Length')
        kg = Quantity(1.0, {'kg':1.0}, 'Mass')
        rho = 1000*kg/m**3
