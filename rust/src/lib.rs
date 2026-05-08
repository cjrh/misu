// Python-API-faithful names (`addType`, `setRepresent`, `setValDict`,
// `_unitString`, `unitCategory`) match the existing user-facing API; do
// not rename them.
#![allow(non_snake_case)]
//! misu Rust core (`misu._engine`).
//!
//! Exposes:
//! - `Quantity`, `QuantityNP` pyclasses
//! - `EIncompatibleUnits`, `ESignatureAlreadyRegistered` exceptions
//! - `addType(quantity, name)` — register a Dim → category-name mapping
//! - `dimensions(**kwargs)` decorator
//! - `quantity_from_string(s)` parser
//! - module-level `RepresentCache` (mirror of the Cython global; provided
//!   only so any user code that touched it still finds a dict-like there).

mod dim;
mod errors;
mod format;
mod parser;
mod quantity;
mod quantity_np;
mod registry;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyTuple};

use crate::errors::{EIncompatibleUnits, ESignatureAlreadyRegistered};
use crate::quantity::Quantity;
use crate::quantity_np::{_restore_quantity_np, QuantityNP};
use crate::registry::QUANTITY_TYPE;

/// `addType(quantity, name)` — registers a Dim → category-name mapping.
#[pyfunction]
fn addType(q: &Quantity, name: String) -> PyResult<()> {
    let mut map = QUANTITY_TYPE.write();
    if let Some(existing) = map.get(&q.dim) {
        return Err(pyo3::exceptions::PyException::new_err(format!(
            "This unit def already registered, owned by: {}",
            existing
        )));
    }
    map.insert(q.dim, name);
    Ok(())
}

/// `dimensions(**spec)` decorator. Verifies that each named argument has the
/// declared `unitCategory()`. Mirrors `misulib.dimensions`.
///
/// Returns a Python callable; we implement this as a closure-producing
/// pyfunction that returns a small wrapper class.
#[pyfunction]
#[pyo3(signature = (**kwargs))]
fn dimensions<'py>(
    py: Python<'py>,
    kwargs: Option<Bound<'py, PyDict>>,
) -> PyResult<Bound<'py, PyAny>> {
    // We generate a Python decorator on the fly. Doing the dimension check
    // in Python keeps full compatibility with arbitrary user-supplied
    // callables (kwargs, defaults, generators, etc.) — the perf-critical
    // path is the inner Quantity arithmetic, which is already in Rust.
    let kwargs = kwargs.unwrap_or_else(|| PyDict::new(py));
    let helpers = py.import("misu._decorator")?;
    let factory = helpers.getattr("make_dimensions_decorator")?;
    factory.call1((kwargs,))
}

/// `quantity_from_string` — parse a string like `"1.0 m^2 s^-1"` into a
/// Quantity by looking up symbols in the unit registry.
#[pyfunction]
fn quantity_from_string<'py>(
    py: Python<'py>,
    s: &str,
) -> PyResult<Bound<'py, PyAny>> {
    parser::parse(py, s)
}

#[pymodule]
fn _engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Quantity>()?;
    m.add_class::<QuantityNP>()?;
    m.add(
        "EIncompatibleUnits",
        m.py().get_type::<EIncompatibleUnits>(),
    )?;
    m.add(
        "ESignatureAlreadyRegistered",
        m.py().get_type::<ESignatureAlreadyRegistered>(),
    )?;
    m.add_function(wrap_pyfunction!(addType, m)?)?;
    m.add_function(wrap_pyfunction!(dimensions, m)?)?;
    m.add_function(wrap_pyfunction!(quantity_from_string, m)?)?;
    m.add_function(wrap_pyfunction!(_restore_quantity_np, m)?)?;
    // Public-but-internal hooks used by the Python catalogue setup.
    m.add_function(wrap_pyfunction!(_unit_registry_set, m)?)?;
    m.add_function(wrap_pyfunction!(_unit_registry_get, m)?)?;
    m.add_function(wrap_pyfunction!(_unit_registry_keys, m)?)?;
    Ok(())
}

// ---- catalog support ----------------------------------------------------

#[pyfunction]
fn _unit_registry_set(py: Python<'_>, name: String, q: &Quantity) {
    let mut reg = registry::UNIT_REGISTRY.write();
    reg.insert(name, Py::new(py, q.clone()).unwrap());
}

#[pyfunction]
fn _unit_registry_get<'py>(
    py: Python<'py>,
    name: String,
) -> Option<Py<Quantity>> {
    let reg = registry::UNIT_REGISTRY.read();
    reg.get(&name).map(|q| q.clone_ref(py))
}

#[pyfunction]
fn _unit_registry_keys<'py>(py: Python<'py>) -> PyResult<Bound<'py, PyTuple>> {
    let reg = registry::UNIT_REGISTRY.read();
    let names: Vec<&str> = reg.keys().map(|s| s.as_str()).collect();
    PyTuple::new(py, names)
}
