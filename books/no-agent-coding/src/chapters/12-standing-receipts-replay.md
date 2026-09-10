# 12. Standing, Receipts, and Replay

**Executive thesis:** Software should make the strongest evidence-backed claim it has earned and no stronger.

## Presence is not standing

A file can exist without compiling. A binary can compile without executing. An API can return success without producing the intended consequence. A workflow definition can exist without ever running. No Agent Coding therefore uses standing states rather than a single Boolean notion of done.

## Receipts bind the claim

A receipt should bind exact subject identity, admitted authority, transformation or actuation, consequence, evidence, and replay information. Cryptographic digesting can make identities tamper-evident, but the digest does not by itself prove correctness. The receipt states what was observed and what claim ceiling that evidence supports.

## Replay converts history into institutional memory

Replay asks whether another operator can reconstruct the relevant standing without trusting the original session narrative. That requirement fights tribal knowledge, ephemeral agent context, and unverifiable “it worked on my machine” claims. Replay is not necessarily re-actuation; safe replay can verify evidence and deterministic manufacture without repeating a dangerous consequence.

## Operating practice

Use typed states such as UNKNOWN, PARTIAL_ALIVE, ALIVE, BLOCKED, BUILD_BROKEN, UNSUPPORTED, and typed REFUSED results. Promote only after the exact admitted subject crosses the boundary named by the claim. Keep the receipt small enough to verify and rich enough to reproduce.

## Diagnostic question

Could another operator replay the evidence behind your strongest production claim?
