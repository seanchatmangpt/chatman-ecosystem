#!/usr/bin/env bash
set -euo pipefail
ttl="${1:-ontology/edge-retirement.ttl}"
grep -q 'ce:RetiredEdgeShape' "$ttl"
grep -q 'sh:pattern "^[0-9a-f]{40}$"' "$ttl"
grep -q 'sh:hasValue ce:machineOwner' "$ttl"
grep -q 'sh:hasValue "NONE"' "$ttl"
grep -q 'ce:replayDigest' "$ttl"
grep -q 'ce:consequence' "$ttl"
printf 'edge-retirement: PASS\n'
