//! Custom Python exception types.

use pyo3::create_exception;
use pyo3::exceptions::PyException;

create_exception!(_engine, EIncompatibleUnits, PyException);
create_exception!(_engine, ESignatureAlreadyRegistered, PyException);
