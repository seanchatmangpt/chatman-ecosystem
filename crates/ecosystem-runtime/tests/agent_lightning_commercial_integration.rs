use ecosystem_core::Authority;
use ecosystem_runtime::agent_lightning_commercial_plane::{
    BudgetPolicy, CommercialControlPlane, DeploymentFeature, DeploymentPolicy, DeploymentTarget,
    MarketplaceBinding, PlaneError, RateCard,
};
use ecosystem_runtime::agent_lightning_service::{
    Grant, JobRequest, Meter, Mode, Policy, Workload,
};
use ecosystem_runtime::commerce::{CommerceLedger, Provider, ProviderEventKind};
use std::collections::{BTreeMap, BTreeSet};

fn binding() -> MarketplaceBinding {
    MarketplaceBinding {
        provider: Provider::Aws,
        seller: "seller:chatman".into(),
        buyer: "buyer:aws".into(),
        product: "product:agent-lightning-managed".into(),
        sku: "sku:enterprise".into(),
        offer: "offer:managed-rl".into(),
        order: "order:aws".into(),
        agreement: "agreement:aws".into(),
        subscription: "subscription:aws".into(),
        entitlement: "entitlement:aws".into(),
        fulfillment: "fulfillment:aws".into(),
        provider_buyer_ref: "aws-buyer".into(),
        provider_product_ref: "aws-product".into(),
        provider_agreement_ref: "aws-agreement".into(),
        provider_entitlement_ref: "aws-agreement".into(),
        provider_subscription_ref: "aws-agreement".into(),
        dimension: "agent-lightning-charge-micro-usd".into(),
        currency: "USD".into(),
    }
}

fn grant(organization: &str) -> Grant {
    Grant {
        organization: organization.into(),
        plan: "enterprise".into(),
        modes: BTreeSet::from([Mode::Hosted]),
        quota: BTreeMap::from([
            (Meter::GpuSeconds, 3_600),
            (Meter::InputTokens, 100_000),
            (Meter::OutputTokens, 20_000),
            (Meter::Rollouts, 1),
        ]),
    }
}

fn request(organization: &str) -> JobRequest {
    JobRequest {
        id: "job-budget-boundary".into(),
        organization: organization.into(),
        workload: Workload::pinned(),
        mode: Mode::Hosted,
        requested: BTreeMap::from([
            (Meter::GpuSeconds, 3_600),
            (Meter::InputTokens, 100_000),
            (Meter::OutputTokens, 20_000),
            (Meter::Rollouts, 1),
        ]),
        idempotency_key: "idem-budget-boundary".into(),
    }
}

fn target() -> DeploymentTarget {
    DeploymentTarget {
        provider: Provider::Aws,
        mode: Mode::Hosted,
        region: "us-east-1".into(),
        zones: 3,
        replicas: 3,
        rpo_seconds: 60,
        rto_seconds: 300,
        features: BTreeSet::from([
            DeploymentFeature::PrivateNetwork,
            DeploymentFeature::DurableReceiptSink,
        ]),
    }
}

#[tokio::test]
async fn replay_survives_saturated_budget_and_revocation_fails_closed() -> Result<(), PlaneError> {
    let binding = binding();
    let mut commerce = CommerceLedger::new(binding.context())?;
    commerce.observe(&binding.observation(
        ProviderEventKind::Agreement,
        "agreement-event",
        0,
        0,
    ))?;
    commerce.observe(&binding.observation(
        ProviderEventKind::Entitlement,
        "entitlement-event",
        0,
        0,
    ))?;
    let fulfillment = commerce.authorize_fulfillment("integration-fulfillment")?;

    let rate_card = RateCard::new(
        "USD",
        BTreeMap::from([
            (Meter::GpuSeconds, 1_000),
            (Meter::InputTokens, 2),
            (Meter::OutputTokens, 8),
            (Meter::Rollouts, 50_000),
        ]),
    )?;
    let exact_job_cost = 4_010_000;
    let mut plane = CommercialControlPlane::new(
        Policy::agent_lightning(),
        DeploymentPolicy::enterprise_default(),
        rate_card,
        BudgetPolicy {
            maximum_job_micros: exact_job_cost,
            maximum_period_micros: exact_job_cost,
        },
        binding,
        "2026-08-19T00:00:00Z",
    )?;

    let organization = "organization:aws-customer";
    let subject = "service-account:aws";
    let key_one = format!("blake3:{}", "1".repeat(64));
    let key_two = format!("blake3:{}", "2".repeat(64));
    plane.bind_entitlement(
        grant(organization),
        &fulfillment,
        Authority::PersistControlPlane,
    )?;
    plane.register_key(
        organization,
        subject,
        "key-1",
        &key_one,
        Authority::PersistControlPlane,
    )?;
    plane.rotate_key(
        organization,
        subject,
        "key-2",
        &key_two,
        Authority::PersistControlPlane,
    )?;

    let request = request(organization);
    let first = plane.admit_run(
        organization,
        subject,
        &key_two,
        &request,
        &target(),
        Authority::PersistControlPlane,
    )?;
    assert_eq!(first.quote.total_micros, exact_job_cost);

    // Replay must not reserve budget a second time. A fresh job would be refused at this boundary.
    let replay = plane.admit_run(
        organization,
        subject,
        &key_two,
        &request,
        &target(),
        Authority::PersistControlPlane,
    )?;
    assert_eq!(replay.reservation.id, first.reservation.id);
    assert_eq!(replay.receipt_digest, first.receipt_digest);

    plane.revoke_identity(organization, subject, Authority::PersistControlPlane)?;
    assert!(plane.authenticate(organization, subject, &key_two).is_err());
    assert!(
        plane
            .authorize_run(
                &first.reservation.id,
                organization,
                subject,
                &key_two,
                Authority::ModifyExternalObject,
            )
            .is_err()
    );
    assert!(plane.replay_verify()? >= 4);
    Ok(())
}
