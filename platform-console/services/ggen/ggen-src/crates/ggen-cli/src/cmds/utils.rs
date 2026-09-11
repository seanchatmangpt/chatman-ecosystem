//! Utils Commands - clap-noun-verb v3.4.0 Migration
//!
//! This module implements utility commands using the v3.4.0 #[verb] pattern.

use clap_noun_verb::Result;
use clap_noun_verb_macros::verb;
use serde::Serialize;
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;

// ============================================================================
// Output Types
// ============================================================================

#[derive(Serialize)]
struct EnvOutput {
    variables: HashMap<String, String>,
    total: usize,
}

/// Output for setting environment variables
#[derive(Serialize)]
#[allow(dead_code)]
struct EnvSetOutput {
    key: String,
    value: String,
    success: bool,
}

// ============================================================================
// Verb Functions
// ============================================================================

/// Manage environment variables
#[verb]
fn env(list: bool, get: Option<String>, set: Option<String>, system: bool) -> Result<EnvOutput> {
    let variables = run_env(list, get.as_deref(), set.as_deref(), system);
    let total = variables.len();
    Ok(EnvOutput { variables, total })
}

/// Resolve the config-file path backing a given env scope.
///
/// - `system == true`  -> a system-wide path, overridable via `GGEN_SYSTEM_ENV_PATH`
///   (defaults to `/etc/ggen/env`).
/// - `system == false` -> a user-level path, overridable via `GGEN_USER_ENV_PATH`
///   (defaults to `$HOME/.config/ggen/env`).
///
/// The override env vars exist so tests (and real deployments that can't write to
/// `/etc`) can point each scope at an isolated, real file on disk rather than a
/// shared or fabricated location.
fn scope_file_path(system: bool) -> PathBuf {
    if system {
        std::env::var("GGEN_SYSTEM_ENV_PATH")
            .map(PathBuf::from)
            .unwrap_or_else(|_| PathBuf::from("/etc/ggen/env"))
    } else {
        std::env::var("GGEN_USER_ENV_PATH")
            .map(PathBuf::from)
            .unwrap_or_else(|_| {
                let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
                PathBuf::from(home).join(".config/ggen/env")
            })
    }
}

/// Load `key=value` pairs (one per line, `#`-prefixed comments and blank lines
/// skipped) from the scope's backing file. Missing file => empty map, not an error:
/// a scope that has never been written to is a legitimate, common state.
fn load_scope_vars(system: bool) -> HashMap<String, String> {
    let path = scope_file_path(system);
    let mut vars = HashMap::new();
    if let Ok(contents) = fs::read_to_string(&path) {
        for line in contents.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with('#') {
                continue;
            }
            if let Some((key, value)) = line.split_once('=') {
                vars.insert(key.trim().to_string(), value.trim().to_string());
            }
        }
    }
    vars
}

/// Persist `key=value` into the scope's backing file, creating parent directories
/// and the file itself as needed, preserving any other keys already stored there.
fn store_scope_var(system: bool, key: &str, value: &str) -> std::io::Result<()> {
    let path = scope_file_path(system);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    let mut vars = load_scope_vars(system);
    vars.insert(key.to_string(), value.to_string());
    let mut contents = String::new();
    for (k, v) in &vars {
        contents.push_str(k);
        contents.push('=');
        contents.push_str(v);
        contents.push('\n');
    }
    fs::write(path, contents)
}

fn run_env(
    list: bool, get: Option<&str>, set: Option<&str>, system: bool,
) -> HashMap<String, String> {
    let mut variables = HashMap::new();

    if let Some(key) = get {
        // System scope resolves only against the system-level store (real
        // process env vars are inherently user/session-scoped, so a --system
        // lookup must not fall back to them). Default (user) scope checks the
        // user-level store first, then falls back to the real process env --
        // preserving the pre-existing default behavior for callers who never
        // wrote a user-scope file.
        if system {
            if let Some(value) = load_scope_vars(true).get(key) {
                variables.insert(key.to_string(), value.clone());
            }
        } else if let Some(value) = load_scope_vars(false).get(key) {
            variables.insert(key.to_string(), value.clone());
        } else if let Ok(value) = std::env::var(key) {
            variables.insert(key.to_string(), value);
        }
    } else if let Some(kv) = set {
        if let Some((key, value)) = kv.split_once('=') {
            if store_scope_var(system, key, value).is_ok() {
                variables.insert(key.to_string(), value.to_string());
            }
        }
    }

    if list || (get.is_none() && set.is_none()) {
        if system {
            variables.extend(load_scope_vars(true));
        } else {
            collect_ggen_env_vars(&mut variables);
            variables.extend(load_scope_vars(false));
        }
    }

    variables
}

fn collect_ggen_env_vars(vars: &mut HashMap<String, String>) {
    for (key, value) in std::env::vars() {
        if key.starts_with("GGEN_") || key.starts_with("RUST_") || key == "HOME" || key == "PATH" {
            vars.insert(key, value);
        }
    }
}

#[cfg(test)]
mod system_flag_tests {
    use super::*;
    use std::sync::Mutex;

    // Serializes tests that mutate process-global env vars (GGEN_SYSTEM_ENV_PATH /
    // GGEN_USER_ENV_PATH) so parallel test threads don't race each other's scope
    // paths. This is a real synchronization primitive over real shared process
    // state, not a mock of any collaborator.
    static ENV_LOCK: Mutex<()> = Mutex::new(());

    struct TempEnvGuard {
        system_path: PathBuf,
        user_path: PathBuf,
    }

    impl Drop for TempEnvGuard {
        fn drop(&mut self) {
            let _ = fs::remove_file(&self.system_path);
            let _ = fs::remove_file(&self.user_path);
            std::env::remove_var("GGEN_SYSTEM_ENV_PATH");
            std::env::remove_var("GGEN_USER_ENV_PATH");
        }
    }

    fn setup_isolated_scopes(tag: &str) -> TempEnvGuard {
        let dir = std::env::temp_dir().join(format!("ggen-cli-system-flag-test-{tag}"));
        let _ = fs::create_dir_all(&dir);
        let system_path = dir.join("system-env");
        let user_path = dir.join("user-env");
        let _ = fs::remove_file(&system_path);
        let _ = fs::remove_file(&user_path);
        std::env::set_var("GGEN_SYSTEM_ENV_PATH", &system_path);
        std::env::set_var("GGEN_USER_ENV_PATH", &user_path);
        TempEnvGuard {
            system_path,
            user_path,
        }
    }

    /// Setting a value with `--system` must land in the system-scope store and
    /// must NOT be visible from a default (user-scope) lookup of the same key --
    /// proving the flag actually changes which real file on disk is touched,
    /// rather than being discarded as a no-op.
    #[test]
    fn system_flag_scopes_writes_to_a_separate_store_from_default() {
        let _guard = ENV_LOCK.lock().unwrap();
        let env_guard = setup_isolated_scopes("separate-store");

        // Write the same key with two different values into the two scopes.
        let system_result = run_env(false, None, Some("GGEN_SCOPE_TEST=system-value"), true);
        let user_result = run_env(false, None, Some("GGEN_SCOPE_TEST=user-value"), false);

        assert_eq!(
            system_result.get("GGEN_SCOPE_TEST").map(String::as_str),
            Some("system-value")
        );
        assert_eq!(
            user_result.get("GGEN_SCOPE_TEST").map(String::as_str),
            Some("user-value")
        );

        // Reading back with --system must return the system value, not the user one.
        let read_system = run_env(false, Some("GGEN_SCOPE_TEST"), None, true);
        assert_eq!(
            read_system.get("GGEN_SCOPE_TEST").map(String::as_str),
            Some("system-value"),
            "--system get must resolve against the system-scope store"
        );

        // Reading back without --system must return the user value, not the system one.
        let read_user = run_env(false, Some("GGEN_SCOPE_TEST"), None, false);
        assert_eq!(
            read_user.get("GGEN_SCOPE_TEST").map(String::as_str),
            Some("user-value"),
            "default get must resolve against the user-scope store"
        );

        // The two backing files on disk are genuinely different and each holds
        // only its own scope's value -- real structural evidence, not just the
        // in-memory map.
        let system_contents = fs::read_to_string(&env_guard.system_path).unwrap();
        let user_contents = fs::read_to_string(&env_guard.user_path).unwrap();
        assert!(system_contents.contains("GGEN_SCOPE_TEST=system-value"));
        assert!(!system_contents.contains("user-value"));
        assert!(user_contents.contains("GGEN_SCOPE_TEST=user-value"));
        assert!(!user_contents.contains("system-value"));
    }

    /// A key set only in the system scope must not appear in a default-scope
    /// `list`, and vice versa -- proving list is scoped too, not only get/set.
    #[test]
    fn system_flag_scopes_list_independently_of_default() {
        let _guard = ENV_LOCK.lock().unwrap();
        let _env_guard = setup_isolated_scopes("scoped-list");

        run_env(false, None, Some("GGEN_ONLY_SYSTEM=1"), true);
        run_env(false, None, Some("GGEN_ONLY_USER=1"), false);

        let system_list = run_env(true, None, None, true);
        assert!(system_list.contains_key("GGEN_ONLY_SYSTEM"));
        assert!(!system_list.contains_key("GGEN_ONLY_USER"));

        let user_list = run_env(true, None, None, false);
        assert!(user_list.contains_key("GGEN_ONLY_USER"));
        assert!(!user_list.contains_key("GGEN_ONLY_SYSTEM"));
    }

    /// The default (non-system) path still falls back to real process env vars
    /// for keys never written into either file store -- the pre-existing
    /// behavior must be preserved, not just the new --system branch.
    #[test]
    fn default_scope_still_falls_back_to_process_env() {
        let _guard = ENV_LOCK.lock().unwrap();
        let _env_guard = setup_isolated_scopes("process-fallback");

        std::env::set_var("GGEN_PROCESS_FALLBACK_TEST", "from-process-env");
        let result = run_env(false, Some("GGEN_PROCESS_FALLBACK_TEST"), None, false);
        assert_eq!(
            result.get("GGEN_PROCESS_FALLBACK_TEST").map(String::as_str),
            Some("from-process-env")
        );
        std::env::remove_var("GGEN_PROCESS_FALLBACK_TEST");

        // The same key must NOT resolve via --system, since process env vars are
        // not part of the system scope.
        let system_result = run_env(false, Some("GGEN_PROCESS_FALLBACK_TEST"), None, true);
        assert!(system_result.get("GGEN_PROCESS_FALLBACK_TEST").is_none());
    }
}

// ============================================================================
// Ontology-generated command reference (crate::generated_commands)
// ============================================================================

/// One row of the ontology-declared CLI command reference.
#[derive(Serialize)]
struct CommandRefEntry {
    label: String,
    description: String,
}

/// Output for `ggen utils commands`.
#[derive(Serialize)]
struct CommandsReferenceOutput {
    commands: Vec<CommandRefEntry>,
    total: usize,
}

/// List the ontology-declared CLI command reference (generated from
/// `.specify/cli-commands.ttl` into `crate::generated_commands`).
#[verb]
fn commands(describe: Option<String>) -> Result<CommandsReferenceOutput> {
    let commands: Vec<CommandRefEntry> = match describe.as_deref() {
        Some(label) => crate::generated_commands::describe_command(label)
            .map(|comment| CommandRefEntry {
                label: label.to_string(),
                description: comment.to_string(),
            })
            .into_iter()
            .collect(),
        None => crate::generated_commands::COMMANDS_REFERENCE
            .iter()
            .filter(|(_, label, _)| !label.is_empty())
            .map(|(_, label, comment)| CommandRefEntry {
                label: (*label).to_string(),
                description: (*comment).to_string(),
            })
            .collect(),
    };
    let total = commands.len();
    Ok(CommandsReferenceOutput { commands, total })
}
