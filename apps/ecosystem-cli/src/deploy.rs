//! Deployment surface for the `ecosystem` binary: schema introspection, MCP
//! stdio serving, HTTP serving, and Kubernetes/container manifest rendering.
//!
//! This module never duplicates the existing hand-rolled command dispatch in
//! `main.rs`. It builds a parallel `clap::Command` schema that mirrors the
//! same command surface, then uses `clap-noun-verb-deploy` to project that
//! schema into MCP/HTTP/Kubernetes/container form. Admitted tool calls are
//! executed by re-invoking this same `ecosystem` binary as a child process
//! with the validated argv, so the actual domain behavior always lives in
//! `main.rs`'s `execute()`, not here.

use clap::{Arg, ArgAction, Command};
use clap_noun_verb_deploy::container::ContainerConfig;
use clap_noun_verb_deploy::kubernetes::KubernetesConfig;
use clap_noun_verb_deploy::mcp::McpServer;
use clap_noun_verb_deploy::http::HttpServer;
use clap_noun_verb_deploy::{CliSchema, CommandAllowList, ProcessExecutor};
use std::env;
use std::io::{stdin, stdout};
use std::net::TcpListener;

const DEFAULT_HTTP_BIND: &str = "0.0.0.0:8080";

/// Build the `clap::Command` schema mirroring `main.rs`'s existing hand-rolled
/// command surface. This is a read-only projection: it is never used to parse
/// argv directly, only to derive the deploy schema/tools/allow-list.
fn schema_command() -> Command {
    Command::new("ecosystem")
        .about("Chatman Ecosystem control plane")
        .subcommand(Command::new("catalog").subcommand(Command::new("validate")))
        .subcommand(
            Command::new("capability").arg(
                Arg::new("args")
                    .num_args(0..)
                    .trailing_var_arg(true)
                    .action(ArgAction::Append),
            ),
        )
        .subcommand(Command::new("standing").subcommand(Command::new("calculate")))
        .subcommand(
            Command::new("receipt")
                .subcommand(Command::new("seal"))
                .subcommand(Command::new("verify-all")),
        )
        .subcommand(
            Command::new("projection")
                .subcommand(Command::new("render"))
                .subcommand(Command::new("check")),
        )
        .subcommand(Command::new("architecture").subcommand(Command::new("check")))
        .subcommand(Command::new("storage").subcommand(Command::new("verify")))
        .subcommand(Command::new("mcp").subcommand(Command::new("handle")))
        .subcommand(
            Command::new("crown")
                .arg(Arg::new("json").long("json").action(ArgAction::SetTrue))
                .arg(Arg::new("verify").long("verify").action(ArgAction::SetTrue)),
        )
}

/// Build a `ProcessExecutor` that re-execs this same `ecosystem` binary for
/// every admitted tool call, and a `CommandAllowList` restricted to exactly
/// the callable command paths present in the schema (least authority: the
/// deploy surface can never admit a command path the schema does not expose).
fn executor_and_policy() -> Result<(ProcessExecutor, CommandAllowList, CliSchema), String> {
    let schema = CliSchema::from_command(&schema_command());
    let current_exe = env::current_exe().map_err(|error| error.to_string())?;
    let executor = ProcessExecutor::new(current_exe);
    let policy = CommandAllowList::new(
        schema.commands.iter().filter(|command| command.callable).map(|command| command.path.clone()),
    );
    Ok((executor, policy, schema))
}

fn run_schema() -> Result<String, String> {
    let schema = CliSchema::from_command(&schema_command());
    serde_json::to_string_pretty(&schema).map_err(|error| error.to_string())
}

fn run_mcp() -> Result<String, String> {
    let (executor, policy, schema) = executor_and_policy()?;
    let server = McpServer::with_policy("ecosystem", env!("CARGO_PKG_VERSION"), schema, executor, policy);
    server
        .serve_stdio(stdin().lock(), stdout().lock())
        .map_err(|error| error.to_string())?;
    Ok(String::new())
}

fn resolve_bind(arguments: &[String]) -> String {
    let mut iterator = arguments.iter();
    while let Some(argument) = iterator.next() {
        if argument == "--bind"
            && let Some(value) = iterator.next()
        {
            return value.clone();
        }
    }
    env::var("ECOSYSTEM_DEPLOY_HTTP_BIND").unwrap_or_else(|_| DEFAULT_HTTP_BIND.to_owned())
}

fn run_http(arguments: &[String]) -> Result<String, String> {
    let (executor, policy, schema) = executor_and_policy()?;
    let server = HttpServer::with_policy(schema, executor, policy);
    let bind = resolve_bind(arguments);
    let listener = TcpListener::bind(&bind).map_err(|error| error.to_string())?;
    server.serve(listener).map_err(|error| error.to_string())?;
    Ok(String::new())
}

fn deploy_binary_command() -> Vec<String> {
    vec!["ecosystem".to_owned()]
}

fn deploy_binary_args() -> Vec<String> {
    vec!["deploy".to_owned(), "mcp".to_owned()]
}

fn run_k8s() -> Result<String, String> {
    let mut config = KubernetesConfig::new("ecosystem-cli", "ecosystem-cli:latest");
    config.command = deploy_binary_command();
    config.args = deploy_binary_args();
    config.port = 8080;
    config.render().map_err(|error| error.to_string())
}

fn run_container() -> Result<String, String> {
    let mut config = ContainerConfig::new("ecosystem-cli", "ecosystem");
    config.args = deploy_binary_args();
    config.port = 8080;
    config.render_dockerfile().map_err(|error| error.to_string())
}

/// Dispatch a `deploy` command area. `arguments` is the full argv (including
/// the leading `"deploy"` element) as passed to the process.
pub fn run_deploy(arguments: &[String]) -> Result<String, String> {
    match arguments {
        [_, area] if area == "schema" => run_schema(),
        [_, area] if area == "mcp" => run_mcp(),
        [_, area, rest @ ..] if area == "http" => run_http(rest),
        [_, area] if area == "k8s" => run_k8s(),
        [_, area] if area == "container" => run_container(),
        _ => Err(
            "REFUSED:UNKNOWN_DEPLOY_COMMAND usage: ecosystem deploy <schema|mcp|http|k8s|container>"
                .to_owned(),
        ),
    }
}
