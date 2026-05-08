//! String/repr/format helpers shared by Quantity and QuantityNP.
//!
//! Mirrors the original Cython algorithms in `engine.pyx::_unitString`,
//! `_getRepresentTuple`, `__str__`, `__format__` so existing test
//! expectations match exactly.

use pyo3::prelude::*;
use pyo3::types::{PyFloat, PyInt};

use crate::dim::Dim;
use crate::registry::REPRESENT_CACHE;

pub const SYMBOLS: [&str; 7] = ["m", "kg", "s", "A", "K", "ca", "mole"];

/// Build the "m^1 s^-2" style fallback when no preferred symbol exists.
pub fn dim_string(dim: &Dim) -> String {
    let mut parts: Vec<String> = Vec::new();
    for (i, &v) in dim.0.iter().enumerate() {
        if v != 0.0 {
            parts.push(format!("{}^{}", SYMBOLS[i], format_exponent(v)));
        }
    }
    parts.join(" ")
}

fn format_exponent(v: f64) -> String {
    // Matches Cython str() of a float, e.g. 1.0 -> "1.0", 2 -> "2.0".
    // The original code used Python's `'{}'.format(v)`, which prints integral
    // floats as e.g. "1.0".
    if v == v.trunc() && v.abs() < 1e16 {
        format!("{:.1}", v)
    } else {
        format!("{}", v)
    }
}

/// Result tuple of `_getRepresentTuple` in the original engine.
pub struct RepresentTuple<'py> {
    pub magnitude: Bound<'py, PyAny>,
    pub symbol: String,
    pub format_spec: String,
}

/// Compute (mag, symbol, format_spec) for a Quantity-like object.
///
/// `magnitude_obj` is the raw magnitude as a Python object (a float for
/// Quantity, an ndarray for QuantityNP). When a `convert_fn` is registered
/// it is called with `(magnitude_obj,)` exactly as the Cython version did
/// (passing self as the first arg, magnitude as the second). For our
/// internal-only callers we use a simpler convention: `convert_fn(self)` —
/// matching the misulib helper which is `lambda inst, _: inst.convert(unit)`.
pub fn represent_tuple<'py>(
    py: Python<'py>,
    quantity_obj: &Bound<'py, PyAny>,
    dim: &Dim,
    raw_mag: Bound<'py, PyAny>,
) -> PyResult<RepresentTuple<'py>> {
    // Snapshot just the small fields out of the lock so we can call back
    // into Python without holding it. The convert_fn (if any) is
    // clone_ref'd while the lock is held.
    enum Plan {
        None,
        Direct,
        Divide(f64),
        Convert(pyo3::Py<pyo3::PyAny>),
    }
    let (plan, symbol, mut format_spec) = {
        let cache = REPRESENT_CACHE.read();
        match cache.get(dim) {
            Some(entry) => {
                let plan = if let Some(div) = entry.divisor {
                    Plan::Divide(div)
                } else if let Some(cf) = entry.convert_fn.as_ref() {
                    Plan::Convert(cf.clone_ref(py))
                } else {
                    Plan::Direct
                };
                (plan, entry.symbol.clone(), entry.format_spec.clone())
            }
            None => (Plan::None, dim_string(dim), String::new()),
        }
    };

    let mag = match plan {
        Plan::None => raw_mag,
        Plan::Direct => raw_mag,
        Plan::Divide(div) => {
            if let Ok(f) = raw_mag.extract::<f64>() {
                pyo3::types::PyFloat::new(py, f / div).into_any()
            } else {
                raw_mag.call_method1("__truediv__", (div,))?
            }
        }
        Plan::Convert(cf) => cf.bind(py).call1((quantity_obj.clone(), raw_mag.clone()))?,
    };
    if !mag.is_instance_of::<PyFloat>() && !mag.is_instance_of::<PyInt>() {
        format_spec.clear();
    }
    Ok(RepresentTuple {
        magnitude: mag,
        symbol,
        format_spec,
    })
}

/// Apply a Python format-spec string to a number using `format(num, spec)`.
pub fn py_format<'py>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    spec: &str,
) -> PyResult<String> {
    let builtins = py.import("builtins")?;
    let formatted = builtins.getattr("format")?.call1((value.clone(), spec))?;
    formatted.extract::<String>()
}

/// `__str__` / `__repr__` — render with the stored format_spec.
pub fn render<'py>(
    py: Python<'py>,
    quantity_obj: &Bound<'py, PyAny>,
    dim: &Dim,
    raw_mag: Bound<'py, PyAny>,
) -> PyResult<String> {
    let r = represent_tuple(py, quantity_obj, dim, raw_mag)?;
    let number = py_format(py, &r.magnitude, &r.format_spec)?;
    if r.symbol.is_empty() {
        Ok(number)
    } else {
        Ok(format!("{} {}", number, r.symbol))
    }
}

/// `__format__(spec)` — caller-supplied spec wins over stored.
///
/// We split the spec into its "alignment+fill+width" prefix and a
/// "number-formatting" suffix. The numeric part is applied to the
/// magnitude alone; the alignment+width is then applied to the
/// rendered "<number> <symbol>" string, so e.g. `'{:<20.2f}'.format(b)`
/// gives `'124812.00 kg/hr     '` (whole-string left-aligned).
pub fn format_with_spec<'py>(
    py: Python<'py>,
    quantity_obj: &Bound<'py, PyAny>,
    dim: &Dim,
    raw_mag: Bound<'py, PyAny>,
    user_spec: &str,
) -> PyResult<String> {
    let r = represent_tuple(py, quantity_obj, dim, raw_mag)?;
    let spec = if user_spec.is_empty() {
        r.format_spec.as_str()
    } else {
        user_spec
    };
    let (align_spec, num_spec) = split_alignment_spec(spec);
    let number = py_format(py, &r.magnitude, &num_spec)?;
    let combined = if r.symbol.is_empty() {
        number
    } else {
        format!("{} {}", number, r.symbol)
    };
    if align_spec.is_empty() {
        Ok(combined)
    } else {
        // Apply the alignment-and-width spec to the combined string by
        // delegating to Python's `format(str, spec)`.
        let combined_obj = combined.as_str().into_pyobject(py)?.into_any();
        py_format(py, &combined_obj, &align_spec)
    }
}

/// Split a format spec like `<20.2f` into (`<20`, `.2f`).
///
/// Format mini-language grammar: `[[fill]align][sign][#][0][width][,][.precision][type]`.
/// We pull off the leading `[fill]align` (optional) and the run of `width`
/// digits before any `,` `.precision` or `type` character.
fn split_alignment_spec(spec: &str) -> (String, String) {
    let chars: Vec<char> = spec.chars().collect();
    let mut i = 0;

    // Optional [fill]align — align is one of '<' '>' '=' '^'. Fill is any
    // single char that's not align/digit/sign.
    let mut align_end = 0;
    if chars.len() >= 2 && matches!(chars[1], '<' | '>' | '=' | '^') {
        align_end = 2;
        i = 2;
    } else if !chars.is_empty() && matches!(chars[0], '<' | '>' | '=' | '^') {
        align_end = 1;
        i = 1;
    }

    // Skip optional sign / # / 0 (these stay with the number-format part)
    let num_start = i;

    // Digits that follow are width (belongs to alignment_spec).
    // BUT if those digits are followed directly by '.' (precision) or
    // a type letter, they're width — same place either way. Keep things
    // simple: width digits move into the alignment spec only when an
    // alignment char preceded them, otherwise they're ambient width
    // which Python applies to the whole result anyway.
    let mut width_end = num_start;
    while width_end < chars.len() && chars[width_end].is_ascii_digit() {
        width_end += 1;
    }
    if align_end > 0 {
        // We have an explicit alignment — capture width into align_spec.
        let align_spec: String = chars[..width_end].iter().collect();
        let num_spec: String = chars[width_end..].iter().collect();
        return (align_spec, num_spec);
    }
    // No alignment char. Leave the spec entirely as the number-format.
    (String::new(), spec.to_string())
}
