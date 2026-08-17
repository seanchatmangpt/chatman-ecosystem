# Appendix M — Capsule ALIVE Specification

A validation capsule is identified by the product:

\[
Source \times Validator \times ExecutionMode \times Toolchain \times Config
\]

## Required evidence

- exact source/artifact identity;
- validator identity and version;
- toolchain identity;
- relevant configuration;
- execution environment/mode;
- start/end timestamps or deterministic run identity;
- exit/result;
- machine-readable validation report;
- negative-fixture results where required;
- receipt digest.

## Reuse rule

`VERIFIER_ALIVE` can be reused only when the verifier's assumptions, toolchain, configuration, and environment identities are equivalent for the new execution.

`SUBJECT_ALIVE` must still be established for the new exact subject.