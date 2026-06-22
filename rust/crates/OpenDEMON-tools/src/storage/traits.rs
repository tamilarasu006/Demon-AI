//! MemoryBackend trait for all storage backends.

use DEMON_core::{DEMONError, RetrievalResult};
use serde_json::Value;

pub trait MemoryBackend: Send + Sync {
    fn backend_id(&self) -> &str;
    fn store(
        &self,
        content: &str,
        source: &str,
        metadata: Option<&Value>,
    ) -> Result<String, DEMONError>;
    fn retrieve(
        &self,
        query: &str,
        top_k: usize,
    ) -> Result<Vec<RetrievalResult>, DEMONError>;
    fn delete(&self, doc_id: &str) -> Result<bool, DEMONError>;
    fn clear(&self) -> Result<(), DEMONError>;
    fn count(&self) -> Result<usize, DEMONError>;
}
