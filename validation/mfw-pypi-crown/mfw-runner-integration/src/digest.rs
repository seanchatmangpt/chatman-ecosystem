use crate::{Error, Result};
use std::{fs, path::Path};

pub fn file_digest(path: &Path) -> Result<String> {
    let bytes = fs::read(path).map_err(|source| Error::Read {
        path: path.to_path_buf(),
        source,
    })?;
    Ok(format!("blake3:{}", blake3::hash(&bytes).to_hex()))
}

pub fn bytes_digest(bytes: &[u8]) -> String {
    format!("blake3:{}", blake3::hash(bytes).to_hex())
}
