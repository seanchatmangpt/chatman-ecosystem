# 36. Legal and Commercial Architecture

## Terms create system constraints

Contracts can define data use, retention, deletion, service levels, support, audit, security, export restrictions, termination, confidentiality, and commercial pricing. Those terms can have direct architectural consequences.

The engineering system should represent **legally admitted facts** without pretending software can replace legal interpretation.

```text
Approved legal fact
  → explicit operational constraint
  → policy / configuration / evidence requirement
```

The arrow must be owned. An LLM does not infer a production-deletion policy from an ambiguous clause and then gain authority to execute it.

## Contract object model

Useful objects include:

```text
MasterAgreement
OrderForm
MarketplaceTerms
EULA
DataProcessingAgreement
SLA
AcceptableUsePolicy
SecurityAddendum
ExportRestriction
TerminationPolicy
```

Each has version, parties, effective interval, priority/override relationship where legally admitted, and source authority.

## Marketplace terms versus negotiated terms

Marketplace standard terms may coexist with seller terms and buyer-negotiated documents. A private offer can carry custom commercial or legal material. The system must know which admitted terms apply to a specific agreement instead of choosing whichever PDF is easiest to find.

`Agreement.terms_digest` should identify the effective approved term set, not merely the latest template.

## Executable boundaries

Some legal facts can be translated into precise policy:

- retention period;
- allowed processing regions;
- named support tier;
- data export availability;
- effective termination date;
- contract quantity;
- prohibited use classes when explicitly codified.

Other clauses require interpretation. Those remain external authority boundaries. The software can surface the question, gather relevant facts, and construct candidate actions, but it stops before irreversible consequence.

## Legal hold and deletion

Termination/cancellation is a clear example. Product access can end while data retention remains required. A legal hold can override ordinary deletion. Commercial state, access state, and data lifecycle therefore cannot be one boolean.

## Export and regional restrictions

Seller location, buyer location, deployment region, sanctioned/restricted parties, and product technology can create external legal requirements. Engineering should provide exact identity and topology facts and route decisions to the proper compliance/legal authority.

## Refusals

- `REFUSED:LLM_GENERATED_TERM_AS_APPROVED_CONTRACT`
- `REFUSED:AMBIGUOUS_LEGAL_TEXT_AS_AUTOMATIC_DO`
- `REFUSED:LATEST_TEMPLATE_AS_EFFECTIVE_AGREEMENT`
- `REFUSED:CANCELLATION_AS_IMMEDIATE_DELETE`
- `REFUSED:LEGAL_HOLD_IGNORED`

## Operational exercise

Select five approved contract obligations with operational effects—for example residency, retention, SLA, termination/export, and support. Define the exact machine fact each creates, its scope/effective time, the system policy that can enforce it, the evidence produced, and the point where legal interpretation remains outside software authority.
