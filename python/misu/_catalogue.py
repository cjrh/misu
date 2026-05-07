"""Builds the misu unit catalogue at import time.

Ported from the original ``misulib.py``; arithmetic and unit-tracking are
delegated to the Rust extension (``misu._engine``). Everything in this
module lands as attributes on the ``misu`` package itself, which is what
existing user code (``from misu import kg, m, ...``) expects.
"""
from __future__ import annotations

import re
import sys

from misu import _engine
from misu._engine import (
    EIncompatibleUnits,
    Quantity,
    QuantityNP,
    addType,
    quantity_from_string,
)
from misu.SIprefixes import SIprefixes_sym

# We populate `misu`, the user-facing top-level package, not this module.
_target = sys.modules['misu']


def _set(name, value):
    setattr(_target, name, value)
    if isinstance(value, Quantity):
        _engine._unit_registry_set(name, value)


def createMetricPrefixes(symbol, skipfunction=None):
    """Inject SI-prefixed versions of `symbol` into the `misu` namespace."""
    base = getattr(_target, symbol)
    for prefix, info in SIprefixes_sym.items():
        if skipfunction and skipfunction(prefix):
            continue
        _set(f'{prefix}{symbol}', (10.0 ** int(info.exponent)) * base)


def createUnit(symbols, quantity, mustCreateMetricPrefixes=False, valdict=None,
               unitCategory=None, metricSkipFunction=None, notes=None):
    """Register a unit (or a group of synonyms) in the misu namespace."""
    if valdict:
        # The original API supports rebuilding a quantity from a dict mapping
        # base-symbol -> exponent. With the Rust core that means producing a
        # fresh Quantity with the right Dim. We synthesise it from the base
        # units already known on the misu namespace.
        base_units = ('m', 'kg', 's', 'A', 'K', 'ca', 'mole')
        unit_list = [float(valdict.get(s) or 0) for s in base_units]
        quantity = Quantity(quantity.magnitude, unit_list)

    first_symbol = symbols.strip().split(' ')[0].strip()
    if unitCategory:
        addType(quantity, unitCategory)
        quantity.setRepresent(as_unit=quantity, symbol=first_symbol)

    for symbol in symbols.split(' '):
        symbol = symbol.strip()
        if not symbol:
            continue
        _set(symbol, quantity)

    if mustCreateMetricPrefixes:
        createMetricPrefixes(first_symbol, metricSkipFunction)


def quantity_from_string_py(string):
    """Pythonic wrapper that handles the same surface syntax as before.

    The original implementation rewrote the input via regex into a Python
    expression and called eval(); we use the Rust parser instead, but
    keep the same friendly behaviour: spaces are implicit ``*``, ``^`` is
    exponentiation.
    """
    string = re.sub(r'([a-zA-Z0-9])(\s+)([a-zA-Z0-9])', r'\1*\3', string)
    return quantity_from_string(string)


# -------------------------------------------------------------------------
# Population of units. This is a verbatim port of the misulib.py catalogue;
# only the helpers above changed.

def populate():
    # Dimensionless --------------------------------------------------------
    dimensionless = Quantity(1.0)
    addType(dimensionless, 'Dimensionless')
    _set('dimensionless', dimensionless)

    # Root units (each has a base-Dim coordinate of 1 in exactly one slot)
    createUnit('m metre metres', Quantity(1.0), valdict=dict(m=1.0),
               mustCreateMetricPrefixes=True, unitCategory='Length')

    createUnit('g gram grams', Quantity(1.0e-3), valdict=dict(kg=1.0),
               mustCreateMetricPrefixes=True, unitCategory='Mass')
    _target.g.setRepresent(as_unit=_target.kg, symbol='kg')

    createUnit('s second sec seconds secs', Quantity(1.0), valdict=dict(s=1.0),
               mustCreateMetricPrefixes=True, unitCategory='Time',
               metricSkipFunction=lambda p: p == 'a')

    createUnit('A ampere amperes amp amps', Quantity(1.0), valdict=dict(A=1.0),
               mustCreateMetricPrefixes=True, unitCategory='Current')

    createUnit('K kelvin', Quantity(1.0),
               valdict=dict(K=1.0), mustCreateMetricPrefixes=True,
               unitCategory='Temperature')
    createUnit('R rankine', _target.K * 5. / 9.)

    createUnit('ca candela cd', Quantity(1.0), valdict=dict(ca=1.0),
               mustCreateMetricPrefixes=False, unitCategory='Luminous intensity')
    createUnit('mol mole moles', Quantity(1.0), valdict=dict(mole=1.0),
               mustCreateMetricPrefixes=True, unitCategory='Substance')
    createMetricPrefixes('mole')

    # Derived units --------------------------------------------------------
    s = _target.s
    m = _target.m
    kg = _target.kg
    K = _target.K
    A = _target.A
    cd = _target.cd
    mol = _target.mol

    createUnit('Hz hertz', 1 / s, mustCreateMetricPrefixes=True, unitCategory='Frequency')
    createUnit('N newton', kg * m / s**2, mustCreateMetricPrefixes=True, unitCategory='Force')
    createUnit('Pa pascal', _target.N / m**2, mustCreateMetricPrefixes=True, unitCategory='Pressure')
    createUnit('J joule', _target.N * m, mustCreateMetricPrefixes=True, unitCategory='Energy')
    createUnit('W watt', _target.J / s, mustCreateMetricPrefixes=True, unitCategory='Power')
    createUnit('C coulomb', s * A, mustCreateMetricPrefixes=True, unitCategory='Charge')
    createUnit('V volt', _target.W / A, mustCreateMetricPrefixes=True, unitCategory='Voltage')
    createUnit('F farad', _target.C / _target.V, mustCreateMetricPrefixes=True, unitCategory='Capacitance')

    createUnit('ohm', _target.V / A, mustCreateMetricPrefixes=True, unitCategory='Resistance')
    createUnit('S siemens', 1 / _target.ohm, mustCreateMetricPrefixes=False, unitCategory='Conductance')
    createUnit('Wb weber', _target.J / A, mustCreateMetricPrefixes=False, unitCategory='Magnetic flux')
    createUnit('T tesla', _target.N / A / m, mustCreateMetricPrefixes=True, unitCategory='Magnetic field strength')

    createUnit('H henry', _target.V * s / A, mustCreateMetricPrefixes=True, unitCategory='Magnetic field strength')
    createUnit('lumen lm', cd * _target.J, mustCreateMetricPrefixes=False, unitCategory='Luminous flux')
    createUnit('lux lx', _target.lm / m**2, mustCreateMetricPrefixes=False, unitCategory='Luminous flux')

    # ---- Time ------------------------------------------------------------
    createUnit('minute mins minutes', 60 * s)
    minutes = _target.minutes
    createUnit('yr year years year_Gregorian', 31556952 * s)
    years = _target.years
    createUnit('year_Julian', 31557600 * s)
    createUnit('year_sidereal', 31558149.7632 * s)
    createUnit('year_tropical', 31556925 * s)
    createUnit('au atomic_unit_of_time', 2.418884254e-17 * s)
    createUnit('Callippic_cycle', 2.3983776e9 * s)
    createUnit('century centuries', 100 * years)
    createUnit('d day days', 86400 * s)
    day = _target.day
    createUnit('day_sidereal', 86164.1 * s)
    createUnit('dec decade decades', 10 * years)
    createUnit('fn fortnight fortnights', 1209600 * s)
    createUnit('helek', 3.3 * s)
    createUnit('Hipparchic_cycle', 9.593424e9 * s)
    createUnit('hr hour hrs hours', 3600 * s)
    hr = _target.hr
    createUnit('j jiffy', .016 * s)
    createUnit('ja jiffy_alternate', 10 * _target.ms)
    createUnit('ke_quarter_of_an_hour', 15 * minutes)
    createUnit('ke_traditional', 14.4 * minutes)
    createUnit('lustre  lustrum', 1.5768e8 * s)
    createUnit('Metonic_cycle  enneadecaeteris', 5.99616e8 * s)
    createUnit('millennium', 1000 * years)
    createUnit('moment', 90 * s)
    createUnit('month_full  mo', 2592000 * s)
    createUnit('month_Greg_avg  mo', 2.6297e6 * s)
    createUnit('month_hollow  mo', 2505600 * s)
    createUnit('month_synodic  mo', 2.551e6 * s)
    createUnit('octaeteris', 2.524608e8 * s)
    createUnit('Planck_time', 1.351211868e-43 * s)
    createUnit('shake shakes', 10 * _target.ns)
    createUnit('sigma', 1 * _target.us)
    createUnit('Sothic_cycle', 4.6074096e10 * s)
    createUnit('svedberg  S', 100 * _target.fs)
    createUnit('wk wks week weeks', 604800 * s)

    # ---- Area ------------------------------------------------------------
    createUnit('m2 square_metre_SI_unit', m ** 2, unitCategory='Area')
    m2 = _target.m2
    for line in _AREA:
        _create(line, m2)

    # ---- Volume ----------------------------------------------------------
    createUnit('m3 cubic_metre_SI_unit', m ** 3, unitCategory='Volume')
    m3 = _target.m3
    for line in _VOLUME:
        _create(line, m3)

    # ---- Magnetic field strength
    createUnit('G Gauss', 1e-4 * _target.T, mustCreateMetricPrefixes=True)

    # ---- Dynamic viscosity
    Pa = _target.Pa
    createUnit('Pa_s pascal_second_SI_unit', Pa * s, unitCategory='Dynamic viscosity')
    for line in _DYNAMIC_VISCOSITY:
        _create(line, Pa * s)

    # ---- Kinematic viscosity
    createUnit('St stokes_cgs_unit', 1e-4 * m**2 / s, unitCategory='Kinematic viscosity')

    # ---- Energy
    J = _target.J
    for line in _ENERGY:
        _create(line, J)

    # ---- Volumetric flow
    createUnit('m3ps cubic_metre_per_second_SI_unit', m3 / s, unitCategory='Volumetric Flow')
    _target.m3ps.setRepresent(as_unit=_target.m3ps, symbol='m3/s')
    createUnit('cmh', m3 / hr)
    for line in _VOL_FLOW:
        _create(line, m3 / s)

    # ---- Force
    N = _target.N
    for line in _FORCE:
        _create(line, N)

    # ---- Length
    for line in _LENGTH:
        _create(line, m)

    # ---- Mass
    for line in _MASS:
        _create(line, kg)

    # ---- Power
    W = _target.W
    for line in _POWER:
        _create(line, W)

    # ---- Pressure
    for line in _PRESSURE:
        _create(line, Pa)

    # ---- Velocity
    createUnit('metre_per_second_SI_unit', m / s, unitCategory='Velocity')
    _target.metre_per_second_SI_unit.setRepresent(
        as_unit=_target.metre_per_second_SI_unit, symbol='m/s')
    for line in _VELOCITY:
        _create(line, m / s)

    # ---- Additional derived
    createUnit('kg_m3', kg / m3, unitCategory='Mass density')
    _target.kg_m3.setRepresent(as_unit=_target.kg_m3, symbol='kg/m3')
    createUnit('kg_hr', kg / hr, unitCategory='Mass flowrate')
    _target.kg_hr.setRepresent(as_unit=_target.kg_hr, symbol='kg/hr')
    createUnit('kmol_hr', _target.kmol / hr, unitCategory='Molar flowrate')
    _target.kmol_hr.setRepresent(as_unit=_target.kmol_hr, symbol='kmol/hr')

    ncm = (m3) * (101325 * Pa) / (8.314 * J / mol / K) / (273.15 * K)
    _set('ncm', ncm); _set('Ncm', ncm)
    ncmh = ncm / hr
    _set('ncmh', ncmh); _set('Ncmh', ncmh)
    scf = (_target.ft) * (101325 * Pa) / (8.314 * J / mol / K) / ((273.15 + 15) * K)
    _set('scf', scf)
    scfm = scf / _target.minute
    _set('scfm', scfm)
    scfd = scf / day
    _set('scfd', scfd)
    _set('MMSCFD', scfd / 1e6)
    _set('SP_OPEC', 101.560 * _target.kPa)
    _set('SP_STP', 1e5 * Pa)
    _set('MMbbl', _target.bbl / 1e6)
    _set('MMscf', scf / 1e6)
    bcf = scf / 1e9
    _set('bcf', bcf); _set('Bcf', bcf)

    # Engineering quantities
    kJ = _target.kJ
    kmol = _target.kmol
    createUnit('kJ_kg_K', kJ / kg / K, unitCategory='Heat capacity mass')
    _target.kJ_kg_K.setRepresent(as_unit=_target.kJ_kg_K, symbol='kJ/kg/K')
    createUnit('kJ_kmol_K', kJ / kmol / K, unitCategory='Heat capacity mole')
    _target.kJ_kmol_K.setRepresent(as_unit=_target.kJ_kmol_K, symbol='kJ/kmol/K')

    createUnit('kJ_kg', kJ / kg, unitCategory='Specific enthalpy mass')
    _target.kJ_kg.setRepresent(as_unit=_target.kJ_kg, symbol='kJ/kg')
    createUnit('kJ_kmol', kJ / kmol, unitCategory='Specific enthalpy mole')
    _target.kJ_kmol.setRepresent(as_unit=_target.kJ_kmol, symbol='kJ/kmol')

    createUnit('W_m_K', W / m / K, unitCategory='Thermal conductivity')
    _target.W_m_K.setRepresent(as_unit=_target.W_m_K, symbol='W/m/K')

    createUnit('N_m', N / m, unitCategory='Surface tension')
    _target.N_m.setRepresent(as_unit=_target.N_m, symbol='N/m')

    createUnit('g_mol', _target.g / mol, unitCategory='Molecular weight')
    _target.g_mol.setRepresent(as_unit=_target.g_mol, symbol='g/mol')


def _create(line, base):
    """Helper used by ``populate`` to register a unit from a (symbols, factor) pair."""
    symbols, factor = line
    createUnit(symbols, factor * base)


# Lists of (space-separated synonyms, scalar factor relative to base)
# ported from misulib.py.
_AREA = [
    ('acre_international ac', 4046.8564224),
    ('acre_US_survey ac_us', 4046.873),
    ('are', 100.0),
    ('barn', 1e-28),
    ('barony', 1.618742e7),
    ('board bd', 7.74192e-3),
    ('boiler_horsepower_equivalent_direct_radiation bhp_EDR', 12.958174),
    ('circular_inch circ_in', 5.067075e-4),
    ('circular_mil circular_thou circ_mil', 5.067075e-10),
    ('cord', 1.48644864),
    ('dunam', 1000.0),
    ('guntha', 101.17),
    ('hectare ha hectares', 10000.0),
    ('hide', 5e5),
    ('rood ro', 1011.7141056),
    ('section', 2.589988110336e6),
    ('shed sheds', 1e-52),
    ('square_roofing', 9.290304),
    ('square_chain_international sq_ch', 404.68564224),
    ('square_chain_US_Survey sq_ch_us', 404.6873),
    ('square_foot sq_ft', 9.290304e-2),
    ('square_foot_US_Survey sq_ft_us', 9.29034116132749e-2),
    ('square_inch sq_in', 6.4516e-4),
    ('square_kilometre km2', 1e6),
    ('square_link_Gunters_International sq_lnk', 4.0468564224e-2),
    ('square_link_Gunters_US_Survey sq_lnk_us', 4.046872e-2),
    ('square_link_Ramsdens sq_lnk_r', 0.09290304),
    ('square_mil square_thou sq_mil', 6.4516e-10),
    ('square_mile sq_mi', 2.589988110336e6),
    ('square_mile_US_Survey sq_mi_us', 2.58999847e6),
    ('square_rod square_pole square_perch sq_rd', 25.29285264),
    ('square_yard_International sq_yd', 0.83612736),
    ('stremma', 1000.0),
    ('township', 9.323994e7),
    ('yardland', 1.2e5),
]

_VOLUME = [
    ('ac_ft acre_foot', 1233.48183754752),
    ('acre_inch', 102.79015312896),
    ('barrel_imperial bl_imp', 0.16365924),
    ('bbl barrel_petroleum bl', 0.158987294928),
    ('barrel_US_dry bl_US', 0.115628198985075),
    ('barrel_US_fluid fl_bl_US', 0.119240471196),
    ('board_foot fbm', 2.359737216e-3),
    ('bucket_imperial bkt', 0.01818436),
    ('bushel_imperial bu_imp', 0.03636872),
    ('bushel_US_dry_heaped bu_US', 0.0440488377086),
    ('bushel_US_dry_level bu_US_lvl', 0.03523907016688),
    ('butt_pipe', 0.476961884784),
    ('coomb', 0.14547488),
    ('cord_firewood', 3.624556363776),
    ('cord_foot', 0.453069545472),
    ('cubic_fathom cu_fm', 6.116438863872),
    ('cubic_foot cu_ft cubic_feet', 0.028316846592),
    ('cubic_inch cu_in cubic_inches', 16.387064e-6),
    ('cubic_mile cu_mi', 4168181825.440579584),
    ('cubic_yard cubic_yards cu_yd', 0.764554857984),
    ('cup_breakfast', 284.130625e-6),
    ('cup_Canadian c_CA', 227.3045e-6),
    ('cup_metric', 250.0e-6),
    ('cup_US_customary c_US', 236.5882365e-6),
    ('cup_US_food_nutrition_labeling c_US_fnl', 2.4e-4),
    ('dash_imperial', 369.961751302083e-9),
    ('dash_US', 308.057599609375e-9),
    ('dessertspoon_imperial', 11.8387760416e-6),
    ('drop_imperial gtt', 98.6564670138e-9),
    ('drop_medical', 83.3e-9),
    ('drop_metric', 50.0e-9),
    ('drop_US gtt_US', 82.14869322916e-9),
    ('fifth', 757.0823568e-6),
    ('firkin', 0.034068706056),
    ('fluid_drachm_imperial fl_dr', 3.5516328125e-6),
    ('fluid_dram_US US_fluidram fl_dr_US', 3.6966911953125e-6),
    ('fluid_scruple_imperial fl_s', 1.18387760416e-6),
    ('gallon_beer beer_gal', 4.621152048e-3),
    ('gal_imp gallon_imperial', 4.54609e-3),
    ('gal_US gallon_US_dry', 4.40488377086e-3),
    ('gallon_US_fluid_Wine', 3.785411784e-3),
    ('gill_imperial Noggin gi_imp nog', 142.0653125e-6),
    ('gill_US gi_US', 118.29411825e-6),
    ('hogshead_imperial hhd_imp', 0.32731848),
    ('hogshead_US hhd_US', 0.238480942392),
    ('jigger_bartending', 44.36e-6),
    ('kilderkin', 0.08182962),
    ('lambda_unit', 1e-9),
    ('last', 2.9094976),
    ('litre L litres', 0.001),
    ('load', 1.4158423296),
    ('minim_imperial minim', 59.1938802083e-9),
    ('minim_US minim_us', 61.611519921875e-9),
    ('ounce_fluid_imperial fl_oz_imp', 28.4130625e-6),
    ('ounce_fluid_US_customary US_fl_oz', 29.5735295625e-6),
    ('ounce_fluid_US_food_nutrition_labeling US_fl_oz_fnl', 3e-5),
    ('peck_imperial pk', 9.09218e-3),
    ('peck_US_dry pk_us', 8.80976754172e-3),
    ('perch per', 0.700841953152),
    ('pinch_imperial', 739.92350260416e-9),
    ('pinch_US', 616.11519921875e-9),
    ('pint_imperial pt_imp', 568.26125e-6),
    ('pint_US_dry pt_US_dry', 550.6104713575e-6),
    ('pint_US_fluid pt_US_fl', 473.176473e-6),
    ('pony', 22.180147171875e-6),
    ('pottle quartern', 2.273045e-3),
    ('quart_imperial qt_imp', 1.1365225e-3),
    ('quart_US_dry qt_US', 1.101220942715e-3),
    ('quart_US_fluid qt_US_fl', 946.352946e-6),
    ('quarter_pail', 0.29094976),
    ('register_ton', 2.8316846592),
    ('sack_imperial bag', 0.10910616),
    ('sack_US', 0.10571721050064),
    ('seam', 0.28191256133504),
    ('shot', 29.57e-6),
    ('strike_imperial', 0.07273744),
    ('strike_US', 0.07047814033376),
    ('tablespoon_Australian_metric', 20.0e-6),
    ('tablespoon_Canadian tbsp', 14.20653125e-6),
    ('tablespoon_imperial tbsp_imp', 17.7581640625e-6),
    ('tablespoon_metric', 15.0e-6),
    ('tablespoon_US_customary tbsp_us', 14.7867647825e-6),
    ('tablespoon_US_food_nutrition_labeling tbsp_us_fnl', 1.5e-5),
    ('teaspoon_Canadian tsp', 4.735510416e-6),
    ('teaspoon_imperial tsp_imp', 5.91938802083e-6),
    ('teaspoon_metric', 5.0e-6),
    ('teaspoon_US_customary tsp_us', 4.928921595e-6),
    ('teaspoon_US_food_nutrition_labeling tsp_us_fnl', 5e-6),
    ('timber_foot', 0.028316846592),
    ('ton_displacement', 0.99108963072),
    ('ton_freight', 1.13267386368),
    ('ton_water', 1.01832416),
    ('tun', 0.953923769568),
    ('wey_US', 1.4095628066752),
]

_DYNAMIC_VISCOSITY = [
    ('poise_cgs_unit', 0.1),
    ('pound_per_foot_hour', 4.133789e-4),
    ('pound_per_foot_second', 1.488164),
    ('pound_force_second_per_square_foot', 47.88026),
    ('pound_force_second_per_square_inch', 6894.757),
]

_ENERGY = [
    ('boe barrel_of_oil_equivalent', 6.12e9),
    ('BTU BTUISO British_thermal_unit_ISO', 1.0545e3),
    ('BTUIT British_thermal_unit_International_Table', 1.05505585262e3),
    ('BTUmean British_thermal_unit_mean', 1.05587e3),
    ('BTUth British_thermal_unit_thermochemical', 1.054350e3),
    ('British_thermal_unit_39_F', 1.05967e3),
    ('British_thermal_unit_59_F', 1.054804e3),
    ('British_thermal_unit_60_F', 1.05468e3),
    ('British_thermal_unit_63_F', 1.0546e3),
    ('cal calIT calorie_International_Table', 4.1868),
    ('calorie_mean calmean', 4.19002),
    ('calth calorie_thermochemical', 4.184),
    ('calorie_3_98_C', 4.2045),
    ('calorie_15_C', 4.1855),
    ('calorie_20_C', 4.1819),
    ('CHUIT Celsius_heat_unit_International_Table', 1.899100534716e3),
    ('cc scc cc_atm cubic_centimetre_of_atmosphere standard_cubic_centimetre', 0.101325),
    ('cu_ft_atm cubic_foot_of_atmosphere standard_cubic_foot', 2.8692044809344e3),
    ('cubic_foot_of_natural_gas', 1.05505585262e6),
    ('scy cubic_yard_of_atmosphere standard_cubic_yard cu_yd_atm', 77.4685209852288e3),
    ('eV electronvolt', 1.60217733e-19),
    ('erg erg_cgs_unit', 1e-7),
    ('ft_lbf foot_pound_force', 1.3558179483314004),
    ('ft_pdl foot_poundal', 4.21401100938048e-2),
    ('imp_gal_atm gallon_atmosphere_imperial', 460.63256925),
    ('gallon_atmosphere_US US_gal_atm', 383.5568490138),
    ('Eh hartree atomic_unit_of_energy', 4.359744e-18),
    ('hph horsepower_hour', 2.684519537696172792e6),
    ('in_lbf inch_pound_force', 0.1129848290276167),
    ('kcal Cal kilocalorie large_calorie', 4.1868e3),
    ('kWh kilowatt_hour Board_of_Trade_Unit', 3.6e6),
    ('litre_atmosphere l_atm sl', 101.325),
    ('quad', 1.05505585262e18),
    ('Ry rydberg', 2.179872e-18),
    ('therm_EC', 105.505585262e6),
    ('therm_US', 105.4804e6),
    ('th thermie', 4.1868e6),
    ('TCE ton_of_coal_equivalent', 29.3076e9),
    ('TOE ton_of_oil_equivalent', 41.868e9),
    ('tTNT ton_of_TNT', 4.184e9),
]

_VOL_FLOW = [
    ('CFM cfm cubic_foot_per_minute', 4.719474432e-4),
    ('CFS cfs cubic_foot_per_second', 0.028316846592),
    ('cubic_inch_per_minute', 2.7311773e-7),
    ('cubic_inch_per_second', 1.6387064e-5),
    ('GPD gallon_US_fluid_per_day', 4.381263638e-8),
    ('GPH gallon_US_fluid_per_hour', 1.051503273e-6),
    ('GPM gallon_US_fluid_per_minute', 6.30901964e-5),
    ('LPM litre_per_minute', 1.6e-5),
]

_FORCE = [
    ('atomic_unit_of_force', 8.23872206e-8),
    ('dyn dyne dynes dyne_cgs_unit', 1e-5),
    ('kgf kp Gf kilogram_force kilopond grave_force', 9.80665),
    ('kip kip_force kipf klbf', 4.4482216152605e3),
    ('mGf milligrave_force gravet_force gf', 9.80665e-3),
    ('ozf ounce_force', 0.2780138509537812),
    ('lbf pound_force', 4.4482216152605),
    ('pdl poundal', 0.138254954376),
    ('sn sthene_mts_unit', 1e3),
    ('tnf ton_force', 8.896443230521e3),
]

_LENGTH = [
    ('nm nanometre nanometres', 1e-9),
    ('angstrom', 0.1e-9),
    ('AU astronomical_unit', 149597870700.0),
    ('barleycorn', 8.46e-3),
    ('a0 bohr atomic_unit_of_length', 5.2917720859e-11),
    ('cable_length_imperial', 185.3184),
    ('cable_length_International', 185.2),
    ('cable_length_US', 219.456),
    ('ch chain_Gunters_Surveyors', 20.11684),
    ('cubit cubits', 0.5),
    ('ell', 1.143),
    ('fm fathom', 1.8288),
    ('fermi', 1e-15),
    ('finger', 0.022225),
    ('finger_cloth', 0.1143),
    ('ft_Ben foot_Benoit', 0.304799735),
    ('foot_Cape', 0.314858),
    ('foot_Clarkes', 0.3047972654),
    ('foot_Indian ft_Ind', 0.304799514),
    ('ft foot feet foot_International', 0.3048),
    ('foot_Sears ft_Sear', 0.30479947),
    ('ft_US foot_US_Survey', 0.304800610),
    ('french_charriere', 0.3e-3),
    ('fur furlong', 201.168),
    ('hand', 0.1016),
    ('inch inch_International', .0254),
    ('lea league_land', 4828.032),
    ('light_day', 2.59020683712e13),
    ('light_hour', 1.0792528488e12),
    ('light_minute', 1.798754748e10),
    ('light_second', 299792458.0),
    ('ly light_year', 9.4607304725808e15),
    ('ln line', 0.002116),
    ('lnk link_Gunters', 0.201168),
    ('link_Ramsdens', 0.3048),
    ('mickey', 1.27e-4),
    ('micron', 1e-6),
    ('mil thou', 2.54e-5),
    ('mil_Sweden_and_Norway', 10000.0),
    ('mile_geographical', 1853.7936),
    ('mi mile mile_international', 1609.344),
    ('mile_tactical_or_data', 1828.8),
    ('mile_telegraph', 1855.3176),
    ('mile_US_Survey', 1609.347219),
    ('nail_cloth', 0.05715),
    ('NL nautical_league', 5556.0),
    ('nautical_mile_Admiralty NM_Adm nmi_Adm', 1853.184),
    ('NM nmi nautical_mile_international', 1852.0),
    ('nautical_mile_US_pre_1954', 1853.248),
    ('pace', 0.762),
    ('palm', 0.0762),
    ('parsec pc', 3.08567782e16),
    ('pt point_American_English', 0.000351450),
    ('point_Didot_European', 0.00037593985),
    ('point_PostScript', 0.0003527),
    ('point_TeX', 0.0003514598),
    ('quarter', 0.2286),
    ('rod pole_perch rd', 5.0292),
    ('rope', 6.096),
    ('span', 0.2286),
    ('spat', 1e12),
    ('stick', 0.0508),
    ('pm stigma bicron_picometre', 1e-12),
    ('twp twip', 1.7638e-5),
    ('xu x_unit siegbahn', 1.0021e-13),
    ('yd yard yard_International', 0.9144),
]

_MASS = [
    ('AMU atomic_mass_unit_unified', 1.66053873e-27),
    ('me atomic_unit_of_mass electron_rest_mass', 9.10938215e-31),
    ('bag_coffee', 60.0),
    ('bag_Portland_cement', 42.63768278),
    ('barge', 20411.65665),
    ('kt_carat', 205.196548333e-6),
    ('ct carat_metric', 200e-6),
    ('clove', 3.62873896),
    ('crith', 89.9349e-6),
    ('Da dalton', 1.66090210e-27),
    ('dram_apothecary_troy dr_t', 3.8879346e-3),
    ('dram_avoirdupois dr_av', 1.7718451953125e-3),
    ('gamma', 1e-9),
    ('gr grain', 64.79891e-6),
    ('hundredweight_long long_cwt_or_cwt', 50.80234544),
    ('hundredweight_short cental sh_cwt', 45.359237),
    ('kip_mass', 453.59237),
    ('mark', 248.8278144e-3),
    ('mite', 3.2399455e-6),
    ('mite_metric', 50e-6),
    ('oz_t ounce_apothecary_troy', 31.1034768e-3),
    ('oz_av ounce_avoirdupois', 28.349523125e-3),
    ('oz ounce_US_food_nutrition_labeling', 28e-3),
    ('pennyweight dwt pwt', 1.55517384e-3),
    ('point_mass', 2e-6),
    ('lb pound', 0.45359237),
    ('lb_av pound_avoirdupois', 0.45359237),
    ('pound_metric', 0.5),
    ('lb_t pound_troy', 0.3732417216),
    ('quarter_imperial', 12.70058636),
    ('quarter_informal', 226.796185),
    ('quarter_long_informal', 254.0117272),
    ('q quintal_metric', 100.0),
    ('scruple_apothecary s_ap', 1.2959782e-3),
    ('sheet', 647.9891e-6),
    ('slug geepound hyl', 14.593903),
    ('st stone', 6.35029318),
    ('ton_assay_long AT', 32.666667e-3),
    ('ton_assay_short AT_short', 29.166667e-3),
    ('ton_long long_tn_or_ton long_ton', 1016.0469088),
    ('ton_short sh_tn short_ton', 907.18474),
    ('t tonne tonne_mts_unit metric_ton', 1000.0),
    ('wey', 114.30527724),
]

_POWER = [
    ('atmosphere_cubic_centimetre_per_minute atm_ccm', 1.68875e-3),
    ('atmosphere_cubic_centimetre_per_second atm_ccs', 0.101325),
    ('atmosphere_cubic_foot_per_hour atm_cfh', 0.797001244704),
    ('atmosphere_cubic_foot_per_minute atm_cfm', 47.82007468224),
    ('atmosphere_cubic_foot_per_second atm_cfs', 2.8692044809344e3),
    ('BTU_International_Table_per_hour BTUITph', 0.293071),
    ('BTU_International_Table_per_minute BTUITpm', 17.584264),
    ('BTU_International_Table_per_second BTUITps', 1.05505585262e3),
    ('calorie_International_Table_per_second calITps', 4.1868),
    ('erg_per_second ergps', 1e-7),
    ('foot_pound_force_per_hour', 3.766161e-4),
    ('foot_pound_force_per_minute', 2.259696580552334e-2),
    ('foot_pound_force_per_second', 1.3558179483314004),
    ('horsepower_boiler bhp', 9.810657e3),
    ('horsepower_European_electrical hp_eu', 736.0),
    ('horsepower_imperial_electrical hp_imp_e', 746.0),
    ('horsepower_imperial_mechanical hp', 745.69987158227022),
    ('horsepower_metric hp_metric', 735.49875),
    ('litre_atmosphere_per_minute', 1.68875),
    ('litre_atmosphere_per_second', 101.325),
    ('lusec', 1.333e-4),
    ('poncelet p', 980.665),
    ('square_foot_equivalent_direct_radiation sq_ft_EDR', 70.337057),
    ('ton_of_air_conditioning', 3504.0),
    ('ton_of_refrigeration_imperial', 3.938875e3),
    ('ton_of_refrigeration_IT', 3.516853e3),
]

_PRESSURE = [
    ('atm atmosphere_standard', 101325.0),
    ('atmosphere_technical at', 9.80665e4),
    ('bar', 1e5),
    ('barye_cgs_unit', 0.1),
    ('centimetre_of_mercury cmHg', 1.33322e3),
    ('centimetre_of_water_4degC cmH2O', 98.0638),
    ('foot_of_mercury_conventional ftHg', 40.63666e3),
    ('foot_of_water_39_2_F ftH2O', 2.98898e3),
    ('inch_of_mercury_conventional inHg', 3.386389e3),
    ('inch_of_water_39_2_F inH2O', 249.082),
    ('kilogram_force_per_square_millimetre', 9.80665e6),
    ('kip_per_square_inch ksi', 6.894757e6),
    ('micron_micrometre_of_mercury mHg', 0.1333224),
    ('mmHg millimetre_of_mercury', 133.3224),
    ('millimetre_of_water_3_98_C mmH2O', 9.80638),
    ('pz pieze_mts_unit', 1e3),
    ('psf pound_per_square_foot', 47.88026),
    ('psi pound_per_square_inch', 6.894757e3),
    ('poundal_per_square_foot', 1.488164),
    ('short_ton_per_square_foot', 95.760518e3),
    ('torr', 133.3224),
]

_VELOCITY = [
    ('fph foot_per_hour', 8.466667e-5),
    ('fpm foot_per_minute', 5.08e-3),
    ('fps foot_per_second', 3.048e-1),
    ('furlong_per_fortnight', 1.663095e-4),
    ('inch_per_hour iph', 7.05556e-6),
    ('inch_per_minute ipm', 4.23333e-4),
    ('inch_per_second ips', 2.54e-2),
    ('kph kilometre_per_hour', 2.777778e-1),
    ('kt kn knot', 0.514444),
    ('knot_Admiralty', 0.514773),
    ('M mach_number', 340.0),
    ('mph mile_per_hour', 0.44704),
    ('mile_per_minute mpm', 26.8224),
    ('mile_per_second mps', 1609.344),
    ('c speed_of_light_in_vacuum', 299792458.0),
    ('speed_of_sound_in_air', 340.0),
]
