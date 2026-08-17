# Appendix K — CLI/API/MCP/A2A Projection Matrix

| Semantic concern | CLI | API | MCP | A2A |
|---|---|---|---|---|
| Capability identity | command id | operation/resource id | tool/resource id | capability id |
| Input schema | args/flags | request schema | tool schema | task/message schema |
| Exact subject | explicit flag or file | typed field | typed field | delegated subject |
| Refusal | exit/status + typed body | typed error | typed tool result/error | typed task refusal |
| Authority | request only | request only | intent only | delegated scope |
| DO | BRCE | BRCE | BRCE | BRCE |
| Receipt | machine-readable output | response/reference | tool result/reference | returned evidence chain |
| Replay | command + subject capsule | request capsule | intent capsule | delegation + evidence capsule |

The exact protocol syntax may evolve. Semantic correspondence is the invariant.