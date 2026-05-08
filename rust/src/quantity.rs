//! Scalar-magnitude Quantity (replaces the Cython `Quantity` class).

use pyo3::class::basic::CompareOp;
use pyo3::exceptions::PyAssertionError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyTuple};

use crate::dim::Dim;
use crate::errors::EIncompatibleUnits;
use crate::format::{self, SYMBOLS};
use crate::quantity_np::QuantityNP;
use crate::registry::{QUANTITY_TYPE, REPRESENT_CACHE, RepresentEntry};

#[pyclass(module = "misu._engine", frozen, from_py_object)]
#[derive(Clone)]
pub struct Quantity {
    pub magnitude: f64,
    pub dim: Dim,
}

impl Quantity {
    #[inline(always)]
    pub fn new(magnitude: f64, dim: Dim) -> Self {
        Quantity { magnitude, dim }
    }

    /// Coerce a Bound PyAny to a Quantity (cloning if it already is one,
    /// wrapping a Python float/int as a dimensionless Quantity otherwise).
    pub fn coerce(obj: &Bound<'_, PyAny>) -> PyResult<Quantity> {
        if let Ok(q) = obj.extract::<Quantity>() {
            Ok(q)
        } else {
            let mag = obj.extract::<f64>()?;
            Ok(Quantity::new(mag, Dim::DIMENSIONLESS))
        }
    }

    pub fn assert_same_units(&self, other: &Quantity) -> PyResult<()> {
        if self.dim != other.dim {
            Err(EIncompatibleUnits::new_err(format!(
                "Incompatible units: {} and {}",
                short_repr(self),
                short_repr(other)
            )))
        } else {
            Ok(())
        }
    }
}

fn short_repr(q: &Quantity) -> String {
    // Used inside an error message before we have access to py — we render
    // without consulting REPRESENT_CACHE here for simplicity. This matches
    // the original test expectation `"Incompatible units: 2 m and 3 kg"`.
    let mag = render_magnitude(q.magnitude);
    let cache = REPRESENT_CACHE.read();
    if let Some(entry) = cache.get(&q.dim) {
        if entry.symbol.is_empty() {
            mag
        } else {
            format!("{} {}", mag, entry.symbol)
        }
    } else {
        let unit_str = crate::format::dim_string(&q.dim);
        if unit_str.is_empty() {
            mag
        } else {
            format!("{} {}", mag, unit_str)
        }
    }
}

fn render_magnitude(m: f64) -> String {
    if m == m.trunc() && m.abs() < 1e16 {
        format!("{}", m as i64)
    } else {
        format!("{}", m)
    }
}

#[pymethods]
impl Quantity {
    #[new]
    #[pyo3(signature = (magnitude, unit=None))]
    fn py_new(magnitude: f64, unit: Option<Vec<f64>>) -> PyResult<Self> {
        let dim = match unit {
            None => Dim::DIMENSIONLESS,
            Some(v) => {
                if v.len() != 7 {
                    return Err(pyo3::exceptions::PyValueError::new_err(
                        "unit list must have length 7",
                    ));
                }
                let mut arr = [0.0; 7];
                arr.copy_from_slice(&v);
                Dim(arr)
            }
        };
        Ok(Quantity::new(magnitude, dim))
    }

    /// Numpy hook — gives Quantity priority during e.g. `np.array * kg`.
    #[classattr]
    fn __array_priority__() -> f64 {
        20.0
    }

    #[getter]
    fn magnitude(&self) -> f64 {
        self.magnitude
    }

    fn unit_as_tuple<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyTuple>> {
        PyTuple::new(py, self.dim.0.iter().copied())
    }

    fn as_tuple<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyTuple>> {
        let unit = self.unit_as_tuple(py)?;
        PyTuple::new(
            py,
            [
                self.magnitude.into_pyobject(py)?.into_any(),
                unit.into_any(),
            ],
        )
    }

    fn units(&self) -> Vec<f64> {
        self.dim.0.to_vec()
    }

    fn getunit(&self) -> Vec<f64> {
        self.dim.0.to_vec()
    }

    fn setunit(&self, _unit: Vec<f64>) -> PyResult<()> {
        // Quantity is frozen; mutating after construction is not supported.
        Err(PyAssertionError::new_err("Quantity is immutable"))
    }

    fn setValDict(&self, _valdict: Bound<'_, PyDict>) -> PyResult<()> {
        Err(PyAssertionError::new_err(
            "Quantity is frozen; build via arithmetic on base units",
        ))
    }

    /// Pickling. Returns a 2-tuple `(constructor, (magnitude, unit_list))`.
    fn __reduce__<'py>(
        &self,
        py: Python<'py>,
    ) -> PyResult<Bound<'py, PyTuple>> {
        let module = py.import("misu._engine")?;
        let ctor = module.getattr("Quantity")?;
        let unit_list = PyTuple::new(py, self.dim.0.iter().copied())?;
        let args = PyTuple::new(
            py,
            [
                self.magnitude.into_pyobject(py)?.into_any(),
                unit_list.into_any(),
            ],
        )?;
        PyTuple::new(py, [ctor.into_any(), args.into_any()])
    }

    fn __str__<'py>(slf: &Bound<'py, Self>, py: Python<'py>) -> PyResult<String> {
        let q = slf.borrow();
        let mag = q.magnitude.into_pyobject(py)?.into_any();
        format::render(py, &slf.clone().into_any(), &q.dim, mag)
    }

    fn __repr__<'py>(slf: &Bound<'py, Self>, py: Python<'py>) -> PyResult<String> {
        Self::__str__(slf, py)
    }

    fn __format__<'py>(
        slf: &Bound<'py, Self>,
        py: Python<'py>,
        format_spec: &str,
    ) -> PyResult<String> {
        let q = slf.borrow();
        let mag = q.magnitude.into_pyobject(py)?.into_any();
        format::format_with_spec(py, &slf.clone().into_any(), &q.dim, mag, format_spec)
    }

    fn _unitString(&self) -> String {
        let cache = REPRESENT_CACHE.read();
        if let Some(entry) = cache.get(&self.dim) {
            entry.symbol.clone()
        } else {
            crate::format::dim_string(&self.dim)
        }
    }

    fn convert(&self, target_unit: &Bound<'_, PyAny>) -> PyResult<f64> {
        let target = target_unit
            .extract::<Quantity>()
            .map_err(|_| PyAssertionError::new_err("Target must be a quantity."))?;
        self.assert_same_units(&target)?;
        Ok(self.magnitude / target.magnitude)
    }

    fn unitCategory(&self) -> PyResult<String> {
        let map = QUANTITY_TYPE.read();
        match map.get(&self.dim) {
            Some(name) => Ok(name.clone()),
            None => Err(pyo3::exceptions::PyException::new_err(format!(
                "The collection of units: \"{}\" has not been defined as a category yet.",
                describe_for_error(self)
            ))),
        }
    }

    #[pyo3(signature = (as_unit=None, symbol=String::new(), convert_function=None, format_spec=String::from(".4g")))]
    fn setRepresent(
        &self,
        as_unit: Option<Bound<'_, PyAny>>,
        symbol: String,
        convert_function: Option<Py<PyAny>>,
        format_spec: String,
    ) -> PyResult<()> {
        if as_unit.is_none() && convert_function.is_none() {
            return Err(pyo3::exceptions::PyException::new_err(
                "Either a target unit or a conversion function must be supplied.",
            ));
        }
        let entry = if let Some(cf) = convert_function {
            RepresentEntry {
                divisor: None,
                convert_fn: Some(cf),
                symbol,
                format_spec,
            }
        } else {
            let unit_q = as_unit.unwrap().extract::<Quantity>()?;
            self.assert_same_units(&unit_q)?;
            RepresentEntry {
                divisor: Some(unit_q.magnitude),
                convert_fn: None,
                symbol,
                format_spec,
            }
        };
        REPRESENT_CACHE.write().insert(self.dim, entry);
        Ok(())
    }

    // ---- arithmetic ------------------------------------------------------

    fn __add__<'py>(
        slf: &Bound<'py, Self>,
        py: Python<'py>,
        other: Bound<'py, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        if is_arraylike(&other) {
            let lhs = QuantityNP::from_quantity(py, &slf.borrow())?;
            let rhs = QuantityNP::coerce(py, &other)?;
            return Ok(lhs.add(py, &rhs)?.into_pyobject(py)?.into_any().unbind());
        }
        let a = slf.borrow();
        let b = Quantity::coerce(&other)?;
        a.assert_same_units(&b)?;
        Ok(Quantity::new(a.magnitude + b.magnitude, a.dim)
            .into_pyobject(py)?
            .into_any()
            .unbind())
    }

    fn __radd__<'py>(
        slf: &Bound<'py, Self>,
        py: Python<'py>,
        other: Bound<'py, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        Self::__add__(slf, py, other)
    }

    fn __sub__<'py>(
        slf: &Bound<'py, Self>,
        py: Python<'py>,
        other: Bound<'py, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        if is_arraylike(&other) {
            let lhs = QuantityNP::from_quantity(py, &slf.borrow())?;
            let rhs = QuantityNP::coerce(py, &other)?;
            return Ok(lhs.sub(py, &rhs)?.into_pyobject(py)?.into_any().unbind());
        }
        let a = slf.borrow();
        let b = Quantity::coerce(&other)?;
        a.assert_same_units(&b)?;
        Ok(Quantity::new(a.magnitude - b.magnitude, a.dim)
            .into_pyobject(py)?
            .into_any()
            .unbind())
    }

    fn __rsub__<'py>(
        slf: &Bound<'py, Self>,
        py: Python<'py>,
        other: Bound<'py, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        if is_arraylike(&other) {
            let lhs = QuantityNP::coerce(py, &other)?;
            let rhs = QuantityNP::from_quantity(py, &slf.borrow())?;
            return Ok(lhs.sub(py, &rhs)?.into_pyobject(py)?.into_any().unbind());
        }
        let a = slf.borrow();
        let b = Quantity::coerce(&other)?;
        a.assert_same_units(&b)?;
        Ok(Quantity::new(b.magnitude - a.magnitude, a.dim)
            .into_pyobject(py)?
            .into_any()
            .unbind())
    }

    fn __mul__<'py>(
        slf: &Bound<'py, Self>,
        py: Python<'py>,
        other: Bound<'py, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        if is_arraylike(&other) {
            let lhs = QuantityNP::from_quantity(py, &slf.borrow())?;
            let rhs = QuantityNP::coerce(py, &other)?;
            return Ok(lhs.mul(py, &rhs)?.into_pyobject(py)?.into_any().unbind());
        }
        let a = slf.borrow();
        let b = Quantity::coerce(&other)?;
        Ok(Quantity::new(a.magnitude * b.magnitude, a.dim.add(&b.dim))
            .into_pyobject(py)?
            .into_any()
            .unbind())
    }

    fn __rmul__<'py>(
        slf: &Bound<'py, Self>,
        py: Python<'py>,
        other: Bound<'py, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        Self::__mul__(slf, py, other)
    }

    fn __truediv__<'py>(
        slf: &Bound<'py, Self>,
        py: Python<'py>,
        other: Bound<'py, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        if is_arraylike(&other) {
            let lhs = QuantityNP::from_quantity(py, &slf.borrow())?;
            let rhs = QuantityNP::coerce(py, &other)?;
            return Ok(lhs
                .truediv(py, &rhs)?
                .into_pyobject(py)?
                .into_any()
                .unbind());
        }
        let a = slf.borrow();
        let b = Quantity::coerce(&other)?;
        Ok(Quantity::new(a.magnitude / b.magnitude, a.dim.sub(&b.dim))
            .into_pyobject(py)?
            .into_any()
            .unbind())
    }

    fn __rtruediv__<'py>(
        slf: &Bound<'py, Self>,
        py: Python<'py>,
        other: Bound<'py, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        if is_arraylike(&other) {
            let lhs = QuantityNP::coerce(py, &other)?;
            let rhs = QuantityNP::from_quantity(py, &slf.borrow())?;
            return Ok(lhs
                .truediv(py, &rhs)?
                .into_pyobject(py)?
                .into_any()
                .unbind());
        }
        let a = slf.borrow();
        let b = Quantity::coerce(&other)?;
        Ok(Quantity::new(b.magnitude / a.magnitude, b.dim.sub(&a.dim))
            .into_pyobject(py)?
            .into_any()
            .unbind())
    }

    fn __pow__<'py>(
        slf: &Bound<'py, Self>,
        py: Python<'py>,
        other: Bound<'py, PyAny>,
        modulo: Option<Bound<'py, PyAny>>,
    ) -> PyResult<Py<PyAny>> {
        let _ = modulo;
        if other.extract::<Quantity>().is_ok() {
            return Err(PyAssertionError::new_err(
                "The exponent must not be a quantity!",
            ));
        }
        let exp = other.extract::<f64>()?;
        let a = slf.borrow();
        Ok(Quantity::new(a.magnitude.powf(exp), a.dim.scale(exp))
            .into_pyobject(py)?
            .into_any()
            .unbind())
    }

    fn __neg__<'py>(slf: &Bound<'py, Self>, py: Python<'py>) -> PyResult<Py<PyAny>> {
        let a = slf.borrow();
        Ok(Quantity::new(-a.magnitude, a.dim)
            .into_pyobject(py)?
            .into_any()
            .unbind())
    }

    fn __pos__<'py>(slf: &Bound<'py, Self>, py: Python<'py>) -> PyResult<Py<PyAny>> {
        let a = slf.borrow();
        Ok(Quantity::new(a.magnitude, a.dim)
            .into_pyobject(py)?
            .into_any()
            .unbind())
    }

    fn __abs__<'py>(slf: &Bound<'py, Self>, py: Python<'py>) -> PyResult<Py<PyAny>> {
        let a = slf.borrow();
        Ok(Quantity::new(a.magnitude.abs(), a.dim)
            .into_pyobject(py)?
            .into_any()
            .unbind())
    }

    fn __richcmp__(&self, other: &Bound<'_, PyAny>, op: CompareOp) -> PyResult<bool> {
        let b = Quantity::coerce(other)?;
        self.assert_same_units(&b)?;
        Ok(match op {
            CompareOp::Lt => self.magnitude < b.magnitude,
            CompareOp::Le => self.magnitude <= b.magnitude,
            CompareOp::Eq => self.magnitude == b.magnitude,
            CompareOp::Ne => self.magnitude != b.magnitude,
            CompareOp::Gt => self.magnitude > b.magnitude,
            CompareOp::Ge => self.magnitude >= b.magnitude,
        })
    }

    fn __float__(&self) -> PyResult<f64> {
        if !self.dim.is_dimensionless() {
            return Err(PyAssertionError::new_err(
                "Must be dimensionless for __float__()",
            ));
        }
        Ok(self.magnitude)
    }

    fn __rshift__(&self, other: &Bound<'_, PyAny>) -> PyResult<f64> {
        self.convert(other)
    }

    fn __hash__(&self) -> u64 {
        let mut h: u64 = self.magnitude.to_bits();
        for v in self.dim.0.iter() {
            h = h.rotate_left(7) ^ v.to_bits();
        }
        h
    }

    // --- numpy-style elementwise math (dimensionless only) --------------
    fn sin(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::sin) }
    fn cos(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::cos) }
    fn tan(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::tan) }
    fn arcsin(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::asin) }
    fn arccos(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::acos) }
    fn arctan(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::atan) }
    fn degrees(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::to_degrees) }
    fn radians(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::to_radians) }
    fn deg2rad(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::to_radians) }
    fn rad2deg(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::to_degrees) }
    fn sinh(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::sinh) }
    fn cosh(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::cosh) }
    fn tanh(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::tanh) }
    fn arcsinh(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::asinh) }
    fn arccosh(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::acosh) }
    fn arctanh(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::atanh) }
    fn exp(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::exp) }
    fn expm1(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::exp_m1) }
    fn exp2(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::exp2) }
    fn log(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::ln) }
    fn log10(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::log10) }
    fn log2(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::log2) }
    fn log1p(&self) -> PyResult<Quantity> { self.dimensionless_call(f64::ln_1p) }
}

impl Quantity {
    fn dimensionless_call(&self, f: fn(f64) -> f64) -> PyResult<Quantity> {
        if !self.dim.is_dimensionless() {
            return Err(EIncompatibleUnits::new_err(
                "Argument must be dimensionless.",
            ));
        }
        Ok(Quantity::new(f(self.magnitude), Dim::DIMENSIONLESS))
    }
}

fn describe_for_error(q: &Quantity) -> String {
    let mag = render_magnitude(q.magnitude);
    let mut parts = vec![mag];
    let extra = SYMBOLS
        .iter()
        .zip(q.dim.0.iter())
        .filter(|(_, &v)| v != 0.0)
        .map(|(s, &v)| format!("{}^{}", s, v))
        .collect::<Vec<_>>()
        .join(" ");
    if !extra.is_empty() {
        parts.push(extra);
    }
    parts.join(" ")
}

/// True if `obj` is a numpy ndarray or a misu QuantityNP — used to route
/// arithmetic through the array-aware path.
///
/// Optimised for the common case: both arms of misu arithmetic are
/// scalar Quantity-or-number 99% of the time. Hot path is therefore a
/// single `is_instance_of::<QuantityNP>` check (PyO3 lookup, no Python
/// attribute access). Only when that fails do we pay the cost of two
/// `hasattr` calls to detect a foreign ndarray.
#[inline]
fn is_arraylike(obj: &Bound<'_, PyAny>) -> bool {
    if obj.is_instance_of::<QuantityNP>() {
        return true;
    }
    // numpy ndarrays are PyArray instances; downcast is much cheaper than
    // `hasattr` (which performs full attribute resolution).
    if obj.cast::<numpy::PyUntypedArray>().is_ok() {
        return true;
    }
    false
}
