from pathlib import Path

path = Path("crates/ecosystem-runtime/src/lib.rs")
text = path.read_text()

replacements = {
    '''            Some(current) if expected == Some(current.version) => {
                record.version = current.version + 1
            }
            Some(_) => return Err(Error::Conflict(record.key)),
            None if expected.is_none() => record.version = 1,
            None => return Err(Error::Conflict(record.key)),''': '''            Some(current) if expected == Some(current.version) => {
                record.version = current.version + 1;
            }
            None if expected.is_none() => {
                record.version = 1;
            }
            Some(_) | None => return Err(Error::Conflict(record.key)),''',
    '''impl SqliteStore {
    pub async fn in_memory() -> Result<Self, Error> {''': '''impl SqliteStore {
    /// Creates an isolated in-memory SQLite adapter and applies its schema.
    ///
    /// # Errors
    /// Returns [`Error::Storage`] when the database cannot be opened or initialized.
    pub async fn in_memory() -> Result<Self, Error> {''',
    '''pub async fn differential_store_check() -> Result<(), Error> {''': '''/// Executes the same optimistic-concurrency fixture against memory and SQLite stores.
///
/// # Errors
/// Returns [`Error::Storage`] when either adapter fails or their observable behavior diverges.
pub async fn differential_store_check() -> Result<(), Error> {''',
    '''impl GovernorRuntime {
    pub async fn execute<F, Fut>(''': '''impl GovernorRuntime {
    /// Executes one authority-bounded, idempotent governor operation.
    ///
    /// # Errors
    /// Returns [`Error::Refused`] for missing idempotency, denied authority, or ambiguous timeout,
    /// and propagates the operation's typed failure.
    pub async fn execute<F, Fut>(''',
    '''#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolContract {
    pub name: String,
    pub read_only: bool,
    pub destructive: bool,
    pub idempotent: bool,
    pub required_authority: Authority,
    pub receipt_required: bool,
    pub timeout_ms: u64,
}''': '''#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ToolNature {
    ReadOnly,
    MutatingNonDestructive,
    MutatingDestructive,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum IdempotencyPolicy {
    Idempotent,
    NonIdempotent,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ReceiptPolicy {
    Optional,
    Required,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolContract {
    pub name: String,
    pub nature: ToolNature,
    pub idempotency: IdempotencyPolicy,
    pub required_authority: Authority,
    pub receipt: ReceiptPolicy,
    pub timeout_ms: u64,
}''',
    '''impl McpBoundary {
    pub fn tools() -> Vec<ToolContract> {''': '''impl McpBoundary {
    /// Returns the complete admitted MCP tool contract surface.
    #[must_use]
    pub fn tools() -> Vec<ToolContract> {''',
    '''                read_only: true,
                destructive: false,
                idempotent: true,
                required_authority: Authority::Observe,
                receipt_required: false,''': '''                nature: ToolNature::ReadOnly,
                idempotency: IdempotencyPolicy::Idempotent,
                required_authority: Authority::Observe,
                receipt: ReceiptPolicy::Optional,''',
    '''                read_only: false,
                destructive: true,
                idempotent: true,
                required_authority: Authority::ModifyExternalObject,
                receipt_required: true,''': '''                nature: ToolNature::MutatingDestructive,
                idempotency: IdempotencyPolicy::Idempotent,
                required_authority: Authority::ModifyExternalObject,
                receipt: ReceiptPolicy::Required,''',
    '''    pub fn handle(request: &str, granted: Authority) -> Result<String, Error> {''': '''    /// Handles one bounded JSON-RPC request through the admitted MCP surface.
    ///
    /// # Errors
    /// Returns [`Error::Mcp`] when the request is malformed or cannot be serialized.
    pub fn handle(request: &str, granted: Authority) -> Result<String, Error> {''',
    '''                    return Ok(rpc_error(id, -32001, "authority denied"));''': '''                    return Ok(rpc_error(&id, -32001, "authority denied"));''',
    '''                if tool.destructive {
                    return Ok(rpc_error(id, -32002, "mutation must pass through broker"));
                }''': '''                if matches!(tool.nature, ToolNature::MutatingDestructive) {
                    return Ok(rpc_error(
                        &id,
                        -32002,
                        "mutation must pass through broker",
                    ));
                }''',
    '''            _ => return Ok(rpc_error(id, -32601, "method not found")),''': '''            _ => return Ok(rpc_error(&id, -32601, "method not found")),''',
    '''fn rpc_error(id: Value, code: i64, message: &str) -> String {''': '''fn rpc_error(id: &Value, code: i64, message: &str) -> String {''',
    '''impl GitHubObservation {
    pub fn normalize(input: &str) -> Result<Self, Error> {''': '''impl GitHubObservation {
    /// Normalizes a GitHub repository observation into a canonical exact-head record.
    ///
    /// # Errors
    /// Returns [`Error::Connector`] when required fields or the 40-hex head SHA are invalid.
    pub fn normalize(input: &str) -> Result<Self, Error> {''',
    '''impl DocumentObservation {
    pub fn normalize(input: &str) -> Result<Self, Error> {''': '''impl DocumentObservation {
    /// Normalizes a document identity, revision, relative path, and BLAKE3 digest.
    ///
    /// # Errors
    /// Returns [`Error::Connector`] when fields are missing or the path/digest is noncanonical.
    pub fn normalize(input: &str) -> Result<Self, Error> {''',
    '''pub fn standing_for_job(state: JobState) -> Standing {''': '''/// Maps an operational governor state to constitutional standing.
#[must_use]
pub fn standing_for_job(state: JobState) -> Standing {''',
}

for old, new in replacements.items():
    if old not in text:
        raise SystemExit(f"missing expected runtime fragment:\n{old}")
    text = text.replace(old, new, 1)

path.write_text(text)
