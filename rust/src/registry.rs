//! Process-wide registries shared by all Quantities.
//!
//! - `QUANTITY_TYPE`: maps a `Dim` to a category name (e.g. "Length", "Mass").
//! - `REPRESENT_CACHE`: maps a `Dim` to its preferred display form.
//! - `UNIT_REGISTRY`: maps a unit symbol string to a `Quantity` reference
//!   (used by `quantity_from_string` and as the public name → unit lookup).
//!
//! `parking_lot::RwLock` keeps reads cheap; writes only happen during
//! catalogue setup at import time and on explicit `setRepresent` calls,
//! so contention is negligible. Free-threaded Python (3.13t/3.14t) safe.

use std::collections::HashMap;

use once_cell::sync::Lazy;
use parking_lot::RwLock;
use pyo3::prelude::*;

use crate::dim::Dim;
use crate::quantity::Quantity;

/// Display configuration: how a particular Dim should be printed.
pub struct RepresentEntry {
    /// Pre-converted: divisor on the magnitude (or NaN if a callable is set).
    pub divisor: Option<f64>,
    /// Optional Python convert_function (overrides `divisor` when set).
    pub convert_fn: Option<Py<PyAny>>,
    pub symbol: String,
    pub format_spec: String,
}

pub static QUANTITY_TYPE: Lazy<RwLock<HashMap<Dim, String>>> =
    Lazy::new(|| RwLock::new(HashMap::new()));

pub static REPRESENT_CACHE: Lazy<RwLock<HashMap<Dim, RepresentEntry>>> =
    Lazy::new(|| RwLock::new(HashMap::new()));

pub static UNIT_REGISTRY: Lazy<RwLock<HashMap<String, Py<Quantity>>>> =
    Lazy::new(|| RwLock::new(HashMap::new()));
