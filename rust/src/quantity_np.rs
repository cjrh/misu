//! Numpy-backed Quantity (replaces the Cython `QuantityNP` class).
//!
//! Holds a 1-D `f64` ndarray plus a Dim. Arithmetic releases the GIL for
//! the actual numerical loop (free-thread-friendly, parallel-safe).

use numpy::ndarray::{Array1, Zip};
use numpy::{IntoPyArray, PyArray1, PyArrayMethods, PyReadonlyArray1};
use pyo3::class::basic::CompareOp;
use pyo3::exceptions::{PyAssertionError, PyTypeError};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PySlice, PyTuple};

use crate::dim::Dim;
use crate::errors::EIncompatibleUnits;
use crate::format;
use crate::quantity::Quantity;
use crate::registry::{QUANTITY_TYPE, REPRESENT_CACHE, RepresentEntry};

#[pyclass(module = "misu._engine")]
pub struct QuantityNP {
    pub magnitude: Py<PyArray1<f64>>,
    pub dim: Dim,
}

impl QuantityNP {
    pub fn new(magnitude: Py<PyArray1<f64>>, dim: Dim) -> Self {
        QuantityNP { magnitude, dim }
    }

    /// Build a QuantityNP from an iterable / scalar / Quantity / ndarray.
    pub fn coerce<'py>(py: Python<'py>, obj: &Bound<'py, PyAny>) -> PyResult<Self> {
        if let Ok(qnp) = obj.extract::<PyRef<QuantityNP>>() {
            return Ok(QuantityNP {
                magnitude: qnp.magnitude.clone_ref(py),
                dim: qnp.dim,
            });
        }
        if let Ok(q) = obj.extract::<Quantity>() {
            // Wrap a scalar Quantity into a 0-d array? Tests use scalar
            // results out of Quantity-on-Quantity ops; for QuantityNP arms
            // (which arise only when one operand is array-like), we lift
            // the scalar to a length-1 array.
            let arr = Array1::from_elem(1, q.magnitude);
            return Ok(QuantityNP::new(arr.into_pyarray(py).unbind(), q.dim));
        }
        // numpy ndarray path
        if let Ok(arr) = obj.downcast::<PyArray1<f64>>() {
            return Ok(QuantityNP::new(arr.clone().unbind(), Dim::DIMENSIONLESS));
        }
        // Generic ndarray of any dtype: convert to f64 via numpy.
        let np = py.import("numpy")?;
        let asarray = np.getattr("asarray")?;
        let conv = asarray.call1((obj.clone(), np.getattr("float64")?))?;
        let arr = conv.downcast_into::<PyArray1<f64>>().map_err(|_| {
            PyTypeError::new_err("Could not coerce to a 1-D float64 numpy array")
        })?;
        Ok(QuantityNP::new(arr.unbind(), Dim::DIMENSIONLESS))
    }

    pub fn from_quantity<'py>(py: Python<'py>, q: &Quantity) -> PyResult<Self> {
        let arr = Array1::from_elem(1, q.magnitude);
        Ok(QuantityNP::new(arr.into_pyarray(py).unbind(), q.dim))
    }

    pub fn assert_same_units(&self, other: &QuantityNP) -> PyResult<()> {
        if self.dim != other.dim {
            Err(EIncompatibleUnits::new_err(
                "Incompatible units for ndarray quantities",
            ))
        } else {
            Ok(())
        }
    }

    fn binary<'py>(
        &self,
        py: Python<'py>,
        rhs: &QuantityNP,
        op: impl Fn(f64, f64) -> f64 + Send + Sync,
    ) -> PyResult<QuantityNP> {
        let lhs_view: PyReadonlyArray1<f64> = self.magnitude.bind(py).readonly();
        let rhs_view: PyReadonlyArray1<f64> = rhs.magnitude.bind(py).readonly();
        let lhs_arr = lhs_view.as_array();
        let rhs_arr = rhs_view.as_array();

        // Broadcast a length-1 operand against an N-length operand.
        let result: Array1<f64> = py.detach(|| {
            let (l, r) = (lhs_arr.len(), rhs_arr.len());
            if l == r {
                let mut out = Array1::<f64>::zeros(l);
                Zip::from(&mut out)
                    .and(&lhs_arr)
                    .and(&rhs_arr)
                    .for_each(|o, &a, &b| *o = op(a, b));
                out
            } else if l == 1 {
                let scalar = lhs_arr[0];
                rhs_arr.mapv(|b| op(scalar, b))
            } else if r == 1 {
                let scalar = rhs_arr[0];
                lhs_arr.mapv(|a| op(a, scalar))
            } else {
                // Length mismatch: fall through with NaN; numpy proper would
                // broadcast multi-D — extend later if a test needs it.
                Array1::from_elem(l.max(r), f64::NAN)
            }
        });

        Ok(QuantityNP::new(
            result.into_pyarray(py).unbind(),
            self.dim,
        ))
    }

    pub fn add(&self, py: Python<'_>, other: &QuantityNP) -> PyResult<QuantityNP> {
        self.assert_same_units(other)?;
        self.binary(py, other, |a, b| a + b)
    }

    pub fn sub(&self, py: Python<'_>, other: &QuantityNP) -> PyResult<QuantityNP> {
        self.assert_same_units(other)?;
        self.binary(py, other, |a, b| a - b)
    }

    pub fn mul(&self, py: Python<'_>, other: &QuantityNP) -> PyResult<QuantityNP> {
        let mut out = self.binary(py, other, |a, b| a * b)?;
        out.dim = self.dim.add(&other.dim);
        Ok(out)
    }

    pub fn truediv(&self, py: Python<'_>, other: &QuantityNP) -> PyResult<QuantityNP> {
        let mut out = self.binary(py, other, |a, b| a / b)?;
        out.dim = self.dim.sub(&other.dim);
        Ok(out)
    }
}

#[pymethods]
impl QuantityNP {
    #[new]
    fn py_new(py: Python<'_>, magnitude: Bound<'_, PyAny>) -> PyResult<Self> {
        Self::coerce(py, &magnitude)
    }

    #[classattr]
    fn __array_priority__() -> f64 {
        20.0
    }

    #[getter]
    fn magnitude<'py>(&self, py: Python<'py>) -> Bound<'py, PyArray1<f64>> {
        self.magnitude.bind(py).clone()
    }

    fn unit_as_tuple<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyTuple>> {
        PyTuple::new(py, self.dim.0.iter().copied())
    }

    fn units(&self) -> Vec<f64> {
        self.dim.0.to_vec()
    }

    fn getunit(&self) -> Vec<f64> {
        self.dim.0.to_vec()
    }

    fn setValDict(&self, _valdict: Bound<'_, PyDict>) -> PyResult<()> {
        Err(PyAssertionError::new_err(
            "QuantityNP is constructed via arithmetic on base units",
        ))
    }

    fn copy(&self, py: Python<'_>) -> QuantityNP {
        let arr = self.magnitude.bind(py).readonly().as_array().to_owned();
        QuantityNP::new(arr.into_pyarray(py).unbind(), self.dim)
    }

    fn __reduce__<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyTuple>> {
        let module = py.import("misu._engine")?;
        let restore = module.getattr("_restore_quantity_np")?;
        let unit_list = PyTuple::new(py, self.dim.0.iter().copied())?;
        let mag = self.magnitude.bind(py).clone();
        let args = PyTuple::new(py, [mag.into_any(), unit_list.into_any()])?;
        PyTuple::new(py, [restore.into_any(), args.into_any()])
    }

    fn __str__<'py>(slf: &Bound<'py, Self>, py: Python<'py>) -> PyResult<String> {
        let q = slf.borrow();
        let mag = q.magnitude.bind(py).clone().into_any();
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
        let mag = q.magnitude.bind(py).clone().into_any();
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

    fn convert(&self, py: Python<'_>, target_unit: &Bound<'_, PyAny>) -> PyResult<Py<PyArray1<f64>>> {
        let target = target_unit
            .extract::<Quantity>()
            .map_err(|_| PyAssertionError::new_err("Target must be a quantity."))?;
        if self.dim != target.dim {
            return Err(EIncompatibleUnits::new_err("Incompatible units"));
        }
        let view = self.magnitude.bind(py).readonly();
        let arr = view.as_array();
        let div = target.magnitude;
        let result: Array1<f64> = py.detach(|| arr.mapv(|x| x / div));
        Ok(result.into_pyarray(py).unbind())
    }

    fn unitCategory(&self) -> PyResult<String> {
        let map = QUANTITY_TYPE.read();
        match map.get(&self.dim) {
            Some(name) => Ok(name.clone()),
            None => Err(pyo3::exceptions::PyException::new_err(
                "The collection of units has not been defined as a category yet.",
            )),
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
            if unit_q.dim != self.dim {
                return Err(EIncompatibleUnits::new_err(
                    "setRepresent target dim mismatch",
                ));
            }
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

    fn __getitem__<'py>(
        slf: &Bound<'py, Self>,
        py: Python<'py>,
        index: Bound<'py, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        let q = slf.borrow();
        // Integer index: return Quantity (scalar).
        if let Ok(i) = index.extract::<isize>() {
            let arr = q.magnitude.bind(py).readonly();
            let view = arr.as_array();
            let len = view.len() as isize;
            let idx = if i < 0 { i + len } else { i };
            if idx < 0 || idx >= len {
                return Err(pyo3::exceptions::PyIndexError::new_err("index out of range"));
            }
            return Ok(Quantity::new(view[idx as usize], q.dim)
                .into_pyobject(py)?
                .into_any()
                .unbind());
        }
        // Otherwise let numpy handle the indexing then wrap.
        let bound = q.magnitude.bind(py);
        let py_any: &Bound<'py, PyAny> = bound.as_any();
        let result = py_any.get_item(index)?;
        // If result is a scalar (0-d / float), wrap as Quantity; else QuantityNP.
        if let Ok(arr) = result.downcast::<PyArray1<f64>>() {
            return Ok(QuantityNP::new(arr.clone().unbind(), q.dim)
                .into_pyobject(py)?
                .into_any()
                .unbind());
        }
        if let Ok(scalar) = result.extract::<f64>() {
            return Ok(Quantity::new(scalar, q.dim)
                .into_pyobject(py)?
                .into_any()
                .unbind());
        }
        // Slice fallthrough
        let _ = PySlice::new(py, 0, 0, 1);
        Err(PyTypeError::new_err("Unsupported index type"))
    }

    fn __len__(&self, py: Python<'_>) -> usize {
        self.magnitude.bind(py).readonly().as_array().len()
    }

    // ---- arithmetic ------------------------------------------------------

    fn __add__<'py>(
        slf: &Bound<'py, Self>,
        py: Python<'py>,
        other: Bound<'py, PyAny>,
    ) -> PyResult<QuantityNP> {
        let rhs = QuantityNP::coerce(py, &other)?;
        slf.borrow().add(py, &rhs)
    }

    fn __radd__<'py>(
        slf: &Bound<'py, Self>,
        py: Python<'py>,
        other: Bound<'py, PyAny>,
    ) -> PyResult<QuantityNP> {
        let lhs = QuantityNP::coerce(py, &other)?;
        lhs.add(py, &slf.borrow())
    }

    fn __sub__<'py>(
        slf: &Bound<'py, Self>,
        py: Python<'py>,
        other: Bound<'py, PyAny>,
    ) -> PyResult<QuantityNP> {
        let rhs = QuantityNP::coerce(py, &other)?;
        slf.borrow().sub(py, &rhs)
    }

    fn __rsub__<'py>(
        slf: &Bound<'py, Self>,
        py: Python<'py>,
        other: Bound<'py, PyAny>,
    ) -> PyResult<QuantityNP> {
        let lhs = QuantityNP::coerce(py, &other)?;
        lhs.sub(py, &slf.borrow())
    }

    fn __mul__<'py>(
        slf: &Bound<'py, Self>,
        py: Python<'py>,
        other: Bound<'py, PyAny>,
    ) -> PyResult<QuantityNP> {
        let rhs = QuantityNP::coerce(py, &other)?;
        slf.borrow().mul(py, &rhs)
    }

    fn __rmul__<'py>(
        slf: &Bound<'py, Self>,
        py: Python<'py>,
        other: Bound<'py, PyAny>,
    ) -> PyResult<QuantityNP> {
        let lhs = QuantityNP::coerce(py, &other)?;
        lhs.mul(py, &slf.borrow())
    }

    fn __truediv__<'py>(
        slf: &Bound<'py, Self>,
        py: Python<'py>,
        other: Bound<'py, PyAny>,
    ) -> PyResult<QuantityNP> {
        let rhs = QuantityNP::coerce(py, &other)?;
        slf.borrow().truediv(py, &rhs)
    }

    fn __rtruediv__<'py>(
        slf: &Bound<'py, Self>,
        py: Python<'py>,
        other: Bound<'py, PyAny>,
    ) -> PyResult<QuantityNP> {
        let lhs = QuantityNP::coerce(py, &other)?;
        lhs.truediv(py, &slf.borrow())
    }

    fn __pow__<'py>(
        slf: &Bound<'py, Self>,
        py: Python<'py>,
        other: Bound<'py, PyAny>,
        modulo: Option<Bound<'py, PyAny>>,
    ) -> PyResult<QuantityNP> {
        let _ = modulo;
        let exp = other.extract::<f64>()?;
        let q = slf.borrow();
        let view = q.magnitude.bind(py).readonly();
        let arr = view.as_array();
        let result: Array1<f64> = py.detach(|| arr.mapv(|x| x.powf(exp)));
        Ok(QuantityNP::new(
            result.into_pyarray(py).unbind(),
            q.dim.scale(exp),
        ))
    }

    fn __neg__(&self, py: Python<'_>) -> PyResult<QuantityNP> {
        let view = self.magnitude.bind(py).readonly();
        let arr = view.as_array();
        let result: Array1<f64> = py.detach(|| arr.mapv(|x| -x));
        Ok(QuantityNP::new(result.into_pyarray(py).unbind(), self.dim))
    }

    fn __richcmp__(
        slf: &Bound<'_, Self>,
        py: Python<'_>,
        other: Bound<'_, PyAny>,
        op: CompareOp,
    ) -> PyResult<Py<PyAny>> {
        let q = slf.borrow();
        let rhs = QuantityNP::coerce(py, &other)?;
        if matches!(op, CompareOp::Eq | CompareOp::Ne) {
            // Allow eq/ne even on different units (returns False/True).
            if q.dim != rhs.dim {
                let v = matches!(op, CompareOp::Ne);
                let pb = pyo3::types::PyBool::new(py, v);
                return Ok(pb.to_owned().into_any().unbind());
            }
        } else if q.dim != rhs.dim {
            return Err(EIncompatibleUnits::new_err("Incompatible units"));
        }
        let l_view = q.magnitude.bind(py).readonly();
        let r_view = rhs.magnitude.bind(py).readonly();
        let l = l_view.as_array();
        let r = r_view.as_array();
        let cmp: Vec<bool> = py.detach(|| {
            let len = l.len().max(r.len());
            (0..len)
                .map(|i| {
                    let a = if l.len() == 1 { l[0] } else { l[i] };
                    let b = if r.len() == 1 { r[0] } else { r[i] };
                    match op {
                        CompareOp::Lt => a < b,
                        CompareOp::Le => a <= b,
                        CompareOp::Eq => a == b,
                        CompareOp::Ne => a != b,
                        CompareOp::Gt => a > b,
                        CompareOp::Ge => a >= b,
                    }
                })
                .collect()
        });
        Ok(cmp.into_pyobject(py)?.into_any().unbind())
    }

    fn __rshift__(&self, py: Python<'_>, other: &Bound<'_, PyAny>) -> PyResult<Py<PyArray1<f64>>> {
        self.convert(py, other)
    }

    // numpy-style elementwise math (dimensionless only)
    fn sin(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::sin) }
    fn cos(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::cos) }
    fn tan(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::tan) }
    fn arcsin(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::asin) }
    fn arccos(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::acos) }
    fn arctan(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::atan) }
    fn degrees(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::to_degrees) }
    fn radians(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::to_radians) }
    fn deg2rad(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::to_radians) }
    fn rad2deg(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::to_degrees) }
    fn sinh(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::sinh) }
    fn cosh(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::cosh) }
    fn tanh(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::tanh) }
    fn arcsinh(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::asinh) }
    fn arccosh(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::acosh) }
    fn arctanh(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::atanh) }
    fn exp(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::exp) }
    fn expm1(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::exp_m1) }
    fn exp2(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::exp2) }
    fn log(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::ln) }
    fn log10(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::log10) }
    fn log2(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::log2) }
    fn log1p(&self, py: Python<'_>) -> PyResult<QuantityNP> { self.dimcall(py, f64::ln_1p) }
}

impl QuantityNP {
    fn dimcall(&self, py: Python<'_>, f: fn(f64) -> f64) -> PyResult<QuantityNP> {
        if !self.dim.is_dimensionless() {
            return Err(EIncompatibleUnits::new_err(
                "Argument must be dimensionless.",
            ));
        }
        let view = self.magnitude.bind(py).readonly();
        let arr = view.as_array();
        let result: Array1<f64> = py.detach(|| arr.mapv(f));
        Ok(QuantityNP::new(
            result.into_pyarray(py).unbind(),
            Dim::DIMENSIONLESS,
        ))
    }
}

#[pyfunction]
pub fn _restore_quantity_np(
    py: Python<'_>,
    magnitude: Bound<'_, PyAny>,
    unit: Vec<f64>,
) -> PyResult<QuantityNP> {
    if unit.len() != 7 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "unit list must have length 7",
        ));
    }
    let mut arr = [0.0; 7];
    arr.copy_from_slice(&unit);
    let mut q = QuantityNP::coerce(py, &magnitude)?;
    q.dim = Dim(arr);
    Ok(q)
}
