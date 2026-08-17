# Appendix F — OCEL 2.0 Process-State Patterns

## Release pattern

Objects:

- repository;
- commit;
- pull request;
- build artifact;
- release;
- receipt.

Events:

- observe source;
- admit candidate;
- validate;
- publish branch;
- open draft PR;
- exact-head verify;
- release;
- supersede.

## Deployment pattern

Objects:

- release artifact;
- environment;
- workload;
- policy;
- authority grant;
- receipt.

Events:

- construct deployment;
- admit DO;
- actuate;
- observe postcondition;
- verify standing;
- rollback or supersede.

## Process-state rule

Prefer deriving current state from admitted object-event relationships rather than maintaining an unrelated status field as a second semantic authority.

Caches and projections are allowed when their derivation is explicit.