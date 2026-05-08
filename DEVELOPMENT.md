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

`cargo llvm-cov show-env --export-prefix` prints `RUSTFLAGS`,
`LLVM_PROFILE_FILE`, and a coverage-specific `CARGO_TARGET_DIR` for the
current shell. The `coverage` recipe sources those into a single bash
process, runs `maturin develop` (which then builds the cdylib with
`-C instrument-coverage`), runs pytest (which loads the instrumented
extension and writes `.profraw` files on interpreter exit), and
finally calls `cargo llvm-cov report` to merge them into the chosen
output formats.

### Gotchas

- **Debug build only.** `[profile.release]` in `Cargo.toml` uses
  `lto = "fat"` and `strip = "symbols"`. Fat LTO drops functions
  referenced only by the coverage map; strip removes the
  `__llvm_covmap` section needed for reporting. The recipe omits
  `--release` for that reason — don't add it back.
- **`#[pymodule]` init isn't covered.** A long-standing rustc issue
  (rust-lang/rust#84605) means proc-macro-generated init code can't
  be instrumented. If the missing lines bother you, wrap the body of
  `_engine` in `rust/src/lib.rs` with `// LCOV_EXCL_START` /
  `// LCOV_EXCL_STOP` markers; LCOV-aware tools (Codecov, genhtml)
  honour them.
- **`extension-module` stays on.** The "remove `extension-module`
  for tests" advice you may see online applies to running `cargo
  test` against a pyo3 crate — irrelevant here, since the tests are
  driven from Python.

## Pitfall: a stray `misu/` at the repository root

If a `misu/` directory exists at the repository root (left over from
the original Cython layout), it shadows the maturin-installed
`python/misu/` because the working directory is on `sys.path` ahead of
the editable install. Symptom: `ModuleNotFoundError: No module named
'misu.engine'` after a successful build.

Fix: delete the stray top-level `misu/` directory. The current Rust
package's source of truth is `python/misu/`.
