//! Runtime and adapter layer for the Chatman Ecosystem.

use async_trait::async_trait;
use ecosystem_core::{Authority, Standing};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use sqlx::{Row, SqlitePool, sqlite::SqlitePoolOptions};
use std::collections::BTreeMap;
use std::time::Duration;
use tokio::sync::Mutex;

#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("conflict for `{0}`")]
    Conflict(String),
    #[error("storage: {0}")]
    Storage(String),
    #[error("refused: {0}")]
    Refused(String),
    #[error("MCP: {0}")]
    Mcp(String),
    #[error("connector: {0}")]
    Connector(String),
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct StateRecord {
    pub key: String,
    pub value: String,
    pub version: i64,
}

#[async_trait]
pub trait StateStore: Send + Sync {
    async fn put(&self, record: StateRecord, expected: Option<i64>) -> Result<StateRecord, Error>;
    async fn get(&self, key: &str) -> Result<Option<StateRecord>, Error>;
}

#[derive(Debug, Default)]
pub struct MemoryStore {
    records: Mutex<BTreeMap<String, StateRecord>>,
}

#[async_trait]
impl StateStore for MemoryStore {
    async fn put(
        &self,
        mut record: StateRecord,
        expected: Option<i64>,
    ) -> Result<StateRecord, Error> {
        let mut records = self.records.lock().await;
        match records.get(&record.key) {
            Some(current) if expected == Some(current.version) => {
                record.version = current.version + 1
            }
            Some(_) => return Err(Error::Conflict(record.key)),
            None if expected.is_none() => record.version = 1,
            None => return Err(Error::Conflict(record.key)),
        }
        records.insert(record.key.clone(), record.clone());
        Ok(record)
    }

    async fn get(&self, key: &str) -> Result<Option<StateRecord>, Error> {
        Ok(self.records.lock().await.get(key).cloned())
    }
}

#[derive(Debug, Clone)]
pub struct SqliteStore {
    pool: SqlitePool,
}

impl SqliteStore {
    pub async fn in_memory() -> Result<Self, Error> {
        let pool = SqlitePoolOptions::new()
            .max_connections(1)
            .connect("sqlite::memory:")
            .await
            .map_err(|e| Error::Storage(e.to_string()))?;
        let store = Self { pool };
        sqlx::query("CREATE TABLE ecosystem_state(key TEXT PRIMARY KEY, value TEXT NOT NULL, version INTEGER NOT NULL CHECK(version > 0))")
            .execute(&store.pool).await.map_err(|e| Error::Storage(e.to_string()))?;
        Ok(store)
    }
}

#[async_trait]
impl StateStore for SqliteStore {
    async fn put(
        &self,
        mut record: StateRecord,
        expected: Option<i64>,
    ) -> Result<StateRecord, Error> {
        let mut tx = self
            .pool
            .begin()
            .await
            .map_err(|e| Error::Storage(e.to_string()))?;
        let current = sqlx::query("SELECT version FROM ecosystem_state WHERE key = ?")
            .bind(&record.key)
            .fetch_optional(&mut *tx)
            .await
            .map_err(|e| Error::Storage(e.to_string()))?;
        match current {
            Some(row) => {
                let version: i64 = row
                    .try_get("version")
                    .map_err(|e| Error::Storage(e.to_string()))?;
                if expected != Some(version) {
                    return Err(Error::Conflict(record.key));
                }
                record.version = version + 1;
                sqlx::query("UPDATE ecosystem_state SET value = ?, version = ? WHERE key = ? AND version = ?")
                    .bind(&record.value).bind(record.version).bind(&record.key).bind(version)
                    .execute(&mut *tx).await.map_err(|e| Error::Storage(e.to_string()))?;
            }
            None if expected.is_none() => {
                record.version = 1;
                sqlx::query("INSERT INTO ecosystem_state(key, value, version) VALUES (?, ?, ?)")
                    .bind(&record.key)
                    .bind(&record.value)
                    .bind(record.version)
                    .execute(&mut *tx)
                    .await
                    .map_err(|e| Error::Storage(e.to_string()))?;
            }
            None => return Err(Error::Conflict(record.key)),
        }
        tx.commit()
            .await
            .map_err(|e| Error::Storage(e.to_string()))?;
        Ok(record)
    }

    async fn get(&self, key: &str) -> Result<Option<StateRecord>, Error> {
        let row = sqlx::query("SELECT key, value, version FROM ecosystem_state WHERE key = ?")
            .bind(key)
            .fetch_optional(&self.pool)
            .await
            .map_err(|e| Error::Storage(e.to_string()))?;
        row.map(|row| {
            Ok(StateRecord {
                key: row
                    .try_get("key")
                    .map_err(|e| Error::Storage(e.to_string()))?,
                value: row
                    .try_get("value")
                    .map_err(|e| Error::Storage(e.to_string()))?,
                version: row
                    .try_get("version")
                    .map_err(|e| Error::Storage(e.to_string()))?,
            })
        })
        .transpose()
    }
}

pub async fn differential_store_check() -> Result<(), Error> {
    async fn exercise(store: &dyn StateStore) -> Result<Vec<StateRecord>, Error> {
        let first = store
            .put(
                StateRecord {
                    key: "standing:crown".into(),
                    value: "CANDIDATE".into(),
                    version: 0,
                },
                None,
            )
            .await?;
        let second = store
            .put(
                StateRecord {
                    key: "standing:crown".into(),
                    value: "ALIVE".into(),
                    version: 0,
                },
                Some(1),
            )
            .await?;
        if store
            .put(
                StateRecord {
                    key: "standing:crown".into(),
                    value: "STALE".into(),
                    version: 0,
                },
                Some(1),
            )
            .await
            .is_ok()
        {
            return Err(Error::Storage("stale update was accepted".into()));
        }
        Ok(vec![first, second])
    }
    let memory = MemoryStore::default();
    let sqlite = SqliteStore::in_memory().await?;
    if exercise(&memory).await? != exercise(&sqlite).await? {
        return Err(Error::Storage("adapter divergence".into()));
    }
    Ok(())
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum JobState {
    Planned,
    Admitted,
    Running,
    AwaitingInput,
    AwaitingAuthority,
    Succeeded,
    Failed,
    Ambiguous,
    Refused,
    Superseded,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GovernorJob {
    pub id: String,
    pub state: JobState,
    pub idempotency_key: String,
    pub required_authority: Authority,
    pub attempts: u32,
    pub result: Option<String>,
}

impl GovernorJob {
    pub fn new(id: impl Into<String>, key: impl Into<String>, authority: Authority) -> Self {
        Self {
            id: id.into(),
            state: JobState::Planned,
            idempotency_key: key.into(),
            required_authority: authority,
            attempts: 0,
            result: None,
        }
    }
}

#[derive(Debug, Default)]
pub struct GovernorRuntime {
    completed: Mutex<BTreeMap<String, String>>,
}

impl GovernorRuntime {
    pub async fn execute<F, Fut>(
        &self,
        job: &mut GovernorJob,
        granted: Authority,
        operation: F,
    ) -> Result<String, Error>
    where
        F: FnOnce() -> Fut,
        Fut: std::future::Future<Output = Result<String, Error>>,
    {
        if let Some(result) = self
            .completed
            .lock()
            .await
            .get(&job.idempotency_key)
            .cloned()
        {
            job.state = JobState::Succeeded;
            job.result = Some(result.clone());
            return Ok(result);
        }
        if job.idempotency_key.is_empty() {
            job.state = JobState::Refused;
            return Err(Error::Refused("idempotency key required".into()));
        }
        if !granted.permits(job.required_authority) {
            job.state = JobState::AwaitingAuthority;
            return Err(Error::Refused("authority denied".into()));
        }
        job.state = JobState::Running;
        job.attempts = job.attempts.saturating_add(1);
        match tokio::time::timeout(Duration::from_secs(5), operation()).await {
            Ok(Ok(result)) => {
                self.completed
                    .lock()
                    .await
                    .insert(job.idempotency_key.clone(), result.clone());
                job.state = JobState::Succeeded;
                job.result = Some(result.clone());
                Ok(result)
            }
            Ok(Err(error)) => {
                job.state = JobState::Failed;
                Err(error)
            }
            Err(_) => {
                job.state = JobState::Ambiguous;
                Err(Error::Refused(
                    "timeout is ambiguous; automatic retry refused".into(),
                ))
            }
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolContract {
    pub name: String,
    pub read_only: bool,
    pub destructive: bool,
    pub idempotent: bool,
    pub required_authority: Authority,
    pub receipt_required: bool,
    pub timeout_ms: u64,
}

#[derive(Debug, Default)]
pub struct McpBoundary;

impl McpBoundary {
    pub fn tools() -> Vec<ToolContract> {
        vec![
            ToolContract {
                name: "ecosystem.crown".into(),
                read_only: true,
                destructive: false,
                idempotent: true,
                required_authority: Authority::Observe,
                receipt_required: false,
                timeout_ms: 5_000,
            },
            ToolContract {
                name: "ecosystem.mutate".into(),
                read_only: false,
                destructive: true,
                idempotent: true,
                required_authority: Authority::ModifyExternalObject,
                receipt_required: true,
                timeout_ms: 5_000,
            },
        ]
    }

    pub fn handle(request: &str, granted: Authority) -> Result<String, Error> {
        let message: Value =
            serde_json::from_str(request).map_err(|e| Error::Mcp(e.to_string()))?;
        let id = message.get("id").cloned().unwrap_or(Value::Null);
        let method = message
            .get("method")
            .and_then(Value::as_str)
            .ok_or_else(|| Error::Mcp("method required".into()))?;
        let result = match method {
            "initialize" => {
                json!({"protocolVersion":"2025-06-18","serverInfo":{"name":"chatman-ecosystem","version":"0.1.0"},"capabilities":{"tools":{}}})
            }
            "tools/list" => {
                serde_json::to_value(Self::tools()).map_err(|e| Error::Mcp(e.to_string()))?
            }
            "tools/call" => {
                let name = message
                    .pointer("/params/name")
                    .and_then(Value::as_str)
                    .ok_or_else(|| Error::Mcp("tool name required".into()))?;
                let tool = Self::tools()
                    .into_iter()
                    .find(|x| x.name == name)
                    .ok_or_else(|| Error::Mcp(format!("unknown tool `{name}`")))?;
                if !granted.permits(tool.required_authority) {
                    return Ok(rpc_error(id, -32001, "authority denied"));
                }
                if tool.destructive {
                    return Ok(rpc_error(id, -32002, "mutation must pass through broker"));
                }
                json!({"content":[{"type":"text","text":"CROWN_QUERY_ADMITTED"}]})
            }
            _ => return Ok(rpc_error(id, -32601, "method not found")),
        };
        serde_json::to_string(&json!({"jsonrpc":"2.0","id":id,"result":result}))
            .map_err(|e| Error::Mcp(e.to_string()))
    }
}

fn rpc_error(id: Value, code: i64, message: &str) -> String {
    json!({"jsonrpc":"2.0","id":id,"error":{"code":code,"message":message}}).to_string()
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GitHubObservation {
    pub repository: String,
    pub default_branch: String,
    pub head_sha: String,
    pub private: bool,
}

impl GitHubObservation {
    pub fn normalize(input: &str) -> Result<Self, Error> {
        let value: Value =
            serde_json::from_str(input).map_err(|e| Error::Connector(e.to_string()))?;
        let text = |name: &str| {
            value
                .get(name)
                .and_then(Value::as_str)
                .map(str::to_owned)
                .ok_or_else(|| Error::Connector(format!("{name} required")))
        };
        let head_sha = text("head_sha")?;
        if head_sha.len() != 40 || !head_sha.chars().all(|c| c.is_ascii_hexdigit()) {
            return Err(Error::Connector("invalid head SHA".into()));
        }
        Ok(Self {
            repository: text("full_name")?,
            default_branch: text("default_branch")?,
            head_sha: head_sha.to_ascii_lowercase(),
            private: value
                .get("private")
                .and_then(Value::as_bool)
                .unwrap_or(false),
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DocumentObservation {
    pub id: String,
    pub revision: String,
    pub path: String,
    pub digest: String,
}

impl DocumentObservation {
    pub fn normalize(input: &str) -> Result<Self, Error> {
        let value: Value =
            serde_json::from_str(input).map_err(|e| Error::Connector(e.to_string()))?;
        let text = |name: &str| {
            value
                .get(name)
                .and_then(Value::as_str)
                .map(str::to_owned)
                .ok_or_else(|| Error::Connector(format!("{name} required")))
        };
        let item = Self {
            id: text("id")?,
            revision: text("revision")?,
            path: text("path")?,
            digest: text("digest")?,
        };
        if item.path.starts_with('/')
            || item.path.contains("..")
            || !item.digest.starts_with("blake3:")
        {
            return Err(Error::Connector("noncanonical document observation".into()));
        }
        Ok(item)
    }
}

pub fn standing_for_job(state: JobState) -> Standing {
    match state {
        JobState::Succeeded => Standing::Alive,
        JobState::Failed | JobState::Ambiguous | JobState::AwaitingAuthority => Standing::Blocked,
        JobState::Refused => Standing::Rejected,
        JobState::Superseded => Standing::Superseded,
        JobState::Planned | JobState::Admitted | JobState::Running | JobState::AwaitingInput => {
            Standing::PartialAlive
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn stores_are_equivalent() -> Result<(), Error> {
        differential_store_check().await
    }

    #[tokio::test]
    async fn governor_is_authority_bounded_and_idempotent() -> Result<(), Error> {
        let runtime = GovernorRuntime::default();
        let mut denied = GovernorJob::new("denied", "denied-key", Authority::Draft);
        assert!(
            runtime
                .execute(&mut denied, Authority::Observe, || async {
                    Ok("no".into())
                })
                .await
                .is_err()
        );
        assert_eq!(denied.state, JobState::AwaitingAuthority);
        let mut first = GovernorJob::new("first", "same-key", Authority::Observe);
        let one = runtime
            .execute(&mut first, Authority::Observe, || async {
                Ok("receipt:1".into())
            })
            .await?;
        let mut duplicate = GovernorJob::new("duplicate", "same-key", Authority::Observe);
        let two = runtime
            .execute(&mut duplicate, Authority::Observe, || async {
                Ok("receipt:2".into())
            })
            .await?;
        assert_eq!(one, two);
        assert_eq!(duplicate.attempts, 0);
        Ok(())
    }

    #[test]
    fn mcp_and_connectors_fail_closed() -> Result<(), Error> {
        let mutation = r#"{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"ecosystem.mutate"}}"#;
        assert!(McpBoundary::handle(mutation, Authority::ModifyExternalObject)?.contains("broker"));
        assert!(
            McpBoundary::handle(
                r#"{"jsonrpc":"2.0","id":2,"method":"missing"}"#,
                Authority::Observe
            )?
            .contains("-32601")
        );
        let github = GitHubObservation::normalize(
            r#"{"full_name":"seanchatmangpt/chatman-ecosystem","default_branch":"main","head_sha":"0123456789abcdef0123456789abcdef01234567","private":false}"#,
        )?;
        assert_eq!(github.default_branch, "main");
        assert!(
            GitHubObservation::normalize(
                r#"{"full_name":"x/y","default_branch":"main","head_sha":"bad"}"#
            )
            .is_err()
        );
        let document = DocumentObservation::normalize(&format!(
            r#"{{"id":"doc","revision":"1","path":"docs/README.md","digest":"blake3:{}"}}"#,
            "0".repeat(64)
        ))?;
        assert_eq!(document.path, "docs/README.md");
        Ok(())
    }
}
