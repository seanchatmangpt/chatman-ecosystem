#![allow(clippy::doc_markdown, clippy::too_many_lines)]

//! Evidence-bounded DfCM scheduler for the older RevOps-capable repository estate.
//!
//! This executable is a planner, not an actuator. It classifies repository roles,
//! ranks reversible construction opportunities, emits typed refusals, and seals
//! exact-subject planning receipts. External consequences stop at `BRCE_REQUIRED`.

use ecosystem_core::{Authority, Receipt, ReceiptId, Standing};
use serde_json::{Value, json};
use std::collections::BTreeSet;
use std::env;
use std::error::Error as StdError;
use std::fmt;

const MANIFEST_VERSION: &str = "old-estate-revops-dfcm-v1";
const AGE_CUTOFF: &str = "2026-05-19";
const OBSERVED_AT: &str = "2026-08-19T16:51:00-07:00";
const EXPECTED_REPOSITORIES: usize = 23;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum StrategyClass {
    Direct,
    Composable,
    NegativeEvidence,
    DependencyOnly,
    Refused,
}

impl StrategyClass {
    const fn as_str(self) -> &'static str {
        match self {
            Self::Direct => "DIRECT",
            Self::Composable => "COMPOSABLE",
            Self::NegativeEvidence => "NEGATIVE_EVIDENCE",
            Self::DependencyOnly => "DEPENDENCY_ONLY",
            Self::Refused => "REFUSED",
        }
    }

    const fn is_active(self) -> bool {
        matches!(
            self,
            Self::Direct | Self::Composable | Self::NegativeEvidence
        )
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ExecutionMode {
    Construct,
    SimulateOnly,
    ObserveOnly,
    DependencyOnly,
    Refused,
}

impl ExecutionMode {
    const fn as_str(self) -> &'static str {
        match self {
            Self::Construct => "CONSTRUCT",
            Self::SimulateOnly => "SIMULATE_ONLY",
            Self::ObserveOnly => "OBSERVE_ONLY",
            Self::DependencyOnly => "DEPENDENCY_ONLY",
            Self::Refused => "REFUSED",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ExternalEffect {
    None,
    Communicate,
    ModifyExternalObject,
}

impl ExternalEffect {
    const fn as_str(self) -> &'static str {
        match self {
            Self::None => "NONE",
            Self::Communicate => "COMMUNICATE",
            Self::ModifyExternalObject => "MODIFY_EXTERNAL_OBJECT",
        }
    }

    const fn required_authority(self) -> Option<Authority> {
        match self {
            Self::None => None,
            Self::Communicate => Some(Authority::Communicate),
            Self::ModifyExternalObject => Some(Authority::ModifyExternalObject),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Disposition {
    Construct,
    VerifyOnly,
    ReferenceOnly,
    Refused,
}

impl Disposition {
    const fn as_str(self) -> &'static str {
        match self {
            Self::Construct => "CONSTRUCT",
            Self::VerifyOnly => "VERIFY_ONLY",
            Self::ReferenceOnly => "REFERENCE_ONLY",
            Self::Refused => "REFUSED",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum DoStanding {
    NotApplicable,
    RefusedAuthority,
    BrceRequired,
}

impl DoStanding {
    const fn as_str(self) -> &'static str {
        match self {
            Self::NotApplicable => "NOT_APPLICABLE",
            Self::RefusedAuthority => "REFUSED:AUTHORITY",
            Self::BrceRequired => "BRCE_REQUIRED",
        }
    }
}

#[derive(Debug, Clone, Copy)]
struct Metrics {
    edges: u8,
    leverage: u8,
    verifier: u8,
    cost: u8,
    irreversibility: u8,
}

#[derive(Debug, Clone, Copy)]
struct StrategySpec {
    repository: &'static str,
    class: StrategyClass,
    role: &'static str,
    mode: ExecutionMode,
    effect: ExternalEffect,
    mission: &'static str,
    verifier: &'static str,
    falsifier: &'static str,
    dependencies: &'static [&'static str],
    metrics: Metrics,
    refusal: Option<&'static str>,
}

#[derive(Debug, Clone, Copy)]
struct Decision {
    spec: StrategySpec,
    disposition: Disposition,
    score: u64,
    do_standing: DoStanding,
}

impl Decision {
    fn to_json(self) -> Value {
        json!({
            "repository": self.spec.repository,
            "strategy_class": self.spec.class.as_str(),
            "role": self.spec.role,
            "execution_mode": self.spec.mode.as_str(),
            "disposition": self.disposition.as_str(),
            "dfcm_score": self.score,
            "external_effect": self.spec.effect.as_str(),
            "required_authority": self
                .spec
                .effect
                .required_authority()
                .map(authority_name),
            "do_standing": self.do_standing.as_str(),
            "mission": self.spec.mission,
            "verifier": self.spec.verifier,
            "falsifier": self.spec.falsifier,
            "dependencies": self.spec.dependencies,
            "refusal": self.spec.refusal,
        })
    }
}

#[derive(Debug)]
struct CliError(String);

impl fmt::Display for CliError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.0)
    }
}

impl StdError for CliError {}

type CliResult<T> = Result<T, Box<dyn StdError>>;

const fn metrics(
    edges: u8,
    leverage: u8,
    verifier: u8,
    cost: u8,
    irreversibility: u8,
) -> Metrics {
    Metrics {
        edges,
        leverage,
        verifier,
        cost,
        irreversibility,
    }
}

const STRATEGIES: &[StrategySpec] = &[
    StrategySpec {
        repository: "ggen",
        class: StrategyClass::Direct,
        role: "manufacturing_compiler",
        mode: ExecutionMode::Construct,
        effect: ExternalEffect::None,
        mission: "Manufacture admitted RevOps projections without owning outreach DO.",
        verifier: "sync, graph conformance, receipt, replay",
        falsifier: "graph/projection drift or replay mismatch",
        dependencies: &["unrdf", "open-ontologies"],
        metrics: metrics(10, 10, 9, 4, 1),
        refusal: None,
    },
    StrategySpec {
        repository: "open-ontologies",
        class: StrategyClass::Direct,
        role: "admission_receipt_court",
        mode: ExecutionMode::Construct,
        effect: ExternalEffect::None,
        mission: "Admit requirements, work orders, mutations, and artifacts independently.",
        verifier: "recursive admission and external receipt verification",
        falsifier: "gate bypass, tenant leakage, or broken receipt chain",
        dependencies: &["ggen"],
        metrics: metrics(9, 10, 9, 4, 1),
        refusal: None,
    },
    StrategySpec {
        repository: "unrdf",
        class: StrategyClass::Direct,
        role: "semantic_operational_graph",
        mode: ExecutionMode::Construct,
        effect: ExternalEffect::None,
        mission: "Own queryable people, organization, campaign, and opportunity semantics.",
        verifier: "SHACL, SPARQL assertions, deterministic graph replay",
        falsifier: "constraint violation or graph provenance loss",
        dependencies: &["open-ontologies"],
        metrics: metrics(9, 10, 8, 4, 1),
        refusal: None,
    },
    StrategySpec {
        repository: "ostar",
        class: StrategyClass::Direct,
        role: "simulation_proof_laboratory",
        mode: ExecutionMode::SimulateOnly,
        effect: ExternalEffect::None,
        mission: "Simulate and prove revenue mechanics before any external DO boundary.",
        verifier: "RevOps proof gates, OCEL conformance, receipt-chain verification",
        falsifier: "simulation promoted to observed external commercial truth",
        dependencies: &["pm4py", "open-ontologies"],
        metrics: metrics(8, 9, 8, 4, 1),
        refusal: None,
    },
    StrategySpec {
        repository: "chatmangpt",
        class: StrategyClass::Direct,
        role: "legacy_revops_execution_lab",
        mode: ExecutionMode::Construct,
        effect: ExternalEffect::None,
        mission: "Requalify historical CRM and RevOps behavior against the current head.",
        verifier: "current BusinessOS/OSA integration and semantic-convention tests",
        falsifier: "historical commit evidence promoted without current execution",
        dependencies: &["unrdf", "ostar"],
        metrics: metrics(8, 9, 7, 5, 2),
        refusal: None,
    },
    StrategySpec {
        repository: "bcinr",
        class: StrategyClass::Direct,
        role: "publication_lifecycle",
        mode: ExecutionMode::Construct,
        effect: ExternalEffect::Communicate,
        mission: "Compile topic through reviewed publication intent and consequence receipt.",
        verifier: "published standing requires an external connector receipt",
        falsifier: "published standing reached from a local file marker alone",
        dependencies: &["linkedin-public-canon", "open-ontologies"],
        metrics: metrics(7, 9, 9, 3, 5),
        refusal: None,
    },
    StrategySpec {
        repository: "yawl",
        class: StrategyClass::Direct,
        role: "champion_discovery_workflow",
        mode: ExecutionMode::Construct,
        effect: ExternalEffect::Communicate,
        mission: "Orchestrate admitted champion discovery and outreach intent construction.",
        verifier: "workflow conformance, bridge evidence, OCEL export",
        falsifier: "conceptual bridge represented as live access or sent outreach",
        dependencies: &["unrdf", "pm4py"],
        metrics: metrics(7, 8, 7, 4, 5),
        refusal: None,
    },
    StrategySpec {
        repository: "clap-noun-verb",
        class: StrategyClass::Composable,
        role: "typed_revops_control_surface",
        mode: ExecutionMode::Construct,
        effect: ExternalEffect::None,
        mission: "Expose typed RevOps commands without inventing business truth.",
        verifier: "dispatch, structured consequence, and capability-standing tests",
        falsifier: "command bypasses the capability that owns domain state",
        dependencies: &["unrdf", "open-ontologies"],
        metrics: metrics(6, 8, 9, 3, 1),
        refusal: None,
    },
    StrategySpec {
        repository: "pyn8n",
        class: StrategyClass::Composable,
        role: "integration_fabric",
        mode: ExecutionMode::Construct,
        effect: ExternalEffect::ModifyExternalObject,
        mission: "Execute admitted workflow handoffs and retries behind external authority.",
        verifier: "integration tests, execution logs, idempotency and retry evidence",
        falsifier: "workflow self-authorizes remote mutation or outreach",
        dependencies: &["Arazzo-Specification", "open-ontologies"],
        metrics: metrics(6, 8, 7, 4, 6),
        refusal: None,
    },
    StrategySpec {
        repository: "knhk",
        class: StrategyClass::Composable,
        role: "brokered_execution_evidence",
        mode: ExecutionMode::Construct,
        effect: ExternalEffect::None,
        mission: "Supply authority, broker, receipt, replay, and negative-control primitives.",
        verifier: "current broker, receipt, replay, and exact-head checks",
        falsifier: "archived claim outranks current evidence or CONSTRUCT becomes DO",
        dependencies: &["open-ontologies"],
        metrics: metrics(7, 9, 6, 5, 2),
        refusal: None,
    },
    StrategySpec {
        repository: "chatman-nano-stack",
        class: StrategyClass::NegativeEvidence,
        role: "adversarial_false_claim_corpus",
        mode: ExecutionMode::ObserveOnly,
        effect: ExternalEffect::None,
        mission: "Preserve fictional LinkedIn/job simulations as negative controls.",
        verifier: "simulation-to-external-outcome promotion must be rejected",
        falsifier: "fictional event accepted as platform, employment, or revenue truth",
        dependencies: &[],
        metrics: metrics(5, 8, 10, 2, 1),
        refusal: None,
    },
    StrategySpec {
        repository: "Arazzo-Specification",
        class: StrategyClass::DependencyOnly,
        role: "portable_api_workflow_contract",
        mode: ExecutionMode::DependencyOnly,
        effect: ExternalEffect::None,
        mission: "Consume the portable API workflow contract without GTM-specific mutation.",
        verifier: "Arazzo conformance in consuming projections",
        falsifier: "Chatman campaign semantics injected into the generic specification",
        dependencies: &[],
        metrics: metrics(0, 7, 8, 1, 1),
        refusal: None,
    },
    StrategySpec {
        repository: "pm4py",
        class: StrategyClass::DependencyOnly,
        role: "process_mining_oracle",
        mode: ExecutionMode::DependencyOnly,
        effect: ExternalEffect::None,
        mission: "Consume PM4Py as a process-discovery and conformance oracle.",
        verifier: "comparative process evidence in consuming systems",
        falsifier: "upstream process source mutated solely for Chatman GTM policy",
        dependencies: &[],
        metrics: metrics(0, 8, 9, 1, 1),
        refusal: None,
    },
    StrategySpec {
        repository: "ash_state_machine",
        class: StrategyClass::DependencyOnly,
        role: "state_machine_primitive",
        mode: ExecutionMode::DependencyOnly,
        effect: ExternalEffect::None,
        mission: "Provide generic resource lifecycle semantics to consumers.",
        verifier: "consumer state-transition tests",
        falsifier: "campaign doctrine embedded into the generic state-machine library",
        dependencies: &[],
        metrics: metrics(0, 6, 8, 1, 1),
        refusal: None,
    },
    StrategySpec {
        repository: "ash_paper_trail",
        class: StrategyClass::DependencyOnly,
        role: "resource_audit_primitive",
        mode: ExecutionMode::DependencyOnly,
        effect: ExternalEffect::None,
        mission: "Provide generic resource-change audit history to consumers.",
        verifier: "consumer mutation-audit tests",
        falsifier: "generic audit library rewritten around one GTM program",
        dependencies: &[],
        metrics: metrics(0, 6, 8, 1, 1),
        refusal: None,
    },
    StrategySpec {
        repository: "ash_cloak",
        class: StrategyClass::DependencyOnly,
        role: "sensitive_field_protection",
        mode: ExecutionMode::DependencyOnly,
        effect: ExternalEffect::None,
        mission: "Protect sensitive fields without owning business semantics.",
        verifier: "consumer encryption and key-boundary tests",
        falsifier: "sensitive data copied into an unprotected RevOps projection",
        dependencies: &[],
        metrics: metrics(0, 7, 8, 1, 1),
        refusal: None,
    },
    StrategySpec {
        repository: "ash_events",
        class: StrategyClass::DependencyOnly,
        role: "event_replay_primitive",
        mode: ExecutionMode::DependencyOnly,
        effect: ExternalEffect::None,
        mission: "Provide actor-attributed event persistence and replay to consumers.",
        verifier: "consumer event-log replay equality",
        falsifier: "event history cannot reconstruct admitted resource state",
        dependencies: &[],
        metrics: metrics(0, 7, 8, 1, 1),
        refusal: None,
    },
    StrategySpec {
        repository: "ash_oban",
        class: StrategyClass::DependencyOnly,
        role: "background_work_primitive",
        mode: ExecutionMode::DependencyOnly,
        effect: ExternalEffect::None,
        mission: "Schedule already-admitted background work in consuming systems.",
        verifier: "consumer scheduling and idempotency tests",
        falsifier: "scheduling confused with authority for an external consequence",
        dependencies: &[],
        metrics: metrics(0, 6, 8, 1, 1),
        refusal: None,
    },
    StrategySpec {
        repository: "ash_double_entry",
        class: StrategyClass::DependencyOnly,
        role: "accounting_primitive",
        mode: ExecutionMode::DependencyOnly,
        effect: ExternalEffect::None,
        mission: "Account only for booked monetary consequences in consumers.",
        verifier: "consumer balance and transfer invariants",
        falsifier: "engagement or pipeline probability recorded as realized revenue",
        dependencies: &[],
        metrics: metrics(0, 7, 8, 1, 1),
        refusal: None,
    },
    StrategySpec {
        repository: "twitter",
        class: StrategyClass::Refused,
        role: "name_only_false_friend",
        mode: ExecutionMode::Refused,
        effect: ExternalEffect::None,
        mission: "Refuse social-distribution standing from an Ash example application.",
        verifier: "repository-purpose inspection",
        falsifier: "repository name used as evidence of social distribution capability",
        dependencies: &[],
        metrics: metrics(0, 0, 10, 1, 1),
        refusal: Some("REFUSED:NO_ADMITTED_REVOPS_SUBJECT"),
    },
    StrategySpec {
        repository: "chiefofstaffgpt",
        class: StrategyClass::Refused,
        role: "name_only_false_friend",
        mode: ExecutionMode::Refused,
        effect: ExternalEffect::None,
        mission: "Refuse agent standing from a Celery-on-Render example repository.",
        verifier: "repository-purpose inspection",
        falsifier: "repository name promoted into agent capability without evidence",
        dependencies: &[],
        metrics: metrics(0, 0, 10, 1, 1),
        refusal: Some("REFUSED:NO_ADMITTED_REVOPS_SUBJECT"),
    },
    StrategySpec {
        repository: "pro-landing",
        class: StrategyClass::Refused,
        role: "generic_template",
        mode: ExecutionMode::Refused,
        effect: ExternalEffect::None,
        mission: "Refuse GTM-product standing from a generic Nuxt landing starter.",
        verifier: "repository-purpose inspection",
        falsifier: "generic template counted as a production acquisition surface",
        dependencies: &[],
        metrics: metrics(0, 0, 10, 1, 1),
        refusal: Some("REFUSED:NO_ADMITTED_REVOPS_SUBJECT"),
    },
    StrategySpec {
        repository: "helpdesk",
        class: StrategyClass::Refused,
        role: "generic_template",
        mode: ExecutionMode::Refused,
        effect: ExternalEffect::None,
        mission: "Refuse customer-success standing from unadmitted Phoenix boilerplate.",
        verifier: "repository-purpose inspection",
        falsifier: "framework starter represented as an operational helpdesk",
        dependencies: &[],
        metrics: metrics(0, 0, 10, 1, 1),
        refusal: Some("REFUSED:NO_ADMITTED_REVOPS_SUBJECT"),
    },
];

fn authority_name(authority: Authority) -> &'static str {
    match authority {
        Authority::Observe => "observe",
        Authority::Classify => "classify",
        Authority::Draft => "draft",
        Authority::PersistControlPlane => "persist-control-plane",
        Authority::OpenDraftPullRequest => "open-draft-pull-request",
        Authority::ModifyExternalObject => "modify-external-object",
        Authority::Communicate => "communicate",
        Authority::Merge => "merge",
        Authority::Delete => "delete",
        Authority::Spend => "spend",
        Authority::Approve => "approve",
        Authority::Release => "release",
    }
}

fn parse_authority(value: &str) -> Result<Authority, CliError> {
    match value {
        "observe" => Ok(Authority::Observe),
        "classify" => Ok(Authority::Classify),
        "draft" => Ok(Authority::Draft),
        "persist-control-plane" => Ok(Authority::PersistControlPlane),
        "open-draft-pull-request" => Ok(Authority::OpenDraftPullRequest),
        "modify-external-object" => Ok(Authority::ModifyExternalObject),
        "communicate" => Ok(Authority::Communicate),
        "merge" => Ok(Authority::Merge),
        "delete" => Ok(Authority::Delete),
        "spend" => Ok(Authority::Spend),
        "approve" => Ok(Authority::Approve),
        "release" => Ok(Authority::Release),
        _ => Err(CliError(format!("unknown exact authority `{value}`"))),
    }
}

fn disposition(spec: StrategySpec) -> Disposition {
    match spec.class {
        StrategyClass::Direct | StrategyClass::Composable => Disposition::Construct,
        StrategyClass::NegativeEvidence => Disposition::VerifyOnly,
        StrategyClass::DependencyOnly => Disposition::ReferenceOnly,
        StrategyClass::Refused => Disposition::Refused,
    }
}

fn dfcm_score(spec: StrategySpec) -> u64 {
    if !spec.class.is_active() {
        return 0;
    }
    let reversibility = 11_u64.saturating_sub(u64::from(spec.metrics.irreversibility.min(10)));
    let cost = u64::from(spec.metrics.cost.max(1));
    u64::from(spec.metrics.edges)
        * u64::from(spec.metrics.leverage)
        * u64::from(spec.metrics.verifier)
        * reversibility
        * 100
        / cost
}

fn do_standing(spec: StrategySpec, granted: Option<Authority>) -> DoStanding {
    let Some(required) = spec.effect.required_authority() else {
        return DoStanding::NotApplicable;
    };
    if granted.is_some_and(|authority| authority.permits(required)) {
        DoStanding::BrceRequired
    } else {
        DoStanding::RefusedAuthority
    }
}

fn evaluate(spec: StrategySpec, granted: Option<Authority>) -> Decision {
    Decision {
        spec,
        disposition: disposition(spec),
        score: dfcm_score(spec),
        do_standing: do_standing(spec, granted),
    }
}

fn plan(granted: Option<Authority>) -> Vec<Decision> {
    let mut decisions = STRATEGIES
        .iter()
        .copied()
        .map(|spec| evaluate(spec, granted))
        .collect::<Vec<_>>();
    decisions.sort_by(|left, right| {
        right
            .score
            .cmp(&left.score)
            .then_with(|| left.spec.repository.cmp(right.spec.repository))
    });
    decisions
}

fn repository_tail(value: &str) -> &str {
    value.rsplit('/').next().unwrap_or(value)
}

fn find_strategy(repository: &str) -> Result<StrategySpec, CliError> {
    let wanted = repository_tail(repository);
    STRATEGIES
        .iter()
        .copied()
        .find(|spec| spec.repository == wanted)
        .ok_or_else(|| {
            CliError(format!(
                "repository `{repository}` is not in {MANIFEST_VERSION}"
            ))
        })
}

fn validate_manifest() -> Result<Value, CliError> {
    if STRATEGIES.len() != EXPECTED_REPOSITORIES {
        return Err(CliError(format!(
            "manifest has {}; expected {EXPECTED_REPOSITORIES}",
            STRATEGIES.len()
        )));
    }

    let mut names = BTreeSet::new();
    for spec in STRATEGIES {
        if !names.insert(spec.repository) {
            return Err(CliError(format!(
                "duplicate repository strategy `{}`",
                spec.repository
            )));
        }
        if spec.mission.trim().is_empty()
            || spec.verifier.trim().is_empty()
            || spec.falsifier.trim().is_empty()
        {
            return Err(CliError(format!(
                "repository `{}` lacks mission/verifier/falsifier closure",
                spec.repository
            )));
        }
        if spec.class == StrategyClass::Refused && spec.refusal.is_none() {
            return Err(CliError(format!(
                "refused repository `{}` lacks a typed refusal",
                spec.repository
            )));
        }
        if spec.class != StrategyClass::Refused && spec.refusal.is_some() {
            return Err(CliError(format!(
                "non-refused repository `{}` carries a refusal",
                spec.repository
            )));
        }
        if spec.class == StrategyClass::DependencyOnly
            && (spec.mode != ExecutionMode::DependencyOnly
                || spec.effect != ExternalEffect::None)
        {
            return Err(CliError(format!(
                "dependency-only repository `{}` crossed its fence",
                spec.repository
            )));
        }
        if spec.class == StrategyClass::Refused
            && (spec.mode != ExecutionMode::Refused || spec.effect != ExternalEffect::None)
        {
            return Err(CliError(format!(
                "refused repository `{}` crossed its fence",
                spec.repository
            )));
        }
    }

    let ostar = find_strategy("ostar")?;
    if ostar.mode != ExecutionMode::SimulateOnly || ostar.effect != ExternalEffect::None {
        return Err(CliError(
            "ostar must remain SIMULATE_ONLY with no external effect".into(),
        ));
    }

    let nano = find_strategy("chatman-nano-stack")?;
    if nano.class != StrategyClass::NegativeEvidence
        || nano.mode != ExecutionMode::ObserveOnly
    {
        return Err(CliError(
            "chatman-nano-stack must remain negative evidence".into(),
        ));
    }

    for repository in ["bcinr", "yawl"] {
        if find_strategy(repository)?.effect != ExternalEffect::Communicate {
            return Err(CliError(format!(
                "{repository} must preserve the COMMUNICATE fence"
            )));
        }
    }

    if find_strategy("pyn8n")?.effect != ExternalEffect::ModifyExternalObject {
        return Err(CliError(
            "pyn8n must preserve the MODIFY_EXTERNAL_OBJECT fence".into(),
        ));
    }

    Ok(json!({
        "manifest_version": MANIFEST_VERSION,
        "valid": true,
        "repository_count": STRATEGIES.len(),
        "unique_repositories": names.len(),
        "invariants": [
            "one strategy per admitted repository",
            "mission + verifier + falsifier required",
            "dependency-only repositories never construct",
            "refused repositories carry typed refusals",
            "OSTAR simulation cannot become external truth",
            "chatman-nano-stack remains negative evidence",
            "external effects require exact authority and BRCE"
        ]
    }))
}

fn manifest_json() -> Value {
    json!({
        "manifest_version": MANIFEST_VERSION,
        "age_rule": {
            "created_before": AGE_CUTOFF,
            "basis": "admitted GitHub owner-inventory age sweep"
        },
        "observed_at": OBSERVED_AT,
        "repository_count": STRATEGIES.len(),
        "entries": STRATEGIES
            .iter()
            .copied()
            .map(|spec| evaluate(spec, None).to_json())
            .collect::<Vec<_>>(),
    })
}

fn plan_json(granted: Option<Authority>) -> Value {
    let decisions = plan(granted);
    let constructable = decisions
        .iter()
        .filter(|item| item.disposition == Disposition::Construct)
        .count();
    let verify_only = decisions
        .iter()
        .filter(|item| item.disposition == Disposition::VerifyOnly)
        .count();
    let reference_only = decisions
        .iter()
        .filter(|item| item.disposition == Disposition::ReferenceOnly)
        .count();
    let refused = decisions
        .iter()
        .filter(|item| item.disposition == Disposition::Refused)
        .count();
    let authority_refusals = decisions
        .iter()
        .filter(|item| item.do_standing == DoStanding::RefusedAuthority)
        .count();
    let broker_required = decisions
        .iter()
        .filter(|item| item.do_standing == DoStanding::BrceRequired)
        .count();

    json!({
        "manifest_version": MANIFEST_VERSION,
        "cutoff": AGE_CUTOFF,
        "granted_authority": granted.map(authority_name),
        "law": "planning never performs DO; exact external authority stops at BRCE_REQUIRED",
        "summary": {
            "constructable": constructable,
            "verify_only": verify_only,
            "reference_only": reference_only,
            "refused": refused,
            "authority_refusals": authority_refusals,
            "broker_required": broker_required,
        },
        "decisions": decisions
            .into_iter()
            .map(Decision::to_json)
            .collect::<Vec<_>>(),
    })
}

fn valid_git_sha(value: &str) -> bool {
    value.len() == 40 && value.chars().all(|character| character.is_ascii_hexdigit())
}

fn create_plan_receipt(git_sha: &str, granted: Option<Authority>) -> CliResult<Receipt> {
    if !valid_git_sha(git_sha) {
        return Err(Box::new(CliError(format!(
            "receipt requires an exact 40-hex Git subject, got `{git_sha}`"
        ))));
    }
    validate_manifest()?;

    let decisions = plan(granted);
    let authority_refusals = decisions
        .iter()
        .filter(|decision| decision.do_standing == DoStanding::RefusedAuthority)
        .count();
    let broker_required = decisions
        .iter()
        .filter(|decision| decision.do_standing == DoStanding::BrceRequired)
        .count();

    let mut receipt = Receipt {
        id: ReceiptId::parse("receipt:old-estate-revops-dfcm-v1")?,
        subject: format!("repository:chatman-ecosystem@{git_sha}"),
        actor: "ecosystem-cli/old-estate-revops".into(),
        authority: Authority::Draft,
        intention: "Compile an old-estate DfCM RevOps plan without external DO".into(),
        observed: vec![
            format!("manifest={MANIFEST_VERSION}"),
            format!("created_before={AGE_CUTOFF}"),
            format!("repositories={}", STRATEGIES.len()),
            format!(
                "requested_exact_authority={}",
                granted.map_or("none", authority_name)
            ),
        ],
        executed: vec![
            "SELECT classified repository strategy roles".into(),
            "CONSTRUCT ranked reversible candidate edges".into(),
            "DO not executed; external consequences remain broker-gated".into(),
        ],
        changed: Vec::new(),
        verified: vec![
            "manifest invariants valid".into(),
            format!("authority_refusals={authority_refusals}"),
            format!("broker_required={broker_required}"),
            "dependency-only and refused repositories excluded from construction".into(),
        ],
        excluded: vec![
            "LinkedIn message sending".into(),
            "CRM or other external object mutation".into(),
            "upstream dependency rewrites".into(),
            "quota-only repository churn".into(),
            "simulation promoted to observed commercial truth".into(),
        ],
        replay: vec![format!(
            "cargo run -p ecosystem-cli --bin old-estate-revops -- receipt {git_sha} {}",
            granted.map_or("none", authority_name)
        )],
        standing_before: Standing::Observed,
        standing_after: Standing::Candidate,
        timestamp: OBSERVED_AT.into(),
        digest: String::new(),
    };
    receipt.sign()?;
    receipt.verify()?;
    Ok(receipt)
}

fn print_json(value: &Value) -> CliResult<()> {
    println!("{}", serde_json::to_string_pretty(value)?);
    Ok(())
}

fn optional_authority(value: Option<&String>) -> Result<Option<Authority>, CliError> {
    match value.map(String::as_str) {
        None | Some("none") => Ok(None),
        Some(raw) => parse_authority(raw).map(Some),
    }
}

fn usage() -> &'static str {
    "old-estate-revops commands:\n  list\n  check\n  plan [none|EXACT_AUTHORITY]\n  repo REPOSITORY [none|EXACT_AUTHORITY]\n  receipt EXACT_40_HEX_GIT_SHA [none|EXACT_AUTHORITY]\n\nExternal authority never actuates here; admitted external effects return BRCE_REQUIRED."
}

fn run() -> CliResult<()> {
    let arguments = env::args().skip(1).collect::<Vec<_>>();
    let Some(command) = arguments.first().map(String::as_str) else {
        println!("{}", usage());
        return Ok(());
    };

    match command {
        "list" => print_json(&manifest_json()),
        "check" => print_json(&validate_manifest()?),
        "plan" => print_json(&plan_json(optional_authority(arguments.get(1))?)),
        "repo" => {
            let repository = arguments
                .get(1)
                .ok_or_else(|| CliError("repo command requires a repository name".into()))?;
            let granted = optional_authority(arguments.get(2))?;
            print_json(&evaluate(find_strategy(repository)?, granted).to_json())
        }
        "receipt" => {
            let git_sha = arguments
                .get(1)
                .ok_or_else(|| CliError("receipt requires an exact Git SHA".into()))?;
            let granted = optional_authority(arguments.get(2))?;
            print_json(&serde_json::to_value(create_plan_receipt(git_sha, granted)?)?)
        }
        "help" | "--help" | "-h" => {
            println!("{}", usage());
            Ok(())
        }
        other => Err(Box::new(CliError(format!(
            "unknown command `{other}`\n{}",
            usage()
        )))),
    }
}

fn main() -> CliResult<()> {
    run()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn manifest_has_expected_repository_count() {
        assert_eq!(STRATEGIES.len(), EXPECTED_REPOSITORIES);
    }

    #[test]
    fn manifest_invariants_are_closed() -> Result<(), CliError> {
        assert_eq!(validate_manifest()?["valid"], true);
        Ok(())
    }

    #[test]
    fn dependency_only_repositories_never_construct() {
        for spec in STRATEGIES
            .iter()
            .copied()
            .filter(|spec| spec.class == StrategyClass::DependencyOnly)
        {
            assert_eq!(disposition(spec), Disposition::ReferenceOnly);
            assert_eq!(dfcm_score(spec), 0);
            assert_eq!(spec.effect, ExternalEffect::None);
        }
    }

    #[test]
    fn refused_false_friends_never_construct() {
        for spec in STRATEGIES
            .iter()
            .copied()
            .filter(|spec| spec.class == StrategyClass::Refused)
        {
            assert_eq!(disposition(spec), Disposition::Refused);
            assert_eq!(dfcm_score(spec), 0);
            assert_eq!(
                spec.refusal,
                Some("REFUSED:NO_ADMITTED_REVOPS_SUBJECT")
            );
        }
    }

    #[test]
    fn ostar_cannot_actuate_external_outcomes() -> Result<(), CliError> {
        let strategy = find_strategy("ostar")?;
        assert_eq!(strategy.mode, ExecutionMode::SimulateOnly);
        assert_eq!(strategy.effect, ExternalEffect::None);
        assert_eq!(
            do_standing(strategy, Some(Authority::Communicate)),
            DoStanding::NotApplicable
        );
        Ok(())
    }

    #[test]
    fn nano_stack_is_negative_evidence() -> Result<(), CliError> {
        let strategy = find_strategy("chatman-nano-stack")?;
        assert_eq!(strategy.class, StrategyClass::NegativeEvidence);
        assert_eq!(disposition(strategy), Disposition::VerifyOnly);
        Ok(())
    }

    #[test]
    fn communication_refuses_without_exact_authority() -> Result<(), CliError> {
        for repository in ["bcinr", "yawl"] {
            let strategy = find_strategy(repository)?;
            assert_eq!(do_standing(strategy, None), DoStanding::RefusedAuthority);
            assert_eq!(
                do_standing(strategy, Some(Authority::Draft)),
                DoStanding::RefusedAuthority
            );
        }
        Ok(())
    }

    #[test]
    fn communication_authority_stops_at_brce() -> Result<(), CliError> {
        for repository in ["bcinr", "yawl"] {
            let strategy = find_strategy(repository)?;
            assert_eq!(
                do_standing(strategy, Some(Authority::Communicate)),
                DoStanding::BrceRequired
            );
        }
        Ok(())
    }

    #[test]
    fn exact_authority_is_not_hierarchical() -> Result<(), CliError> {
        let strategy = find_strategy("pyn8n")?;
        assert_eq!(
            do_standing(strategy, Some(Authority::Communicate)),
            DoStanding::RefusedAuthority
        );
        assert_eq!(
            do_standing(strategy, Some(Authority::ModifyExternalObject)),
            DoStanding::BrceRequired
        );
        Ok(())
    }

    #[test]
    fn plan_is_deterministic() {
        assert_eq!(plan_json(None), plan_json(None));
    }

    #[test]
    fn all_active_strategies_have_positive_scores() {
        for spec in STRATEGIES
            .iter()
            .copied()
            .filter(|spec| spec.class.is_active())
        {
            assert!(dfcm_score(spec) > 0);
        }
    }

    #[test]
    fn repository_lookup_accepts_full_name() -> Result<(), CliError> {
        assert_eq!(
            find_strategy("seanchatmangpt/ggen")?.repository,
            find_strategy("ggen")?.repository
        );
        Ok(())
    }

    #[test]
    fn exact_subject_receipt_rejects_non_sha() {
        assert!(create_plan_receipt("main", None).is_err());
    }

    #[test]
    fn exact_subject_receipt_is_signed_and_replayable() -> CliResult<()> {
        let sha = "9355418943e772bdc46f11055ce5e43efd70455d";
        let receipt = create_plan_receipt(sha, None)?;
        assert!(receipt.digest.starts_with("blake3:"));
        assert!(receipt.subject.ends_with(sha));
        receipt.verify()?;
        Ok(())
    }
}
