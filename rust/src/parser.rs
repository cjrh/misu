//! Tiny parser for `quantity_from_string`.
//!
//! Accepts strings like:
//!   `1 m`, `1.0 m`, `-1.158e+05 m/s kg^6.0`, `1 m^2 s^-1`, `1 m^2     s^-1`.
//!
//! All multiplications are done with raw `f64` + `Dim` ops in Rust — far
//! faster than the Cython implementation, which round-tripped through
//! Python's `eval()` on a regex-rewritten string.

use pyo3::prelude::*;

use crate::dim::Dim;
use crate::quantity::Quantity;
use crate::registry::UNIT_REGISTRY;

pub fn parse<'py>(py: Python<'py>, input: &str) -> PyResult<Bound<'py, PyAny>> {
    let s = input.trim();
    let mut iter = s.chars().peekable();

    // 1. Optional leading sign + numeric magnitude.
    let mut buf = String::new();
    if matches!(iter.peek(), Some('+') | Some('-')) {
        buf.push(iter.next().unwrap());
    }
    while let Some(&c) = iter.peek() {
        if c.is_ascii_digit() || c == '.' || c == 'e' || c == 'E' {
            buf.push(c);
            iter.next();
        } else if (c == '+' || c == '-') && matches!(buf.chars().last(), Some('e') | Some('E')) {
            buf.push(c);
            iter.next();
        } else {
            break;
        }
    }
    let mut magnitude: f64 = buf.parse().map_err(|_| {
        pyo3::exceptions::PyValueError::new_err(format!(
            "Cannot parse number from {:?}",
            input
        ))
    })?;
    let mut dim = Dim::DIMENSIONLESS;

    skip_ws(&mut iter);
    while let Some(&c) = iter.peek() {
        let op_char = if c == '/' || c == '*' {
            let ch = iter.next().unwrap();
            skip_ws(&mut iter);
            ch
        } else {
            '*' // implicit multiplication between adjacent symbols
        };
        let (sym, exp) = read_term(&mut iter)?;
        let q = {
            let reg = UNIT_REGISTRY.read();
            reg.get(&sym)
                .map(|q| q.bind(py).borrow().clone())
                .ok_or_else(|| {
                    pyo3::exceptions::PyValueError::new_err(format!("Unknown unit: {}", sym))
                })?
        };
        let (q_mag, q_dim) = if let Some(e) = exp {
            (q.magnitude.powf(e), q.dim.scale(e))
        } else {
            (q.magnitude, q.dim)
        };
        if op_char == '/' {
            magnitude /= q_mag;
            dim = dim.sub(&q_dim);
        } else {
            magnitude *= q_mag;
            dim = dim.add(&q_dim);
        }
        skip_ws(&mut iter);
    }
    Ok(Quantity::new(magnitude, dim).into_pyobject(py)?.into_any())
}

fn skip_ws(iter: &mut std::iter::Peekable<std::str::Chars<'_>>) {
    while let Some(&c) = iter.peek() {
        if c.is_whitespace() {
            iter.next();
        } else {
            break;
        }
    }
}

fn read_term(
    iter: &mut std::iter::Peekable<std::str::Chars<'_>>,
) -> PyResult<(String, Option<f64>)> {
    let mut sym = String::new();
    while let Some(&c) = iter.peek() {
        if c.is_ascii_alphabetic() || c == '_' || (sym.len() > 0 && c.is_ascii_digit()) {
            sym.push(c);
            iter.next();
        } else {
            break;
        }
    }
    if sym.is_empty() {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Expected unit symbol",
        ));
    }
    let exp = if iter.peek() == Some(&'^') {
        iter.next();
        let mut buf = String::new();
        if matches!(iter.peek(), Some('+') | Some('-')) {
            buf.push(iter.next().unwrap());
        }
        while let Some(&c) = iter.peek() {
            if c.is_ascii_digit() || c == '.' {
                buf.push(c);
                iter.next();
            } else {
                break;
            }
        }
        Some(buf.parse::<f64>().map_err(|_| {
            pyo3::exceptions::PyValueError::new_err(format!("Bad exponent: {:?}", buf))
        })?)
    } else {
        None
    };
    Ok((sym, exp))
}
