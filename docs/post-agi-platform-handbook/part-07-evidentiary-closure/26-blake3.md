# 26. BLAKE3 and Content Identity

Content-addressed identity is foundational to replay and reconstitution because human-readable names are mutable.

BLAKE3 is useful in the ecosystem as a fast cryptographic hash for binding bytes to a digest.

\[
h = BLAKE3(content)
\]

If the content changes, the digest should change with overwhelming probability. That gives a stable identity for exact bytes.

## What a hash proves

A content digest supports integrity and identity claims about the bytes presented to the verifier. It does **not**, by itself, prove who created the content, whether the creator was authorized, or whether the content is semantically correct.

Origin requires an authenticated binding such as a trusted signature or another receipted authority relation.

This distinction is important enough to state as a non-collapse law:

\[
ContentIdentity \neq Provenance \neq Authority \neq Correctness
\]

## Binding construction inputs

A construction receipt can hash:

- semantic graphs or canonical serializations;
- templates;
- source archives;
- configuration;
- toolchain manifests;
- generated artifacts;
- validation reports.

The receipt then describes the relationships among those identities.

This allows later systems to ask whether an allegedly equivalent replay actually used the same source material.

## Receipt DAGs

When receipts refer to parent receipt digests, evidence forms a content-addressed DAG.

A deployment receipt may point to a build receipt, which points to source and ontology receipts. A class-closure receipt may point to several successful instance receipts and the equivalence proof that connects them.

The DAG is more informative than a flat audit log because causality and identity travel together.

## Tamper evidence versus secrecy

Hashing does not make content secret. It also does not prevent an attacker from creating a different document and hashing it.

The security property comes from checking the expected digest through an authenticated trust path.

Post-AGI systems should prefer precise cryptographic claims to magical language about hashes.

## Falsifier

Any architecture that treats possession of a BLAKE3 digest as proof of authorized origin is conflating content identity with authentication.

## Operational exercise

Draw the digest chain for one artifact from ontology and source through build, validation, deployment, and observed runtime state. Mark which edges are merely hash relationships and which are authenticated provenance or authority relationships.