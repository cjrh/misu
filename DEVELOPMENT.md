# Developing misu

## Build & test

Common dev operations are wrapped in a [`justfile`](./justfile). Run
`just` to see what's available:

```bash
just            # list recipes
just test       # build (release) + run pytest
just test-dev   # build (debug) + run pytest — faster rebuilds
just build      # debug build only
just coverage   # Rust coverage from the Python test suite (see below)
```

The raw commands behind `just test` are:

```bash
# from a venv with maturin + pytest + numpy installed
maturin develop --release
pytest python/misu/tests
```

`maturin develop --release` compiles the Rust crate (`rust/src/`) into the
`misu._engine` extension and installs the package as editable. Subsequent
edits to pure-Python files (`python/misu/*.py`) take effect without
rebuilding; edits to Rust require re-running `maturin develop`.

## Layout

```
Cargo.toml          # Rust crate manifest
pyproject.toml      # Python package metadata, maturin backend
justfile            # Common dev tasks (also used by CI)
rust/src/           # Rust source (compiled to misu._engine)
python/misu/        # Pure-Python facade and unit catalogue
python/misu/tests/  # pytest test suite
```

`pyproject.toml` sets `tool.maturin.python-source = "python"`. That is
why pure-Python files live under `python/misu/` rather than at the
repository root.

## Code coverage

`just coverage` produces Rust code-coverage from the Python test suite,
using `cargo-llvm-cov`. It writes:

- `target/llvm-cov/html/index.html` — browsable HTML report
- `target/llvm-cov/coverage.lcov` — LCOV file (suitable for Codecov /
  Coveralls upload from CI)
- a `--summary-only` line printed to stdout

One-time setup on a fresh machine:

```bash
just coverage-setup
# == rustup component add llvm-tools-preview
#    cargo install cargo-llvm-cov
```

### How it works

`cargo llvm-cov show-env --sh` prints `RUSTFLAGS`,
`LLVM_PROFILE_FILE`, and a coverage-specific `CARGO_TARGET_DIR` for the
current shell. The `coverage` recipe sources those into a single bash
process, runs `maturin develop --profile dev` (which then builds the
cdylib with `-C instrument-coverage`), runs pytest (which loads the
instrumented extension and writes `.profraw` files on interpreter
exit), and finally calls `cargo llvm-cov report` to merge them into
the chosen output formats.

### Gotchas

- **Debug build only.** `[profile.release]` in `Cargo.toml` uses
  `lto = "fat"` and `strip = "symbols"`. Fat LTO drops functions
  referenced only by the coverage map; strip removes the
  `__llvm_covmap` section needed for reporting. The recipe omits
  `--release` for that reason — don't add it back.
- **`#[pymodule]` init isn't coverable** (rust-lang/rust#84605 — proc-
  macro-generated init can't be instrumented). The body of `_engine`
  in `rust/src/lib.rs` is wrapped with `// LCOV_EXCL_START` /
  `// LCOV_EXCL_STOP` markers. **Important**: those markers are
  honoured by LCOV-format consumers (Coveralls, Codecov, `genhtml`)
  that re-read the source file when processing the LCOV upload, but
  **NOT by `cargo llvm-cov`'s own** `--summary-only` /
  `--show-missing-lines` output, which uses LLVM's coverage data
  directly. Expect Coveralls' reported number to be a few percentage
  points higher than `just coverage`'s local summary; the local
  number is a slight underestimate, not an error.
- **`extension-module` stays on.** The "remove `extension-module`
  for tests" advice you may see online applies to running `cargo
  test` against a pyo3 crate — irrelevant here, since the tests are
  driven from Python.

## Free-threaded Python (3.13t / 3.14t)

`misu` ships wheels for the free-threaded (no-GIL) CPython builds in
addition to the GIL-enabled ones, but the two are built differently:

- **GIL builds** (3.9–3.14): a single `abi3` wheel per (OS, arch) covers
  all supported interpreters, thanks to
  `pyo3 = { features = ["abi3-py39", ...] }` in `Cargo.toml`.
- **Free-threaded builds** (3.13t, 3.14t): the free-threaded ABI does
  *not* support `Py_LIMITED_API`, so `abi3-pyXX` is silently ignored on
  these interpreters. Free-threaded wheels are version-specific and are
  produced by separate jobs in the release workflow.

Local build against a free-threaded interpreter:

```bash
maturin develop --release --interpreter python3.14t
```

Thread-safety posture:

- PyO3 0.28+ defaults to `gil_used = false` at the module level, so
  `misu._engine` already declares itself free-thread-aware.
- `Quantity` is `#[pyclass(frozen)]` — immutable after construction —
  so scalar arithmetic is safe without explicit GIL release. See the
  module-doc comment on `rust/src/quantity.rs`.
- `QuantityNP` releases the GIL around its ndarray loops via
  `py.detach()`. See the module-doc comment on `rust/src/quantity_np.rs`.

CI / release status:

- `ci.yml` includes `3.14t` in its matrix (alongside `3.9`–`3.14`).
- `release.yml` builds `linux-freethreaded`, `macos-freethreaded`, and
  `windows-freethreaded` wheels for `3.14t` as separate jobs (each per
  OS, since `manylinux` and `maturin` args differ per platform).

When a future free-threaded CPython lands (e.g. `3.15t`), add a matrix
entry to `ci.yml` and three new `*-freethreaded` jobs to `release.yml`,
following the existing pattern.

## Pitfall: a stray `misu/` at the repository root

If a `misu/` directory exists at the repository root (left over from
the original Cython layout), it shadows the maturin-installed
`python/misu/` because the working directory is on `sys.path` ahead of
the editable install. Symptom: `ModuleNotFoundError: No module named
'misu.engine'` after a successful build.

Fix: delete the stray top-level `misu/` directory. The current Rust
package's source of truth is `python/misu/`.
