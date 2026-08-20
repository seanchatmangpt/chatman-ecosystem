//! Evidence-bounded DfCM scheduler for the older RevOps-capable repository estate.
//!
//! This executable is intentionally a planner, not an actuator. It classifies
//! repository roles, ranks reversible construction opportunities, emits typed
//! refusals, and can seal an exact-subject planning receipt with the ecosystem's
//! canonical BLAKE3 receipt implementation. External consequences remain behind
//! their exact authority and BRCE boundaries.

use ecosystem_core::{Authority, Receipt, ReceiptId, Standing};
use serde_json::{Value, json};
use std::cmp::Ordering;
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

    const fn is_constructable(self) -> bool {
        matches!(self, Self::Direct | Self::Composable)
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
    independent_edges: u8,
    ecosystem_leverage: u8,
    verifier_availability: u8,
    construction_cost: u8,
    irreversibility: u8,
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
            "required_authority": self.spec.effect.required_authority().map(authority_name),
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

const STRATEGIES: &[StrategySpec] = &[
    StrategySpec {
        repository: "ggen",
        class: StrategyClass::Direct,
        role: "manufacturing_compiler",
        mode: ExecutionMode::Construct,
        effect: ExternalEffect::None,
        mission: "Manufacture campaign, CRM, workflow, conformance, and receipt projections from admitted semantic authority; never own outreach DO.",
        verifier: "ggen sync/receipt/replay plus graph-to-generated-surface conformance",
        falsifier: "generated surface diverges from admitted graph or receipt replay",
        dependencies: &["unrdf", "open-ontologies"],
        independent_edges: 10,
        ecosystem_leverage: 10,
        verifier_availability: 9,
        construction_cost: 4,
        irreversibility: 1,
        refusal: None,
    },
    StrategySpec {
        repository: "open-ontologies",
        class: StrategyClass::Direct,
        role: "admission_receipt_court",
        mode: ExecutionMode::Construct,
        effect: ExternalEffect::None,
        mission: "Independently admit requirements, work orders, mutations, and emitted RevOps artifacts; bind every admitted consequence to replayable evidence.",
        verifier: "external receipt verifier plus recursive admission gates",
        falsifier: "gate bypass, cross-tenant leakage, broken chain, or unverifiable receipt",
        dependencies: &["ggen"],
        independent_edges: 9,
        ecosystem_leverage: 10,
        verifier_availability: 9,
        construction_cost: 4,
        irreversibility: 1,
        refusal: None,
    },
    StrategySpec {
        repository: "unrdf",
        class: StrategyClass::Direct,
        role: "semantic_operational_graph",
        mode: ExecutionMode::Construct,
        effect: ExternalEffect::None,
        mission: "Own the queryable Person/Organization/Problem/Opportunity/Campaign/Interaction graph and its SHACL/SPARQL constraints.",
        verifier: "SHACL validation, SPARQL assertions, deterministic graph replay",
        falsifier: "constraint violation, non-deterministic projection, or graph provenance loss",
        dependencies: &["open-ontologies"],
        independent_edges: 9,
        ecosystem_leverage: 10,
        verifier_availability: 8,
        construction_cost: 4,
        irreversibility: 1,
        refusal: None,
    },
    StrategySpec {
        repository: "ostar",
        class: StrategyClass::Direct,
        role: "simulation_proof_laboratory",
        mode: ExecutionMode::SimulateOnly,
        effect: ExternalEffect::None,
        mission: "Simulate and prove admitted revenue-process mechanics before any external connector is granted DO authority.",
        verifier: "RevOps proof gates, OCEL conformance, and receipt-chain verification",
        falsifier: "a simulated lead, message, deal, contract, or revenue event is represented as an observed external outcome",
        dependencies: &["pm4py", "open-ontologies"],
        independent_edges: 8,
        ecosystem_leverage: 9,
        verifier_availability: 8,
        construction_cost: 4,
        irreversibility: 1,
        refusal: None,
    },
    StrategySpec {
        repository: "chatmangpt",
        class: StrategyClass::Direct,
        role: "legacy_revops_execution_lab",
        mode: ExecutionMode::Construct,
        effect: ExternalEffect::None,
        mission: "Recover and requalify historical CRM agents, ICP qualification, outreach-sequence semantics, deal progression, and contract-closure telemetry against current exact-head boundaries.",
        verifier: "current-head BusinessOS/OSA CRM integration tests plus semantic-convention validation",
        falsifier: "historical commit evidence is promoted without current exact-head execution",
        dependencies: &["unrdf", "ostar"],
        independent_edges: 8,
        ecosystem_leverage: 9,
        verifier_availability: 7,
        construction_cost: 5,
        irreversibility: 2,
        refusal: None,
    },
    StrategySpec {
        repository: "bcinr",
        class: StrategyClass::Direct,
        role: "publication_lifecycle",
        mode: ExecutionMode::Construct,
        effect: ExternalEffect::Communicate,
        mission: "Compile topic -> draft -> review -> publication-intent -> external-DO -> receipt -> published as a mechanically admitted cross-channel lifecycle.",
        verifier: "publication state requires an external connector receipt, not a file marker",
        falsifier: "PUBLISHED standing is reached without a platform consequence receipt",
        dependencies: &["linkedin-public-canon", "open-ontologies"],
        independent_edges: 7,
        ecosystem_leverage: 9,
        verifier_availability: 9,
        construction_cost: 3,
        irreversibility: 5,
        refusal: None,
    },
    StrategySpec {
        repository: "yawl",
        class: StrategyClass::Direct,
        role: "champion_discovery_workflow",
        mode: ExecutionMode::Construct,
        effect: ExternalEffect::Communicate,
        mission: "Run admitted champion/path discovery, ranking, strategy construction, and OCEL workflow evidence while fencing outreach consequence behind exact communication authority.",
        verifier: "YAWL workflow conformance plus OCEL export and bridge evidence",
        falsifier: "conceptual LinkedIn/Outreach bridge is treated as a live connector or a generated outreach plan is treated as a sent message",
        dependencies: &["unrdf", "pm4py"],
        independent_edges: 7,
        ecosystem_leverage: 8,
        verifier_availability: 7,
        construction_cost: 4,
        irreversibility: 5,
        refusal: None,
    },
    StrategySpec {
        repository: "clap-noun-verb",
        class: StrategyClass::Composable,
        role: "typed_revops_control_surface",
        mode: ExecutionMode::Construct,
        effect: ExternalEffect::None,
        mission: "Expose typed noun-verb commands for campaign, lead, account, opportunity, POV, pipeline, receipt, and attribution operations without owning domain truth.",
        verifier: "command-dispatch tests plus structured consequence and capability standing checks",
        falsifier: "CLI command silently invents business truth or bypasses its owning capability",
        dependencies: &["unrdf", "open-ontologies"],
        independent_edges: 6,
        ecosystem_leverage: 8,
        verifier_availability: 9,
        construction_cost: 3,
        irreversibility: 1,
        refusal: None,
    },
    StrategySpec {
        repository: "pyn8n",
        class: StrategyClass::Composable,
        role: "integration_fabric",
        mode: ExecutionMode::Construct,
        effect: ExternalEffect::ModifyExternalObject,
        mission: "Execute admitted cross-system workflow handoffs, retries, and connector choreography; qualification and message authority remain external inputs.",
        verifier: "workflow integration tests, execution logs, retry/failure evidence",
        falsifier: "workflow self-authorizes qualification, CRM mutation, or outreach from generated intent alone",
        dependencies: &["Arazzo-Specification", "open-ontologies"],
        independent_edges: 6,
        ecosystem_leverage: 8,
        verifier_availability: 7,
        construction_cost: 4,
        irreversibility: 6,
        refusal: None,
    },
    StrategySpec {
        repository: "knhk",
        class: StrategyClass::Composable,
        role: "brokered_execution_evidence",
        mode: ExecutionMode::Construct,
        effect: ExternalEffect::None,
        mission: "Supply authority, broker, receipt, replay, timing, and negative-control primitives while keeping historical commercial narratives subordinate to current evidence.",
        verifier: "current exact-head component validation plus broker/receipt/replay checks",
        falsifier: "archived business claim outranks current executable evidence or SELECT/CONSTRUCT is collapsed into DO",
        dependencies: &["open-ontologies"],
        independent_edges: 7,
        ecosystem_leverage: 9,
        verifier_availability: 6,
        construction_cost: 5,
        irreversibility: 2,
        refusal: None,
    },
    StrategySpec {
        repository: "chatman-nano-stack",
        class: StrategyClass::NegativeEvidence,
        role: "adversarial_false_claim_corpus",
        mode: ExecutionMode::ObserveOnly,
        effect: ExternalEffect::None,
        mission: "Preserve historical fictional LinkedIn/job/outreach simulations as falsifiers proving generated narrative is not an external consequence.",
        verifier: "negative controls reject simulation->application, generated-outreach->sent-message, simulated-revenue->observed-revenue promotion",
        falsifier: "any archived fictional event is accepted as a real platform, employment, or revenue event",
        dependencies: &[],
        independent_edges: 5,
        ecosystem_leverage: 8,
        verifier_availability: 10,
        construction_cost: 2,
        irreversibility: 1,
        refusal: None,
    },
    StrategySpec {
        repository: "Arazzo-Specification",
        class: StrategyClass::DependencyOnly,
        role: "portable_api_workflow_contract",
        mode: ExecutionMode::DependencyOnly,
        effect: ExternalEffect::None,
        mission: "Reference the portable API workflow contract; keep Chatman-specific RevOps doctrine outside the upstream-shaped specification repository.",
        verifier: "Arazzo conformance in consuming projections",
        falsifier: "Chatman-specific campaign semantics are injected into the generic specification repository",
        dependencies: &[],
        independent_edges: 0,
        ecosystem_leverage: 7,
        verifier_availability: 8,
        construction_cost: 1,
        irreversibility: 1,
        refusal: None,
    },
    StrategySpec {
        repository: "pm4py",
        class: StrategyClass::DependencyOnly,
        role: "process_mining_oracle",
        mode: ExecutionMode::DependencyOnly,
        effect: ExternalEffect::None,
        mission: "Remain an external process-mining oracle for discovery and conformance rather than a container for Chatman sales doctrine.",
        verifier: "consume PM4Py outputs as comparative process evidence",
        falsifier: "upstream process-mining source is modified solely to encode Chatman GTM policy",
        dependencies: &[],
        independent_edges: 0,
        ecosystem_leverage: 8,
        verifier_availability: 9,
        construction_cost: 1,
        irreversibility: 1,
        refusal: None,
    },
    StrategySpec {
        repository: "ash_state_machine",
        class: StrategyClass::DependencyOnly,
        role: "state_machine_primitive",
        mode: ExecutionMode::DependencyOnly,
        effect: ExternalEffect::None,
        mission: "Provide reusable resource lifecycle semantics to a RevOps application without becoming LinkedIn-specific.",
        verifier: "consumer state-transition tests",
        falsifier: "campaign doctrine is embedded into the generic state-machine library",
        dependencies: &[],
        independent_edges: 0,
        ecosystem_leverage: 6,
        verifier_availability: 8,
        construction_cost: 1,
        irreversibility: 1,
        refusal: None,
    },
    StrategySpec {
        repository: "ash_paper_trail",
        class: StrategyClass::DependencyOnly,
        role: "resource_audit_primitive",
        mode: ExecutionMode::DependencyOnly,
        effect: ExternalEffect::None,
        mission: "Provide resource-change audit history to the consuming RevOps application.",
        verifier: "consumer mutation-audit tests",
        falsifier: "generic audit library is rewritten around one GTM program",
        dependencies: &[],
        independent_edges: 0,
        ecosystem_leverage: 6,
        verifier_availability: 8,
        construction_cost: 1,
        irreversibility: 1,
        refusal: None,
    },
    StrategySpec {
        repository: "ash_cloak",
        class: StrategyClass::DependencyOnly,
        role: "sensitive_field_protection",
        mode: ExecutionMode::DependencyOnly,
        effect: ExternalEffect::None,
        mission: "Protect sensitive prospect and customer attributes in consuming applications without owning their business semantics.",
        verifier: "consumer encryption/decryption and key-boundary tests",
        falsifier: "PII is copied into an unprotected RevOps projection",
        dependencies: &[],
        independent_edges: 0,
        ecosystem_leverage: 7,
        verifier_availability: 8,
        construction_cost: 1,
        irreversibility: 1,
        refusal: None,
    },
    StrategySpec {
        repository: "ash_events",
        class: StrategyClass::DependencyOnly,
        role: "event_replay_primitive",
        mode: ExecutionMode::DependencyOnly,
        effect: ExternalEffect::None,
        mission: "Provide actor-attributed event persistence and replay for interaction lineage in a consuming RevOps system.",
        verifier: "consumer event-log replay equality",
        falsifier: "event history cannot reconstruct admitted resource state",
        dependencies: &[],
        independent_edges: 0,
        ecosystem_leverage: 7,
        verifier_availability: 8,
        construction_cost: 1,
        irreversibility: 1,
        refusal: None,
    },
    StrategySpec {
        repository: "ash_oban",
        class: StrategyClass::DependencyOnly,
        role: "background_work_primitive",
        mode: ExecutionMode::DependencyOnly,
        effect: ExternalEffect::None,
        mission: "Provide condition-triggered background execution for already-admitted follow-up work.",
        verifier: "consumer scheduling and idempotency tests",
        falsifier: "background scheduling is confused with authority to perform the external consequence",
        dependencies: &[],
        independent_edges: 0,
        ecosystem_leverage: 6,
        verifier_availability: 8,
        construction_cost: 1,
        irreversibility: 1,
        refusal: None,
    },
    StrategySpec {
        repository: "ash_double_entry",
        class: StrategyClass::DependencyOnly,
        role: "accounting_primitive",
        mode: ExecutionMode::DependencyOnly,
        effect: ExternalEffect::None,
        mission: "Provide double-entry accounting primitives for booked monetary consequences, never inferred engagement value.",
        verifier: "consumer balance and transfer invariants",
        falsifier: "engagement or pipeline probability is recorded as realized revenue",
        dependencies: &[],
        independent_edges: 0,
        ecosystem_leverage: 7,
        verifier_availability: 8,
        construction_cost: 1,
        irreversibility: 1,
        refusal: None,
    },
    StrategySpec {
        repository: "twitter",
        class: StrategyClass::Refused,
        role: "name_only_false_friend",
        mode: ExecutionMode::Refused,
        effect: ExternalEffect::None,
        mission: "Refuse social-distribution standing: observed repository identity is an Ash example application, not an admitted social-network connector.",
        verifier: "repository-purpose inspection",
        falsifier: "repository name alone is used as evidence of a social distribution capability",
        dependencies: &[],
        independent_edges: 0,
        ecosystem_leverage: 0,
        verifier_availability: 10,
        construction_cost: 1,
        irreversibility: 1,
        refusal: Some("REFUSED:NO_ADMITTED_REVOPS_SUBJECT"),
    },
    StrategySpec {
        repository: "chiefofstaffgpt",
        class: StrategyClass::Refused,
        role: "name_only_false_friend",
        mode: ExecutionMode::Refused,
        effect: ExternalEffect::None,
        mission: "Refuse chief-of-staff standing from naming alone: observed repository material is a Celery-on-Render example.",
        verifier: "repository-purpose inspection",
        falsifier: "repository name is promoted into an agent capability without implementation evidence",
        dependencies: &[],
        independent_edges: 0,
        ecosystem_leverage: 0,
        verifier_availability: 10,
        construction_cost: 1,
        irreversibility: 1,
        refusal: Some("REFUSED:NO_ADMITTED_REVOPS_SUBJECT"),
    },
    StrategySpec {
        repository: "pro-landing",
        class: StrategyClass::Refused,
        role: "generic_template",
        mode: ExecutionMode::Refused,
        effect: ExternalEffect::None,
        mission: "Refuse GTM-product standing from a generic Nuxt landing-page starter; it may be referenced as a UI pattern only.",
        verifier: "repository-purpose inspection",
        falsifier: "generic template presence is counted as a production acquisition surface",
        dependencies: &[],
        independent_edges: 0,
        ecosystem_leverage: 0,
        verifier_availability: 10,
        construction_cost: 1,
        irreversibility: 1,
        refusal: Some("REFUSED:NO_ADMITTED_REVOPS_SUBJECT"),
    },
    StrategySpec {
        repository: "helpdesk",
        class: StrategyClass::Refused,
        role: "generic_template",
        mode: ExecutionMode::Refused,
        effect: ExternalEffect::None,
        mission: "Refuse customer-success standing from Phoenix boilerplate until a real helpdesk capability is admitted and verified.",
        verifier: "repository-purpose inspection",
        falsifier: "framework starter is represented as an operational customer-success system",
        dependencies: &[],
        independent_edges: 0,
        ecosystem_leverage: 0,
        verifier_availability: 10,
        construction_cost: 1,
        irreversibility: 1,
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
    if !matches!(
        spec.class,
        StrategyClass::Direct | StrategyClass::Composable | StrategyClass::NegativeEvidence
    ) {
        return 0;
    }
    let reversibility = 11_u64.saturating_sub(u64::from(spec.irreversibility.min(10)));
    let cost = u64::from(spec.construction_cost.max(1));
    u64::from(spec.independent_edges)
        * u64::from(spec.ecosystem_leverage)
        * u64::from(spec.verifier_availability)
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

fn manifest_json() -> Value {
    let entries = STRATEGIES
        .iter()
        .copied()
        .map(|spec| evaluate(spec, None).to_json())
        .collect::<Vec<_>>();
    json!({
        "manifest_version": MANIFEST_VERSION,
        "age_rule": {
            "created_before": AGE_CUTOFF,
            "basis": "GitHub owner-inventory age classification from the admitted old-estate sweep"
        },
        "observed_at": OBSERVED_AT,
        "repository_count": entries.len(),
        "entries": entries,
    })
}

fn plan_json(granted: Option<Authority>) -> Value {
    let decisions = plan(granted);
    let constructable = decisions
        .iter()
        .filter(|item| item.spec.class.is_constructable())
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
        "law": "SELECT/CONSTRUCT planning never performs DO; exact external authority only advances an intent to BRCE_REQUIRED",
        "summary": {
            "constructable": constructable,
            "verify_only": verify_only,
            "reference_only": reference_only,
            "refused": refused,
            "authority_refusals": authority_refusals,
            "broker_required": broker_required,
        },
        "decisions": decisions.into_iter().map(Decision::to_json).collect::<Vec<_>>(),
    })
}

fn repository_tail(value: &str) -> &str {
    match value.rsplit('/').next() {
        Some(tail) => tail,
        None => value,
    }
}

fn find_strategy(repository: &str) -> Result<StrategySpec, CliError> {
    let wanted = repository_tail(repository);
    STRATEGIES
        .iter()
        .copied()
        .find(|spec| spec.repository == wanted)
        .ok_or_else(|| CliError(format!("repository `{repository}` is not in {MANIFEST_VERSION}")))
}

fn validate_manifest() -> Result<Value, CliError> {
    if STRATEGIES.len() != EXPECTED_REPOSITORIES {
        return Err(CliError(format!(
            "manifest has {} repositories; expected {EXPECTED_REPOSITORIES}",
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
                "non-refused repository `{}` carries a refusal code",
                spec.repository
            )));
        }
        if spec.class == StrategyClass::DependencyOnly
            && (spec.mode != ExecutionMode::DependencyOnly || spec.effect != ExternalEffect::None)
        {
            return Err(CliError(format!(
                "dependency-only repository `{}` crosses its construction/effect fence",
                spec.repository
            )));
        }
        if spec.class == StrategyClass::Refused
            && (spec.mode != ExecutionMode::Refused || spec.effect != ExternalEffect::None)
        {
            return Err(CliError(format!(
                "refused repository `{}` crosses its refusal fence",
                spec.repository
            )));
        }
    }

    let ostar = find_strategy("ostar")?;
    if ostar.mode != ExecutionMode::SimulateOnly || ostar.effect != ExternalEffect::None {
        return Err(CliError(
            "ostar must remain SIMULATE_ONLY with no external consequence".into(),
        ));
    }
    let nano = find_strategy("chatman-nano-stack")?;
    if nano.class != StrategyClass::NegativeEvidence || nano.mode != ExecutionMode::ObserveOnly {
        return Err(CliError(
            "chatman-nano-stack must remain negative evidence / observe-only".into(),
        ));
    }
    for repository in ["bcinr", "yawl"] {
        let strategy = find_strategy(repository)?;
        if strategy.effect != ExternalEffect::Communicate {
            return Err(CliError(format!(
                "{repository} must preserve the COMMUNICATE authority fence"
            )));
        }
    }
    let pyn8n = find_strategy("pyn8n")?;
    if pyn8n.effect != ExternalEffect::ModifyExternalObject {
        return Err(CliError(
            "pyn8n must preserve the MODIFY_EXTERNAL_OBJECT authority fence".into(),
        ));
    }

    Ok(json!({
        "manifest_version": MANIFEST_VERSION,
        "valid": true,
        "repository_count": STRATEGIES.len(),
        "unique_repositories": names.len(),
        "invariants": [
            "one strategy per admitted repository",
            "every strategy has mission + verifier + falsifier",
            "dependency-only repositories never enter construction",
            "refused repositories carry typed refusals",
            "OSTAR simulation cannot become external outcome truth",
            "chatman-nano-stack remains negative evidence",
            "BCINR and YAWL COMMUNICATE effects require exact authority and BRCE",
            "pyn8n external mutation requires exact MODIFY_EXTERNAL_OBJECT authority and BRCE"
        ]
    }))
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
    let plan = plan(granted);
    let authority_refusals = plan
        .iter()
        .filter(|decision| decision.do_standing == DoStanding::RefusedAuthority)
        .count();
    let broker_required = plan
        .iter()
        .filter(|decision| decision.do_standing == DoStanding::BrceRequired)
        .count();
    let mut receipt = Receipt {
        id: ReceiptId::parse("receipt:old-estate-revops-dfcm-v1")?,
        subject: format!("repository:chatman-ecosystem@{git_sha}"),
        actor: "ecosystem-cli/old-estate-revops".into(),
        authority: Authority::Draft,
        intention: "Compile the older repository estate into a DfCM RevOps strategy plan without performing external DO".into(),
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
            "SELECT classified direct/composable/negative/dependency/refused roles".into(),
            "CONSTRUCT ranked reversible strategy candidates".into(),
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

fn usage() -> &'static str {
    "old-estate-revops commands:\n  list\n  check\n  plan [none|EXACT_AUTHORITY]\n  repo REPOSITORY [none|EXACT_AUTHORITY]\n  receipt EXACT_40_HEX_GIT_SHA [none|EXACT_AUTHORITY]\n\nExternal authority never actuates here; admitted external effects return BRCE_REQUIRED."
}

fn optional_authority(value: Option<&String>) -> Result<Option<Authority>, CliError> {
    match value.map(String::as_str) {
        None | Some("none") => Ok(None),
        Some(raw) => parse_authority(raw).map(Some),
    }
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
        "plan" => {
            let granted = optional_authority(arguments.get(1))?;
            print_json(&plan_json(granted))
        }
        "repo" => {
            let repository = arguments.get(1).ok_or_else(|| {
                CliError("repo command requires a repository name".into())
            })?;
            let granted = optional_authority(arguments.get(2))?;
            let decision = evaluate(find_strategy(repository)?, granted);
            print_json(&decision.to_json())
        }
        "receipt" => {
            let git_sha = arguments.get(1).ok_or_else(|| {
                CliError("receipt command requires an exact 40-hex Git SHA".into())
            })?;
            let granted = optional_authority(arguments.get(2))?;
            let receipt = create_plan_receipt(git_sha, granted)?;
            print_json(&serde_json::to_value(receipt)?)
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
        let result = validate_manifest()?;
        assert_eq!(result["valid"], true);
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
            assert_eq!(spec.refusal, Some("REFUSED:NO_ADMITTED_REVOPS_SUBJECT"));
        }
    }

    #[test]
    fn ostar_cannot_actuate_external_outcomes() -> Result<(), CliError> {
        let strategy = find_strategy("ostar")?;
        assert_eq!(strategy.mode, ExecutionMode::SimulateOnly);
        assert_eq!(strategy.effect, ExternalEffect::None);
        assert_eq!(do_standing(strategy, Some(Authority::Communicate)), DoStanding::NotApplicable);
        Ok(())
    }

    #[test]
    fn nano_stack_is_negative_evidence_not_constructable_work() -> Result<(), CliError> {
        let strategy = find_strategy("chatman-nano-stack")?;
        assert_eq!(strategy.class, StrategyClass::NegativeEvidence);
        assert_eq!(disposition(strategy), Disposition::VerifyOnly);
        Ok(())
    }

    #[test]
    fn communicate_effect_refuses_without_exact_authority() -> Result<(), CliError> {
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
    fn communicate_authority_only_advances_to_brce_required() -> Result<(), CliError> {
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
    fn exact_authority_does_not_form_a_hierarchy() -> Result<(), CliError> {
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
        let first = plan_json(None);
        let second = plan_json(None);
        assert_eq!(first, second);
    }

    #[test]
    fn all_active_strategies_have_positive_dfcm_scores() {
        for spec in STRATEGIES.iter().copied().filter(|spec| {
            matches!(
                spec.class,
                StrategyClass::Direct | StrategyClass::Composable | StrategyClass::NegativeEvidence
            )
        }) {
            assert!(dfcm_score(spec) > 0);
        }
    }

    #[test]
    fn repository_lookup_accepts_full_github_name() -> Result<(), CliError> {
        assert_eq!(
            find_strategy("seanchatmangpt/ggen")?.repository,
            find_strategy("ggen")?.repository
        );
        Ok(())
    }

    #[test]
    fn exact_subject_receipt_rejects_non_sha() {
        let result = create_plan_receipt("main", None);
        assert!(result.is_err());
    }

    #[test]
    fn exact_subject_receipt_is_signed_and_replayable() -> CliResult<()> {
        let sha = "9355418943e772bdc46f11055ce5e43efd70455d";
        let receipt = create_plan_receipt(sha, None)?;
        assert!(receipt.digest.starts_with("blake3:"));
        receipt.verify()?;
        assert!(receipt.subject.ends_with(sha));
        Ok(())
    }
}
