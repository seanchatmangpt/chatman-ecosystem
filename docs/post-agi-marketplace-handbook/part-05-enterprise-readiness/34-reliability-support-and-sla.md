# 34. Reliability, Support, and SLA

## A promise is an architectural input

An SLA is not the sentence “99.9% uptime.” It is a commercial interface binding a measurable service indicator, threshold, window, exclusions, support process, consequence, and often service-credit policy.

```text
SLA = Promise(SLI, Threshold, Window, Consequence)
```

Once sold, the promise constrains architecture and operations for the term of the agreement.

## SLI before percentage

Useful indicators can include API availability, successful fulfillment, entitlement propagation, metering acceptance, support response, restore success, or other customer-visible behavior. The indicator definition must state measurement point and exclusions.

A platform can have healthy Kubernetes nodes while customers cannot activate purchased subscriptions. Technical uptime alone is not commercial reliability.

## SLO and error budget

SLOs provide the operational target and error budget. They should be set from real architecture and customer need, then monitored continuously. A plan cannot truthfully promise a stronger SLA than the system can measure and sustain.

Different plans can project different commercial consequences while sharing the same underlying indicators.

## Support is a state machine

Support tiers should define:

```text
severity classification
response target
communication cadence
escalation path
coverage hours
restoration target if promised
customer obligations
closure criteria
```

Response time is not resolution time. A support dashboard that conflates them will eventually generate false SLA claims.

## RTO, RPO, and disaster recovery

Recovery promises must be exercised. A document describing a restore path is `CANDIDATE`; a successful exact restore of the relevant product version and data class supplies execution evidence.

RTO and RPO can differ across vendor-hosted SaaS and customer-hosted deployment classes. Keep those differences in plan/deployment policy rather than vague documentation.

## Service credits

If SLA breaches create credits, credit calculation becomes a financial DO. The input should be receipted SLI evidence and the effective agreement. The resulting credit/refund requires exact authority and reconciliation.

## Marketplace outages

A marketplace can be unavailable while the running product remains healthy. Decide which capabilities degrade: new purchase, entitlement refresh, metering, private-offer creation, or settlement import. Existing customer access may continue under bounded cached entitlement policy if the commercial contract permits it.

## Refusals

- `REFUSED:SLA_STRONGER_THAN_MEASURABLE_ARCHITECTURE`
- `REFUSED:INFRA_UPTIME_AS_CUSTOMER_AVAILABILITY`
- `REFUSED:RESPONSE_TIME_AS_RESOLUTION_TIME`
- `REFUSED:DR_DOCUMENT_AS_RESTORE_EXECUTION`
- `REFUSED:SERVICE_CREDIT_WITHOUT_AUTHORITY`

## Operational exercise

Take a premium plan and derive the exact SLI, SLO, SLA, support, failover, backup/restore, incident, service-credit, and evidence machinery required to sell it. Then repeat for a customer-hosted plan and make responsibility differences explicit.
