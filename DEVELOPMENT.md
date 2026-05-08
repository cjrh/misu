# Developing misu

## Build & test

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
rust/src/           # Rust source (compiled to misu._engine)
python/misu/        # Pure-Python facade and unit catalogue
python/misu/tests/  # pytest test suite
```

`pyproject.toml` sets `tool.maturin.python-source = "python"`. That is
why pure-Python files live under `python/misu/` rather than at the
repository root.

## Pitfall: a stray `misu/` at the repository root

If a `misu/` directory exists at the repository root (left over from
the original Cython layout), it shadows the maturin-installed
`python/misu/` because the working directory is on `sys.path` ahead of
the editable install. Symptom: `ModuleNotFoundError: No module named
'misu.engine'` after a successful build.

Fix: delete the stray top-level `misu/` directory. The current Rust
package's source of truth is `python/misu/`.
