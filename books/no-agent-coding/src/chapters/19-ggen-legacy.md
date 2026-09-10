# 19. ggen-legacy and Reconstitution

**Executive thesis:** Legacy modernization should begin by recovering bounded semantics and authority, not by asking an agent to rewrite what the organization no longer understands.

## World-as-found first

Reconstitution observes the existing system as it actually behaves: files, APIs, runtime topology, schemas, docs, tests, public contracts, provenance, and contradictions. These observations are evidence, not automatically truth. The output can legitimately contain gaps.

## Authority vacuums are real

Some systems have rules with no surviving owner, conflicting documentation, or behavior that nobody can justify. The correct reconstitution result may be NO_AUTHORITY or UNKNOWN for part of the surface. Manufacturing a confident explanation would make the migration less trustworthy than the legacy system.

## Replacement after equivalence

Once enough bounded meaning is admitted, ggen can manufacture replacement projections and compare them against observed contracts. Retirement should depend on equivalence evidence at the relevant boundaries, not on visual similarity or a model’s explanation of the old code.

## Operating practice

Choose a bounded legacy slice with an observable consumer. Preserve the old subject, reconstitute its semantic contract, manufacture a candidate replacement, run both against independent witnesses, receipt the comparison, and retire only the portion whose equivalence has standing.

## Diagnostic question

Which legacy migration currently depends on confident interpretation where authority is actually missing?
