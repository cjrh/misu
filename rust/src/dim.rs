//! The 7-element SI dimension exponent vector and operations on it.
//!
//! All quantities in misu carry one of these. Equality, addition, subtraction,
//! and scalar multiplication are length-7 loops that LLVM will autovectorize
//! at `opt-level=3`.

use std::hash::{Hash, Hasher};

/// The seven base-SI dimensions (m, kg, s, A, K, ca, mole) — kept as f64
/// so non-integer exponents (e.g. `m^-0.5`) work, matching the original
/// Cython behaviour.
#[derive(Clone, Copy, Debug, Default)]
#[repr(C)]
pub struct Dim(pub [f64; 7]);

impl Dim {
    pub const DIMENSIONLESS: Dim = Dim([0.0; 7]);

    #[inline(always)]
    pub fn is_dimensionless(&self) -> bool {
        self.0.iter().all(|x| *x == 0.0)
    }

    #[inline(always)]
    pub fn add(&self, other: &Dim) -> Dim {
        let mut out = [0.0; 7];
        for i in 0..7 {
            out[i] = self.0[i] + other.0[i];
        }
        Dim(out)
    }

    #[inline(always)]
    pub fn sub(&self, other: &Dim) -> Dim {
        let mut out = [0.0; 7];
        for i in 0..7 {
            out[i] = self.0[i] - other.0[i];
        }
        Dim(out)
    }

    #[inline(always)]
    pub fn scale(&self, k: f64) -> Dim {
        let mut out = [0.0; 7];
        for i in 0..7 {
            out[i] = self.0[i] * k;
        }
        Dim(out)
    }
}

impl PartialEq for Dim {
    #[inline(always)]
    fn eq(&self, other: &Self) -> bool {
        // Bitwise comparison — exponents are produced by arithmetic on
        // identical f64 inputs, so for matching dims they are bit-identical.
        // (This avoids NaN-related gotchas of `==` on f64 too.)
        self.0
            .iter()
            .zip(other.0.iter())
            .all(|(a, b)| a.to_bits() == b.to_bits())
    }
}

impl Eq for Dim {}

impl Hash for Dim {
    #[inline]
    fn hash<H: Hasher>(&self, state: &mut H) {
        for v in self.0.iter() {
            state.write_u64(v.to_bits());
        }
    }
}
