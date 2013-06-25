from cjrhunit import *

pressure = 2000*kPa
print pressure
print pressure.convert(bar)
pressure.setRepresent(kPa, 'kPa')
print pressure
pressure.setRepresent(bar, 'bar')
print pressure
atm_pressure = 101.325 * kPa
barg = lambda bara: bara + atm_pressure
bara = pressure
print barg(bara)

print
print 'Temperature testing'
print

temp = 273.15 * K
print temp
temp.setRepresent(
    convert_function=lambda _, mag: mag - 273.15, 
    symbol='C')
print temp
temp = temp + 100*K
print temp

print
print 'Energy'
print

energy = 100*J
print 'energy = {}'.format(energy)
energy.setRepresent(as_unit=J, symbol='J')
print 'energy = {}'.format(energy)
print 'energy.convert(BTU) = {}'.format(energy.convert(BTU))
