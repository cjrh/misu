# coding=utf8
from __future__ import division, print_function 
import sys
import traceback
import math
import re
from misu.engine import *
from misu.SIprefixes import SIprefixes_sym


def createMetricPrefixes(symbol, skipfunction=None):
    ''' Populates the namespace with all the SI-prefixed versions of the
    given symbol.  This uses exec() internally.'''
    for prefix in SIprefixes_sym:
        if skipfunction and skipfunction(prefix):
            continue
        template = 'global {p}{s}; {p}{s} = 1e{e} * {s}'
        subs = template.format(
            p=prefix, s=symbol, e=SIprefixes_sym[prefix].exponent)
        exec(subs)


def createUnit(symbols, quantity, mustCreateMetricPrefixes=False, valdict=None,
               unitCategory=None, metricSkipFunction=None, notes=None):
    '''
        symbols: string of space-delimited units.  These will also be eval'ed
                 into the module namespace, and will be entered as keys in
                 UnitRegistry.

        quantity: would typically be a result of a calculation against
                  base SI or some other unit defined earlier.

        notes: any important notes about the unit.
    '''
    if valdict:
        quantity.setValDict(valdict)
    first_symbol = symbols.strip().split(' ')[0].strip()
    if unitCategory:
        addType(quantity, unitCategory)
        quantity.setRepresent(as_unit=quantity, symbol=first_symbol)

    for i, symbol in enumerate(symbols.split(' ')):
        try:
            symbol = symbol.strip()
            if symbol == '':
                continue
            UnitRegistry[symbol] = quantity
            exec('global {s}; {s} = quantity'.format(s=symbol))
        except:
            print(traceback.format_exc())

    # Metric prefixes
    if mustCreateMetricPrefixes:
        createMetricPrefixes(first_symbol, metricSkipFunction)


def quantity_from_string(string):
    """Create a Quantity instance from the supplied string.

    The string has to be in the format that misu uses for string representations, i.e.
    the following works:

    1.0 m
    1 m
    1 m^2 s^-1
    1 m/s
    1.248e+05 m/s
    -1.158e+05 m/s kg

    """
    # Multiplication: replace all whitespace surounded by a-z,A-Z,0-9 with *
    string = re.sub(r'([a-z,A-Z,0-9])(\s+)([a-z,A-Z,0-9])',r'\1*\3' , string)

    # Exponentiation: replace all ^ with **
    string = re.sub(r'\^', r'**' , string)

    res = None
    try:
        res = eval(string)
    except NameError:
        print('String {s} not understood.'.format(string))
        res = None
    except SyntaxError:
        print('String {s} not understood.'.format(string))
        res = None
    return res


def plot_quantities(ax, x, xunits, y, yunits, series_label,
                    y_axlabel=None, x_axlabel=None):
    ''' Utility function that will include the units into the plot.'''
    xdata = x >> xunits
    ydata = y >> yunits
    # TODO : unfinished.


# Population of units data
dimensionless = Quantity(1.0)
addType(dimensionless, 'Dimensionless')


# Root units
createUnit('m metre metres', Quantity(1.0), valdict=dict(m=1.0),
           mustCreateMetricPrefixes=True, unitCategory='Length')

createUnit('g gram grams', Quantity(1.0e-3), valdict=dict(kg=1.0),
           mustCreateMetricPrefixes=True, unitCategory='Mass')
g.setRepresent(as_unit=kg, symbol='kg')

createUnit('s second sec seconds secs', Quantity(1.0), valdict=dict(s=1.0),
           mustCreateMetricPrefixes=True , unitCategory='Time',
           metricSkipFunction=lambda p: p=='a') # makes "as" which is illegal

createUnit('A ampere amperes amp amps', Quantity(1.0), valdict=dict(A=1.0),
           mustCreateMetricPrefixes=True, unitCategory='Current')

createUnit('K kelvin', Quantity(1.0),
           valdict=dict(K=1.0), mustCreateMetricPrefixes=True,
           unitCategory='Temperature')
createUnit('R rankine', K*5./9.)


def temperature_value_from_celsius(celsius):
    return (celsius - 273.15)*K


def temperature_change_from_celsius(celsius):
    return celsius * K


def temperature_value_from_fahrenheit(fahrenheit):
    return (fahrenheit + 459.67) * R


def temperature_change_from_fahrenheit(fahrenheit):
    return fahrenheit * R


createUnit('ca candela cd', Quantity(1.0), valdict=dict(ca=1.0), mustCreateMetricPrefixes=False, unitCategory='Luminous intensity')
createUnit('mol mole moles', Quantity(1.0), valdict=dict(mole=1.0), mustCreateMetricPrefixes=True, unitCategory='Substance')
createMetricPrefixes('mole')

# Derived units (definitions)

#import pdb; pdb.set_trace()
createUnit('Hz hertz', 1 / s, mustCreateMetricPrefixes=True, unitCategory='Frequency')
createUnit('N newton', kg * m / s**2, mustCreateMetricPrefixes=True, unitCategory='Force')
createUnit('Pa pascal', N / m**2, mustCreateMetricPrefixes=True, unitCategory='Pressure')
createUnit('J joule', N * m, mustCreateMetricPrefixes=True, unitCategory='Energy')
createUnit('W watt', J / s, mustCreateMetricPrefixes=True, unitCategory='Power')
createUnit('C coulomb', s * A, mustCreateMetricPrefixes=True, unitCategory='Charge')
createUnit('V volt', W / A, mustCreateMetricPrefixes=True, unitCategory='Voltage')
createUnit('F farad', C / V, mustCreateMetricPrefixes=True, unitCategory='Capacitance')

createUnit('ohm', V / A, mustCreateMetricPrefixes=True, unitCategory='Resistance')
createUnit('S siemens', 1 / ohm, mustCreateMetricPrefixes=False, unitCategory='Conductance')
createUnit('Wb weber', J / A, mustCreateMetricPrefixes=False, unitCategory='Magnetic flux')
createUnit('T tesla', N / A / m, mustCreateMetricPrefixes=True, unitCategory='Magnetic field strength')

createUnit('H henry', V * s / A, mustCreateMetricPrefixes=True, unitCategory='Magnetic field strength')
createUnit('lumen lm', cd * J, mustCreateMetricPrefixes=False, unitCategory='Luminous flux')
createUnit('lux lx', lm / m**2, mustCreateMetricPrefixes=False, unitCategory='Luminous flux')

############ Big list of definitions #################################################

# Time
createUnit('minute mins minutes', 60 * s)
createUnit('yr year years year_Gregorian', 31556952 * s)
createUnit('year_Julian', 31557600 * s)
createUnit('year_sidereal', 31558149.7632 * s)
createUnit('year_tropical', 31556925 * s)
createUnit('au atomic_unit_of_time', 2.418884254e-17 * s)
createUnit('Callippic_cycle ', 2.3983776e9 * s)
createUnit('century centuries', 100 * years)
createUnit('d day days', 86400 * s)
createUnit('day_sidereal', 86164.1 * s)
createUnit('dec decade decades', 10 * years)
createUnit('fn fortnight fortnights', 1209600 * s)
createUnit('helek', 3.3 * s)
createUnit('Hipparchic_cycle', 9.593424e9 * s)
createUnit('hr hour hrs hours', 3600 * s)
createUnit('j jiffy', .016 * s)
createUnit('ja jiffy_alternate', 10 * ms)
createUnit('ke_quarter_of_an_hour ', 15 * minutes)
createUnit('ke_traditional ', 14.4 * minutes)
createUnit('lustre  lustrum ', 1.5768e8 * s)
createUnit('Metonic_cycle  enneadecaeteris ', 5.99616e8 * s)
createUnit('millennium ', 1000 * years)
createUnit('moment ', 90 * s)
createUnit('month_full  mo ', 2592000 * s)
createUnit('month_Greg_avg  mo ', 2.6297e6 * s)
createUnit('month_hollow  mo ', 2505600 * s)
createUnit('month_synodic  mo ', 2.551e6 * s)
createUnit('octaeteris ', 2.524608e8 * s)
createUnit('Planck_time ', 1.351211868e-43 * s)
createUnit('shake shakes', 10 * ns)
createUnit('sigma ', 1 * us)
createUnit('Sothic_cycle ', 4.6074096e10 * s)
createUnit('svedberg  S ', 100 * fs)
createUnit('wk wks week weeks', 604800 * s)

# Area
createUnit('m2 square_metre_SI_unit', 1 * m ** 2, unitCategory='Area')

createUnit('acre_international  ac ', 4046.8564224 * m2)
createUnit('acre_US_survey  ac ', 4046.873 * m2)
createUnit('are', 100 * m2)
createUnit('barn', 1e-28 * m2)
createUnit('barony ', 1.618742e7 * m2)
createUnit('board  bd ', 7.74192e-3 * m2)
createUnit('boiler_horsepower_equivalent_direct_radiation  bhp_EDR ', 12.958174 * m2)
createUnit('circular_inch  circ_in ', 5.067075e-4 * m2)
createUnit('circular_mil  circular_thou  circ_mil ', 5.067075e-10 * m2)
createUnit('cord ', 1.48644864 * m2)
createUnit('dunam ', 1000 * m2)
createUnit('guntha ', 101.17 * m2)
createUnit('hectare  ha hectares', 10000 * m2)
createUnit('hide ', 5e5 * m2)
createUnit('rood  ro ', 1011.7141056 * m2)
createUnit('section ', 2.589988110336e6 * m2)
createUnit('shed sheds', 1e-52 * m2)
createUnit('square_roofing ', 9.290304 * m2)
createUnit('square_chain_international  sq_ch ', 404.68564224 * m2)
createUnit('square_chain_US_Survey  sq_ch ', 404.6873 * m2)
createUnit('square_foot  sq_ft ', 9.290304e-2 * m2)
createUnit('square_foot_US_Survey  sq_ft ', 9.29034116132749e-2 * m2)
createUnit('square_inch  sq_in ', 6.4516e-4 * m2)
createUnit('square_kilometre  km2 ', 1e6 * m2)
createUnit('square_link_Gunters_International  sq_lnk ', 4.0468564224e-2 * m2)
createUnit('square_link_Gunters_US_Survey  sq_lnk ', 4.046872e-2 * m2)
createUnit('square_link_Ramsdens  sq_lnk ', 0.09290304 * m2)
createUnit('square_mil  square_thou  sq_mil ', 6.4516e-10 * m2)
createUnit('square_mile  sq_mi ', 2.589988110336e6 * m2)
createUnit('square_mile_US_Survey  sq_mi ', 2.58999847e6 * m2)
createUnit('square_rod  square_pole  square_perch  sq_rd ', 25.29285264 * m2)
createUnit('square_yard_International  sq_yd ', 0.83612736 * m2)
createUnit('stremma ', 1000 * m2)
createUnit('township ', 9.323994e7 * m2)
createUnit('yardland ', 1.2e5 * m2)

# Volume
createUnit('m3 cubic_metre_SI_unit', 1 * m ** 3, unitCategory='Volume')

createUnit('ac_ft acre_foot', 1233.48183754752 * m3)
createUnit('acre_inch ', 102.79015312896 * m3)
createUnit('barrel_imperial  bl_imp ', 0.16365924 * m3)
createUnit('bbl barrel_petroleum  bl', 0.158987294928 * m3)
createUnit('barrel_US_dry  bl_US ', 0.115628198985075 * m3)
createUnit('barrel_US_fluid  fl_bl_US ', 0.119240471196 * m3)
createUnit('board_foot fbm ', 2.359737216e-3 * m3)
createUnit('bucket_imperial  bkt ', 0.01818436 * m3)
createUnit('bushel_imperial  bu_imp ', 0.03636872 * m3)
createUnit('bushel_US_dry_heaped  bu_US ', 0.0440488377086 * m3)
createUnit('bushel_US_dry_level  bu_US_lvl ', 0.03523907016688 * m3)
createUnit('butt_pipe ', 0.476961884784 * m3)
createUnit('coomb ', 0.14547488 * m3)
createUnit('cord_firewood ', 3.624556363776 * m3)
createUnit('cord_foot ', 0.453069545472 * m3)
createUnit('cubic_fathom  cu_fm ', 6.116438863872 * m3)
createUnit('cubic_foot  cu_ft cubic_feet ', 0.028316846592 * m3)
createUnit('cubic_inch  cu_in cubic_inches ', 16.387064e-6 * m3)
createUnit('cubic_mile  cu_mi ', 4168181825.440579584 * m3)
createUnit('cubic_yard cubic_yards cu_yd ', 0.764554857984 * m3)
createUnit('cup_breakfast ', 284.130625e-6 * m3)
createUnit('cup_Canadian  c_CA ', 227.3045e-6 * m3)
createUnit('cup_metric', 250.0e-6 * m3)
createUnit('cup_US_customary  c_US ', 236.5882365e-6 * m3)
createUnit('cup_US_food_nutrition_labeling  c_US ', 2.4e-4 * m3)
createUnit('dash_imperial ', 369.961751302083e-9 * m3)
createUnit('dash_US ', 308.057599609375e-9 * m3)
createUnit('dessertspoon_imperial ', 11.8387760416e-6 * m3)
createUnit('drop_imperial  gtt ', 98.6564670138e-9 * m3)
createUnit('drop_imperial_alt  gtt ', 77.886684e-9 * m3)
createUnit('drop_medical ', 83.03e-9 * m3)
createUnit('drop_medical ', 83.3e-9 * m3)
createUnit('drop_metric ', 50.0e-9 * m3)
createUnit('drop_US  gtt ', 82.14869322916e-9 * m3)
createUnit('drop_US_alt  gtt ', 64.85423149671e-9 * m3)
createUnit('drop_US_alt  gtt ', 51.34293326823e-9 * m3)
createUnit('fifth ', 757.0823568e-6 * m3)
createUnit('firkin ', 0.034068706056 * m3)
createUnit('fluid_drachm_imperial  fl_dr ', 3.5516328125e-6 * m3)
createUnit('fluid_dram_US  US_fluidram  fl_dr ', 3.6966911953125e-6 * m3)
createUnit('fluid_scruple_imperial  fl_s ', 1.18387760416e-6 * m3)
createUnit('gallon_beer  beer_gal ', 4.621152048e-3 * m3)
createUnit('gal_imp gallon_imperial', 4.54609e-3 * m3)
createUnit('gal_US gallon_US_dry', 4.40488377086e-3 * m3)
createUnit('gallon_US_fluid_Wine', 3.785411784e-3 * m3)
createUnit('gill_imperial  Noggin  gi_imp  nog ', 142.0653125e-6 * m3)
createUnit('gill_US  gi_US ', 118.29411825e-6 * m3)
createUnit('hogshead_imperial  hhd_imp ', 0.32731848 * m3)
createUnit('hogshead_US  hhd_US ', 0.238480942392 * m3)
createUnit('jigger_bartending ', 44.36e-6 * m3)
createUnit('kilderkin ', 0.08182962 * m3)
createUnit('lambda_unit ', 1e-9 * m3)
createUnit('last ', 2.9094976 * m3)
createUnit('litre  L litres', 0.001 * m3)
createUnit('load ', 1.4158423296 * m3)
createUnit('minim_imperial  minim ', 59.1938802083e-9 * m3)
createUnit('minim_US  minim ', 61.611519921875e-9 * m3)
createUnit('ounce_fluid_imperial  fl_oz_imp ', 28.4130625e-6 * m3)
createUnit('ounce_fluid_US_customary  US_fl_oz ', 29.5735295625e-6 * m3)
createUnit('ounce_fluid_US_food_nutrition_labeling  US_fl_oz ', 3e-5 * m3)
createUnit('peck_imperial  pk ', 9.09218e-3 * m3)
createUnit('peck_US_dry  pk ', 8.80976754172e-3 * m3)
createUnit('perch  per ', 0.700841953152 * m3)
createUnit('pinch_imperial ', 739.92350260416e-9 * m3)
createUnit('pinch_US ', 616.11519921875e-9 * m3)
createUnit('pint_imperial  pt_imp ', 568.26125e-6 * m3)
createUnit('pint_US_dry  pt_US_dry ', 550.6104713575e-6 * m3)
createUnit('pint_US_fluid  pt_US_fl ', 473.176473e-6 * m3)
createUnit('pony ', 22.180147171875e-6 * m3)
createUnit('pottle  quartern ', 2.273045e-3 * m3)
createUnit('quart_imperial  qt_imp ', 1.1365225e-3 * m3)
createUnit('quart_US_dry  qt_US ', 1.101220942715e-3 * m3)
createUnit('quart_US_fluid  qt_US ', 946.352946e-6 * m3)
createUnit('quarter_pail ', 0.29094976 * m3)
createUnit('register_ton ', 2.8316846592 * m3)
createUnit('sack_imperial  bag ', 0.10910616 * m3)
createUnit('sack_US ', 0.10571721050064 * m3)
createUnit('seam ', 0.28191256133504 * m3)
createUnit('shot ', 29.57e-6 * m3)
createUnit('strike_imperial ', 0.07273744 * m3)
createUnit('strike_US ', 0.07047814033376 * m3)
createUnit('tablespoon_Australian_metric ', 20.0e-6 * m3)
createUnit('tablespoon_Canadian  tbsp ', 14.20653125e-6 * m3)
createUnit('tablespoon_imperial  tbsp ', 17.7581640625e-6 * m3)
createUnit('tablespoon_metric ', 15.0e-6 * m3)
createUnit('tablespoon_US_customary  tbsp ', 14.7867647825e-6 * m3)
createUnit('tablespoon_US_food_nutrition_labeling  tbsp ', 1.5e-5 * m3)
createUnit('teaspoon_Canadian  tsp ', 4.735510416e-6 * m3)
createUnit('teaspoon_imperial  tsp ', 5.91938802083e-6 * m3)
createUnit('teaspoon_metric ', 5.0e-6 * m3)
createUnit('teaspoon_US_customary  tsp ', 4.928921595e-6 * m3)
createUnit('teaspoon_US_food_nutrition_labeling  tsp ', 5e-6 * m3)
createUnit('timber_foot ', 0.028316846592 * m3)
createUnit('ton_displacement ', 0.99108963072 * m3)
createUnit('ton_freight ', 1.13267386368 * m3)
createUnit('ton_water ', 1.01832416 * m3)
createUnit('tun ', 0.953923769568 * m3)
createUnit('wey_US ', 1.4095628066752 * m3)

# Magnetic field strength
createUnit('G Gauss', 1e-4 * T, mustCreateMetricPrefixes=True)

# Dynamic viscosity
createUnit('Pa_s pascal_second_SI_unit', 1 * Pa * s, unitCategory='Dynamic viscosity')
createUnit('poise_cgs_unit ', 0.1 * Pa * s)
createUnit('pound_per_foot_hour ', 4.133789e-4 * Pa * s)
createUnit('pound_per_foot_second ', 1.488164 * Pa * s)
createUnit('pound_force_second_per_square_foot ', 47.88026 * Pa * s)
createUnit('pound_force_second_per_square_inch ', 6894.757 * Pa * s)

# Kinematic viscosity
createUnit('St stokes_cgs_unit', 1e-4 * m**2 / s, unitCategory='Kinematic viscosity')

# Energy
createUnit('boe barrel_of_oil_equivalent', 6.12e9 * J)
createUnit('BTU BTUISO British_thermal_unit_ISO', 1.0545e3 * J)
createUnit('BTUIT British_thermal_unit_International_Table', 1.05505585262e3 * J)
createUnit('BTUmean British_thermal_unit_mean', 1.05587e3 * J)
createUnit('BTUth British_thermal_unit_thermochemical', 1.054350e3 * J)
createUnit('British_thermal_unit_39_F ',  1.05967e3 * J)
createUnit('British_thermal_unit_59_F ',  1.054804e3 * J)
createUnit('British_thermal_unit_60_F ',  1.05468e3 * J)
createUnit('British_thermal_unit_63_F ',  1.0546e3 * J)
createUnit('cal calIT calorie_International_Table', 4.1868 * J)
createUnit('calorie_mean  calmean', 4.19002 * J)
createUnit('calth calorie_thermochemical', 4.184 * J)
createUnit('calorie_3_98_C ', 4.2045 * J)
createUnit('calorie_15_C ', 4.1855 * J)
createUnit('calorie_20_C ', 4.1819 * J)
createUnit('CHUIT Celsius_heat_unit_International_Table', 1.899100534716e3 * J)
createUnit('cc scc cc_atm cubic_centimetre_of_atmosphere standard_cubic_centimetre', 0.101325 * J)
createUnit('scf cu_ft_atm cubic_foot_of_atmosphere standard_cubic_foot', 2.8692044809344e3 * J)
createUnit('cubic_foot_of_natural_gas', 1.05505585262e6 * J)
createUnit('scy cubic_yard_of_atmosphere  standard_cubic_yard  cu_yd_atm', 77.4685209852288e3 * J)
createUnit('eV electronvolt', 1.60217733e-19 * J)
createUnit('erg erg_cgs_unit', 1e-7 * J)
createUnit('ft_lbf foot_pound_force', 1.3558179483314004 * J)
createUnit('ft_pdl foot_poundal', 4.21401100938048e-2 * J)
createUnit('imp_gal_atm gallon_atmosphere_imperial', 460.63256925 * J)
createUnit('gallon_atmosphere_US  US_gal_atm ', 383.5568490138 * J)
createUnit('Eh hartree  atomic_unit_of_energy', 4.359744e-18 * J)
createUnit('hph horsepower_hour', 2.684519537696172792e6 * J)
createUnit('in_lbf inch_pound_force', 0.1129848290276167 * J)
createUnit('kcal Cal kilocalorie  large_calorie', 4.1868e3 * J)
createUnit('kWh kilowatt_hour  Board_of_Trade_Unit', 3.6e6 * J)
createUnit('litre_atmosphere  l_atm  sl ', 101.325 * J)
createUnit('quad ', 1.05505585262e18 * J)
createUnit('Ry rydberg', 2.179872e-18 * J)
createUnit('therm_EC', 105.505585262e6 * J)
createUnit('therm_US', 105.4804e6 * J)
createUnit('th thermie', 4.1868e6 * J)
createUnit('TCE ton_of_coal_equivalent', 29.3076e9 * J)
createUnit('TOE ton_of_oil_equivalent', 41.868e9 * J)
createUnit('tTNT ton_of_TNT', 4.184e9 * J)

# Volumetric flow
createUnit('m3ps cubic_metre_per_second_SI_unit',  1 * m3/s, unitCategory='Volumetric Flow')
m3ps.setRepresent(as_unit=m3ps, symbol='m3/s')
createUnit('cmh', m3/hr)

createUnit('CFM cfm cubic_foot_per_minute', 4.719474432e-4 * m3/s)
createUnit('CFS cfs cubic_foot_per_second',  0.028316846592 * m3/s)
createUnit('cubic_inch_per_minute', 2.7311773e-7 * m3/s)
createUnit('cubic_inch_per_second', 1.6387064e-5 * m3/s)
createUnit('GPD gallon_US_fluid_per_day', 4.381263638e-8 * m3/s)
createUnit('GPH gallon_US_fluid_per_hour', 1.051503273e-6 * m3/s)
createUnit('GPM gallon_US_fluid_per_minute', 6.30901964e-5 * m3/s)
createUnit('LPM litre_per_minute', 1.6e-5 * m3/s)

# Force
createUnit('atomic_unit_of_force ',  8.23872206e-8 * N)
createUnit('dyn dyne dynes dyne_cgs_unit', 1e-5 * N)
createUnit('kgf kp Gf kilogram_force kilopond grave_force', 9.80665 * N)
createUnit('kip kip_force kipf klbf ', 4.4482216152605e3 * N)
createUnit('mGf milligrave_force  gravet_force gf ', 9.80665 * mN)
createUnit('ozf ounce_force', 0.2780138509537812 * N)
createUnit('lbf pound_force', 4.4482216152605 * N)
createUnit('pdl poundal', 0.138254954376 * N)
createUnit('sn sthene_mts_unit', 1e3 * N)
createUnit('tnf ton_force', 8.896443230521e3 * N)

#Length
createUnit('nm nanometre  nanometres', 1e-9 * m)
createUnit('angstrom ', 0.1 * nm)
createUnit('AU astronomical_unit AU', 149597870700 * m)
createUnit('barleycorn ', 8.46e-3 * m)
createUnit('a0 bohr atomic_unit_of_length', 5.2917720859e-11 * m)
createUnit('cable_length_imperial ', 185.3184 * m)
createUnit('cable_length_International ', 185.2 * m)
createUnit('cable_length_US ', 219.456 * m)
createUnit('ch chain_Gunters_Surveyors', 20.11684 * m)
createUnit('cubit cubits ', 0.5 * m)
createUnit('ell  ', 1.143 * m)
createUnit('fm fathom', 1.8288 * m)
createUnit('fermi', 1e-15 * m)
createUnit('finger', 0.022225 * m)
createUnit('finger_cloth', 0.1143 * m)
createUnit('ft_Ben foot_Benoit', 0.304799735 * m)
createUnit('foot_Cape', 0.314858 * m)
createUnit('foot_Clarkes', 0.3047972654 * m)
createUnit('foot_Indian ft_Ind', 0.304799514 * m)
createUnit('ft foot feet foot_International', 0.3048 * m)
createUnit('foot_Sears ft_Sear', 0.30479947 * m)
createUnit('ft_US foot_US_Survey', 0.304800610 * m)
createUnit('F french_charriere', 0.3e-3 * m)
createUnit('fur furlong', 201.168 * m)
createUnit('hand', 0.1016 * m)
createUnit('inch inch_International', .0254 * m)
createUnit('lea league_land', 4828.032 * m)
createUnit('light_day ', 2.59020683712e13 * m)
createUnit('light_hour ', 1.0792528488e12 * m)
createUnit('light_minute ', 1.798754748e10 * m)
createUnit('light_second ', 299792458 * m)
createUnit('ly light_year', 9.4607304725808e15 * m)
createUnit('ln line', 0.002116 * m)
createUnit('lnk link_Gunters', 0.201168 * m)
createUnit('link_Ramsdens ', 0.3048 * m)
createUnit('mickey ', 1.27e-4 * m)
createUnit('micron', 1e-6 * m)
createUnit('mil  thou ', 2.54e-5 * m)
createUnit('mil_Sweden_and_Norway', 10000 * m)
createUnit('mile_geographical', 1853.7936 * m)
createUnit('mi mile mile_international', 1609.344 * m)
createUnit('mile_tactical_or_data', 1828.8 * m)
createUnit('mile_telegraph', 1855.3176 * m)
createUnit('mile_US_Survey', 1609.347219 * m)
createUnit('nail_cloth ', 0.05715 * m)
createUnit('NL nautical_league nl ', 5556 * m)
createUnit('nautical_mile_Admiralty  NM_Adm  nmi_Adm ', 1853.184 * m)
createUnit('NM nmi nautical_mile_international', 1852 * m)
createUnit('nautical_mile_US_pre_1954 ', 1853.248 * m)
createUnit('pace ', 0.762 * m)
createUnit('palm ', 0.0762 * m)
createUnit('parsec  pc ', 3.08567782e16 * m)
createUnit('pt point_American_English', 0.000351450 * m)
createUnit('point_Didot_European', 0.00037593985 * m)
createUnit('point_PostScript', 0.0003527 * m)
createUnit('point_TeX', 0.0003514598 * m)
createUnit('quarter ', 0.2286 * m)
createUnit('rod  pole  perch  rd ', 5.0292 * m)
createUnit('rope  rope ', 6.096 * m)
createUnit('span ', 0.2286 * m)
createUnit('spat  ', 1e12 * m)
createUnit('stick ', 0.0508 * m)
createUnit('pm stigma  bicron_picometre', 1e-12 * m)
createUnit('twp twip', 1.7638e-5 * m)
createUnit('xu x_unit siegbahn', 1.0021e-13 * m)
createUnit('yd yard yard_International', 0.9144 * m)

# Mass
createUnit('AMU atomic_mass_unit_unified', 1.66053873e-27 * kg)
createUnit('me atomic_unit_of_mass  electron_rest_mass', 9.10938215e-31 * kg)
createUnit('bag_coffee ', 60 * kg)
createUnit('bag_Portland_cement ', 42.63768278 * kg)
createUnit('barge ', 20411.65665 * kg)
createUnit('kt carat', 205.196548333 * mg)
createUnit('ct carat_metric', 200 * mg)
createUnit('clove ', 3.62873896 * kg)
createUnit('crith ', 89.9349 * mg)
createUnit('Da dalton', 1.66090210e-27 * kg)
createUnit('dram_apothecary troy  dr_t ', 3.8879346 * g)
createUnit('dram_avoirdupois  dr_av ', 1.7718451953125 * g)
createUnit('gamma ', 1e-6 * g)
createUnit('gr grain', 64.79891 * mg)
createUnit('hundredweight_long  long_cwt_or_cwt ', 50.80234544 * kg)
createUnit('hundredweight_short  cental  sh_cwt ', 45.359237 * kg)
createUnit('kip', 453.59237 * kg)
createUnit('mark ', 248.8278144 * g)
createUnit('mite ', 3.2399455 * mg)
createUnit('mite_metric ', 50 * mg)
createUnit('oz_t ounce_apothecary troy', 31.1034768 * g)
createUnit('oz_av ounce_avoirdupois', 28.349523125 * g)
createUnit('oz ounce_US_food_nutrition_labeling', 28 * g)
createUnit('pennyweight  dwt  pwt ', 1.55517384 * g)
createUnit('point ', 2 * mg)
createUnit('lb pound', 0.45359237 * kg)
createUnit('lb_av pound_avoirdupois', 0.45359237 * kg)
createUnit('pound_metric ', 500 * g)
createUnit('lb_t pound_troy', 0.3732417216 * kg)
createUnit('quarter_imperial ', 12.70058636 * kg)
createUnit('quarter_informal ', 226.796185 * kg)
createUnit('quarter_long_informal ', 254.0117272 * kg)
createUnit('q quintal_metric', 100 * kg)
createUnit('scruple_apothecary  s_ap ', 1.2959782 * g)
createUnit('sheet', 647.9891 * mg)
createUnit('slug geepound hyl', 14.593903 * kg)
createUnit('st stone', 6.35029318 * kg)
createUnit('ton_assay_long  AT ', 32.666667 * g)
createUnit('ton_assay_short  AT ', 29.166667 * g)
createUnit('ton_long long_tn_or_ton long_ton', 1016.0469088 * kg)
createUnit('ton_short sh_tn short_ton ', 907.18474 * kg)
createUnit('t tonne tonne_mts_unit metric_ton', 1000 * kg)
createUnit('wey ', 114.30527724 * kg)

# Power
createUnit('atmosphere_cubic_centimetre_per_minute  atm_ccm ', 1.68875e-3 * W)
createUnit('atmosphere_cubic_centimetre_per_second  atm_ccs ', 0.101325 * W)
createUnit('atmosphere_cubic_foot_per_hour  atm_cfh ', 0.797001244704 * W)
createUnit('atmosphere_cubic_foot_per_minute  atm_cfm ', 47.82007468224 * W)
createUnit('atmosphere_cubic_foot_per_second  atm_cfs ', 2.8692044809344e3 * W)
createUnit('BTU_International_Table_per_hour  BTUITph ', 0.293071 * W)
createUnit('BTU_International_Table_per_minute  BTUITpm ', 17.584264 * W)
createUnit('BTU_International_Table_per_second  BTUITps ', 1.05505585262e3 * W)
createUnit('calorie_International_Table_per_second  calITps ', 4.1868 * W)
createUnit('erg_per_second  ergps ', 1e-7 * W)
createUnit('foot_pound_force_per_hour ', 3.766161e-4 * W)
createUnit('foot_pound_force_per_minute ', 2.259696580552334e-2 * W)
createUnit('foot_pound_force_per_second ', 1.3558179483314004 * W)
createUnit('horsepower_boiler  bhp ', 9.810657e3 * W)
createUnit('horsepower_European_electrical  hp ', 736 * W)
createUnit('horsepower_imperial_electrical  hp ', 746 * W)
createUnit('horsepower_imperial_mechanical  hp ', 745.69987158227022 * W)
createUnit('horsepower_metric  hp ', 735.49875 * W)
createUnit('litre_atmosphere_per_minute ', 1.68875 * W)
createUnit('litre_atmosphere_per_second ', 101.325 * W)
createUnit('lusec lusec ', 1.333e-4 * W)
createUnit('poncelet  p ', 980.665 * W)
createUnit('square_foot_equivalent_direct_radiation  sq_ft_EDR ', 70.337057 * W)
createUnit('ton_of_air_conditioning ', 3504 * W)
createUnit('ton_of_refrigeration_imperial ', 3.938875e3 * W)
createUnit('ton_of_refrigeration_IT ', 3.516853e3 * W)

# Pressure
createUnit('atm atmosphere_standard', 101325 * Pa)
createUnit('atmosphere_technical  at ', 9.80665e4 * Pa)
createUnit('bar', 1e5 * Pa)
createUnit('barye_cgs_unit ', 0.1 * Pa)
createUnit('centimetre_of_mercury  cmHg ', 1.33322e3 * Pa)
createUnit('centimetre_of_water_4degC  cmH2O ', 98.0638 * Pa)
createUnit('foot_of_mercury_conventional  ftHg ', 40.63666e3 * Pa)
createUnit('foot_of_water_39_2_F  ftH2O ', 2.98898e3 * Pa)
createUnit('inch_of_mercury_conventional  inHg ', 3.386389e3 * Pa)
createUnit('inch_of_water_39_2_F  inH2O ', 249.082 * Pa)
createUnit('kilogram_force_per_square_millimetre ', 9.80665e6 * Pa)
createUnit('kip_per_square_inch  ksi ', 6.894757e6 * Pa)
createUnit('micron_micrometre_of_mercury  mHg ', 0.1333224 * Pa)
createUnit('mmHg millimetre_of_mercury', 133.3224 * Pa)
createUnit('millimetre_of_water_3_98_C  mmH2O ', 9.80638 * Pa)
createUnit('pz pieze_mts_unit  ', 1e3 * Pa)
createUnit('psf pound_per_square_foot', 47.88026 * Pa)
createUnit('psi pound_per_square_inch', 6.894757e3 * Pa)
createUnit('poundal_per_square_foot ', 1.488164 * Pa)
createUnit('short_ton_per_square_foot ', 95.760518e3 * Pa)
createUnit('torr', 133.3224 * Pa)

# Velocity
createUnit('metre_per_second_SI_unit ', 1 * m/s, unitCategory='Velocity')
metre_per_second_SI_unit.setRepresent(as_unit=metre_per_second_SI_unit, symbol='m/s')

createUnit('fph foot_per_hour', 8.466667e-5 * m/s)
createUnit('fpm foot_per_minute', 5.08e-3 * m/s)
createUnit('fps foot_per_second', 3.048e-1 * m/s)
createUnit('furlong_per_fortnight ', 1.663095e-4 * m/s)
createUnit('inch_per_hour  iph ', 7.05556e-6 * m/s)
createUnit('inch_per_minute  ipm ', 4.23333e-4 * m/s)
createUnit('inch_per_second  ips ', 2.54e-2 * m/s)
createUnit('kph kilometre_per_hour', 2.777778e-1 * m/s)
createUnit('kt kn knot', 0.514444 * m/s)
createUnit('knot_Admiralty', 0.514773 * m/s)
createUnit('M mach_number', 340 * m/s)
createUnit('mph mile_per_hour', 0.44704 * m/s)
createUnit('mile_per_minute  mpm ', 26.8224 * m/s)
createUnit('mile_per_second  mps ', 1609.344 * m/s)
createUnit('c speed_of_light_in_vacuum', 299792458 * m/s)
createUnit('speed_of_sound_in_air', 340 * m/s)

# Additional derived quantities
createUnit('kg_m3', kg/m3, unitCategory="Mass density")
kg_m3.setRepresent(as_unit=kg_m3, symbol='kg/m3')
#import pdb; pdb.set_trace()
createUnit('kg_hr', kg/hr, unitCategory="Mass flowrate")
kg_hr.setRepresent(as_unit=kg_hr, symbol='kg/hr')
createUnit('kmol_hr', kmol/hr, unitCategory="Molar flowrate")
kmol_hr.setRepresent(as_unit=kmol_hr, symbol='kmol/hr')
ncm = Ncm = (m3) * (101325*Pa) / (8.314*J/mol/K) / (273.15*K)
ncmh = Ncmh = ncm / hr
# NOTE 15 C:
scf = (ft) * (101325*Pa) / (8.314*J/mol/K) / ((273.15+15)*K)
scfm = scf / minute
scfd = scf / day
MMSCFD = scfd / 1e6
SP_OPEC = 101.560 * kPa
# NOTE! http://goldbook.iupac.org/S05910.html
SP_STP = 1e5 * Pa # http://goldbook.iupac.org/S06036.html
MMbbl = bbl / 1e6
MMscf = scf / 1e6
bcf = Bcf = scf / 1e9

# Engineering quantities
createUnit('kJ_kg_K', kJ/kg/K, unitCategory="Heat capacity mass")
kJ_kg_K.setRepresent(as_unit=kJ_kg_K, symbol='kJ/kg/K')
createUnit('kJ_kmol_K', kJ/kmol/K, unitCategory="Heat capacity mole")
kJ_kmol_K.setRepresent(as_unit=kJ_kmol_K, symbol='kJ/kmol/K')

createUnit('kJ_kg', kJ/kg, unitCategory="Specific enthalpy mass")
kJ_kg.setRepresent(as_unit=kJ_kg, symbol='kJ/kg')
createUnit('kJ_kmol', kJ/kmol, unitCategory="Specific enthalpy mole")
kJ_kmol.setRepresent(as_unit=kJ_kmol, symbol='kJ/kmol')

'''
createUnit('kJ_kg_K_entropy', kJ/kg/K, unitCategory="Specific entropy mass")
kJ_kg_K_entropy.setRepresent(as_unit=kJ_kg_K_entropy, symbol='kJ/kg/K')
createUnit('kJ_kmol_K_entropy', kJ/kg/K, unitCategory="Specific entropy mole")
kJ_kmol_K_entropy.setRepresent(as_unit=kJ_kmol_K_entropy, symbol='kJ/kmol/K')
'''

createUnit('W_m_K', W/m/K, unitCategory="Thermal conductivity")
W_m_K.setRepresent(as_unit=W_m_K, symbol='W/m/K')

createUnit('N_m', N/m, unitCategory="Surface tension")
N_m.setRepresent(as_unit=N_m, symbol='N/m')

createUnit('g_mol', g/mol, unitCategory="Molecular weight")
g_mol.setRepresent(as_unit=g_mol, symbol='g/mol')


# This is a decorator that will ensure arguments match declared units
def dimensions(**_params_):
    def check_types(_func_, _params_ = _params_):
        def modified(*args, **kw):
            if sys.version_info.major == 2:
                arg_names = _func_.func_code.co_varnames
            elif sys.version_info.major == 3:
                arg_names = _func_.__code__.co_varnames
            else:
                raise Exception('Invalid Python version!')
            kw.update(zip(arg_names, args))
            for name, category in _params_.items():
                param = kw[name]
                assert isinstance(param, Quantity), \
                    '''Parameter "{}" must be an instance of class Quantity
(and must be of unit type "{}").'''.format(name, category)
                assert param.unitCategory() == category, \
                    'Parameter "{}" must be unit type "{}".'.format(name, category)
            return _func_(**kw)
        modified.__name__ = _func_.__name__
        modified.__doc__ = _func_.__doc__
        # Py 3 only
        #modified.__annotations__ = _func_.__annotations__
        return modified
    # For IDEs, make sure the arg lists propagate through to the user
    return check_types


if __name__ == '__main__':
    print()
    print('*'*80)
    print()
    def test(text):
        '''Utility function for pretty-print test output.'''
        try:
            print('{:50}: {}'.format(text, eval(text)))
        except:
            print()
            print('Trying: ' + text)
            print(traceback.format_exc())
            print()

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

    ############################################################################

    from sys import getsizeof
    print(getsizeof(a))

    print()
    print('Testing Quantities')
    print('==================')
    print()
    #print 'QuantityType = {}'.format(QuantityType)
    #print 'Quantity Type of m is {}'.format(QuantityType[m.unit])
    print()
    print('Hz = {}'.format(Hz))
    print('kHz = {}'.format(kHz))
    print('MHz = {}'.format(MHz))
    print('GHz = {}'.format(GHz))

    def pbrk():
        print()
        print('='*20)
        print()
    pbrk()

    def lookupType(quantity):
        print('Quantity: {} Type: {}'.format(quantity, quantity.unitCategory()))

    lookupType(BTU)
    lookupType(lb)
    lookupType(200 * MW * 10 * d)
    #import pdb; pdb.set_trace()
    J.setRepresent(as_unit=GJ, symbol='GJ')
    lookupType(200 * MW * 10 * d)

    #########################################D:\Dropbox\Technical\codelibs\workspace\ipython_notebooks###################################

    pbrk()
    print('Example calculations:')
    pbrk()

    mass = 200*lb
    #import pdb; pdb.set_trace()
    print('mass = {}'.format(mass))
    flowrate = 40*mg/s
    print('flowrate = {}'.format(flowrate))
    s.setRepresent(as_unit=d, symbol='days')
    print('Time required to make final mass = {}'.format(mass / flowrate))

    ############################################################################

    pbrk()
    print('Checking the function decorator')
    pbrk()

    @dimensions(rho='Mass density', v='Velocity', L='Length', mu='Dynamic viscosity')
    def Reynolds_number(rho, v, L, mu):
        return rho * v * L / mu

    data = dict(rho=1000*kg/m3, v=12*m/s, L=5*inch, mu=1e-3*Pa*s)
    print('Re = {}'.format(Reynolds_number(**data)))

    data = dict(rho=1000*kg/m3, v=12*m/s, L=1.5*inch, mu=1.011e-3*Pa*s)
    Re = Reynolds_number(**data)
    print('Re = {:.2e}'.format(Reynolds_number(**data)))

    @dimensions(roughness='Length', Dh='Length', Re='Dimensionless')
    def friction_factor_Colebrook(roughness, Dh, Re):
        '''Returns friction factor.
        http://hal.archives-ouvertes.fr/docs/00/33/56/55/PDF/fast_colebrook.pdf
        '''
        K = roughness.convert(m) / Dh.convert(m)
        l = math.log(10)
        x1 = l * K * Re / 18.574
        x2 = math.log(l * Re.magnitude / 5.02)
        zj = x2 - 1./5.
        for i in range(2): # two iterations
            ej = (zj + math.log(x1 + zj) - x2) / (1. + x1 + zj)
            tol = (1. + x1 + zj + (1./2.)*ej) * ej * (x1 + zj) / (1. + x1 + zj + ej + (1./3.)*ej**2)
            zj = zj - tol

        return (l / 2.0 / zj)**2

    @dimensions(roughness='Length', Dh='Length', Re='Dimensionless')
    def friction_factor_Colebrook_Haaland(roughness, Dh, Re):
        K = roughness.convert(m) / Dh.convert(m)
        tmp = math.pow(K/3.7, 1.11) + 6.9 / Re
        inv = -1.8 * math.log10(tmp)
        return dimensionless * (1./inv)**2

    f = friction_factor_Colebrook(1e-6*m, 1.5*inch, Re)
    fH = friction_factor_Colebrook_Haaland(1e-6*m, 1.5*inch, Re)
    print('At Re = {}, friction factor = {}'.format(Re, f))
    print('At Re = {}, friction factorH = {}'.format(Re, fH))
    if isinstance(f, Quantity):
        print('f.unitCategory() = {}'.format(f.unitCategory()))
    #if isinstance(fH, Quantity):

    @dimensions(
        fD='Dimensionless', D='Length', rho='Mass density', v='Velocity', L='Length')
    def pressure_drop(fD, D, rho, v, L=1*m):
        '''Arguments are
            fD:  Darcy-Weisbach friction factor
            L:   Length of pipe (default 1 metre)
            D:   Diameter of pipe
            rho: Density of the fluid
            v:   Velocity of the fluid
        '''
        return fD * L / D * rho * v**2 / 2

    flow = 1*m3/s
    m.setRepresent(as_unit=inch, symbol='"')
    Pa.setRepresent(as_unit=bar, symbol='bar')
    for D in [x*inch for x in range(1, 11)]:
        v = flow / D**2 / math.pi * 4
        rho = 1000*kg/m3
        Re = Reynolds_number(rho=rho, v=v, L=D, mu=1e-3*Pa*s)
        f = friction_factor_Colebrook(1e-5*m, D, Re)
        print('Pressure drop at diameter {} = {}'.format(
            D, pressure_drop(f, D, rho, v, L=1*m)))

    pbrk()
    print('Few more checks')
    pbrk()

    v = 101*m/s
    print('101 m/s -> ft/hr = {}').format(v.convert(ft/hr))

    dbg = 1
    import numpy as np
    x = np.array([1, 2, 3])
