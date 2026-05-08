"""Benchmark misu vs plain Python floats for heavy-math, looping code.

Two physically-meaningful workloads are timed in each form:

1. fall_with_drag — Euler integration of 1-D free-fall with quadratic drag.
   Tight inner loop dominated by arithmetic on a single scalar.

2. orbit_step — 2-D Kepler step with sqrt and mixed dimensions
   (length, velocity, acceleration). Slightly more varied operations.

The "plain" form uses Python floats. The "misu" form uses Quantity objects
throughout the inner loop so the unit-tracking overhead is fully exercised.
The two forms compute the same numerical result; the misu form just carries
units along.

Usage:
    python scripts/benchmark.py
"""
from __future__ import annotations

import math
import statistics
import sys
import time

import misu
from misu import kg, m, s


# ---------- workload 1: free-fall with quadratic drag ------------------------

def fall_with_drag_float(v0, mass, c, dt, steps, g):
    v = v0
    x = 0.0
    for _ in range(steps):
        # F = m*g - c*v*|v|  (drag opposes motion)
        F = mass * g - c * v * abs(v)
        a = F / mass
        v = v + a * dt
        x = x + v * dt
    return x


def fall_with_drag_misu(v0, mass, c, dt, steps, g):
    v = v0
    x = 0.0 * m
    for _ in range(steps):
        F = mass * g - c * v * abs(v)
        a = F / mass
        v = v + a * dt
        x = x + v * dt
    return x


# ---------- workload 2: 2-D gravitational orbit step (Euler) -----------------

def orbit_float(rx, ry, vx, vy, mu, dt, steps):
    for _ in range(steps):
        r2 = rx * rx + ry * ry
        r = math.sqrt(r2)
        a = -mu / (r2 * r)        # = -mu / r^3
        ax = a * rx
        ay = a * ry
        vx = vx + ax * dt
        vy = vy + ay * dt
        rx = rx + vx * dt
        ry = ry + vy * dt
    return rx, ry, vx, vy


def orbit_misu(rx, ry, vx, vy, mu, dt, steps):
    for _ in range(steps):
        r2 = rx * rx + ry * ry
        r = r2 ** 0.5
        a = -mu / (r2 * r)
        ax = a * rx
        ay = a * ry
        vx = vx + ax * dt
        vy = vy + ay * dt
        rx = rx + vx * dt
        ry = ry + vy * dt
    return rx, ry, vx, vy


# ---------- timing helpers ---------------------------------------------------

def timeit(fn, *args, repeats=5):
    """Run fn(*args) `repeats` times and return (best, median, last_result)."""
    samples = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        result = fn(*args)
        samples.append(time.perf_counter() - t0)
    return min(samples), statistics.median(samples), result


def report(name, t_float, t_misu, r_float, r_misu):
    ratio = t_misu / t_float
    print(f"\n== {name} ==")
    print(f"  plain float : {t_float*1e3:9.3f} ms   result = {r_float}")
    print(f"  misu        : {t_misu*1e3:9.3f} ms   result = {r_misu}")
    print(f"  slowdown    : {ratio:6.2f}x")
    return ratio


def main():
    print(f"Python {sys.version.split()[0]} | misu {misu.__version__}")

    # ---- fall_with_drag --------------------------------------------------
    STEPS_FALL = 200_000
    f_min, _, f_res = timeit(
        fall_with_drag_float,
        50.0, 1.0, 0.01, 1e-3, STEPS_FALL, 9.81,
    )
    # misu version — same numerical inputs, dressed in units.
    # c has units kg/m so c*v^2 is a force (N), keeping F dimensionally clean.
    m_min, _, m_res = timeit(
        fall_with_drag_misu,
        50.0 * m / s,
        1.0 * kg,
        0.01 * kg / m,
        1e-3 * s,
        STEPS_FALL,
        9.81 * m / s**2,
    )
    r1 = report(f"fall_with_drag ({STEPS_FALL:,} steps)",
                f_min, m_min, f_res, m_res)

    # ---- orbit -----------------------------------------------------------
    STEPS_ORBIT = 100_000
    f_min, _, f_res = timeit(
        orbit_float,
        1.0, 0.0, 0.0, 1.0, 1.0, 1e-3, STEPS_ORBIT,
    )
    # Concrete units so dimensions check out: [mu]=m^3/s^2, [r]=m, [v]=m/s.
    m_min, _, m_res = timeit(
        orbit_misu,
        1.0 * m, 0.0 * m,
        0.0 * m / s, 1.0 * m / s,
        1.0 * m**3 / s**2,
        1e-3 * s,
        STEPS_ORBIT,
    )
    r2 = report(f"orbit_step     ({STEPS_ORBIT:,} steps)",
                f_min, m_min, f_res, m_res)

    print("\n----------------------------------------")
    print(f"geo. mean slowdown across workloads : {(r1*r2)**0.5:.2f}x")


if __name__ == "__main__":
    main()
