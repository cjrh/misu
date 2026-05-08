# Common dev operations for misu.
# Run `just` (or `just --list`) to see available recipes.
# Recipes are designed to work the same locally and in CI.

# Show available recipes.
default:
    @just --list

# Build the Rust extension into the active venv (debug profile).
build:
    maturin develop

# Build the Rust extension into the active venv (release profile).
build-release:
    maturin develop --release

# Run the Python test suite against a release build.
test: build-release
    pytest python/misu/tests

# Run the Python test suite against a debug build (faster rebuild loop).
test-dev: build
    pytest python/misu/tests

# One-time setup for `just coverage`.
coverage-setup:
    rustup component add llvm-tools-preview
    cargo install cargo-llvm-cov

# Rust code coverage from the Python test suite (HTML + LCOV).
coverage:
    #!/usr/bin/env bash
    # Coverage forces the dev profile: the release profile has
    # lto="fat" + strip="symbols", which break LLVM coverage maps.
    # `--profile dev` overrides tool.maturin.profile in pyproject.toml.
    set -euo pipefail
    source <(cargo llvm-cov show-env --sh)
    export CARGO_TARGET_DIR="$CARGO_LLVM_COV_TARGET_DIR"
    export CARGO_INCREMENTAL=1
    cargo llvm-cov clean --workspace
    maturin develop --profile dev
    pytest python/misu/tests
    cargo llvm-cov report --html
    cargo llvm-cov report --lcov --output-path target/llvm-cov/coverage.lcov
    cargo llvm-cov report --summary-only

# Remove build artifacts and coverage output.
clean:
    cargo clean
