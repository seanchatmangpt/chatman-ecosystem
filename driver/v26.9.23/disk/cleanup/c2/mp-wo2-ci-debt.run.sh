#!/usr/bin/env bash
# cleanup-2: preserve-then-remove /Users/sac/wt/v26922/mp-wo2-ci-debt (ggen-marketplace worktree,
# branch fix/ci-debt-26922). Plan: mp-wo2-ci-debt.plan.json. Decision 1 (driver): per-checkout ggen
# signing keys are ephemeral credentials; evidence = receipts + verifying.key.
# Never adds a private key to any commit; never rm -rf; never deletes a branch or ref.
set -euo pipefail
W=/Users/sac/wt/v26922/mp-wo2-ci-debt
GD=/Users/sac/ggen-marketplace/.git
C2=/Users/sac/wt/v26922/v26923/disk/cleanup/c2
REF=refs/preserve/v26.9.23/cleanup/mp-wo2-ci-debt
HEAD_EXPECT=46122984e0ecb8ca92feb89b7e68c16af24b0ec5
PACK=packs/xaas-public-ash-projection-pack
EVIDENCE=(.ggen-v2/receipt-log.jsonl .ggen-v2/receipt.json .ggen/keys/verifying.key
  $PACK/.ggen-v2/receipt-log.jsonl $PACK/.ggen-v2/receipt.json $PACK/.ggen/keys/verifying.key)
SIGNING=(.ggen/keys/signing.key $PACK/.ggen/keys/signing.key)
cd "$C2"
say() { printf '[%s] %s\n' "$(date '+%FT%T%z')" "$*"; }

say "== re-check immediately before acting"
[ "$(git -C "$W" rev-parse HEAD)" = "$HEAD_EXPECT" ] || { say "ABORT head moved"; exit 10; }
cwds=$(lsof -a -d cwd -Fn 2>/dev/null || true)
if printf '%s\n' "$cwds" | grep -F "$W" >/dev/null; then say "ABORT live process cwd"; exit 11; fi
argv=$(ps -axww -o pid=,command= || true)
hits=$(printf '%s\n' "$argv" | grep -F "$W" | grep -v -e 'grep' -e 'mp-wo2-ci-debt.run.sh' -e 'verify_mp-wo2' || true)
[ -z "$hits" ] || { say "ABORT live process argv: $hits"; exit 12; }
recent=$(find "$W" -newermt "$(date -v-12H '+%Y-%m-%d %H:%M:%S')" -not -path "$W" 2>/dev/null || true)
[ -z "$recent" ] || { say "ABORT change within 12h: $recent"; exit 13; }
[ -z "$(git -C "$W" status --porcelain -uall)" ] || { say "ABORT dirty/untracked appeared"; exit 14; }
ign=$(git -C "$W" ls-files -o -i --exclude-standard | sort)
want=$(printf '%s\n' "${EVIDENCE[@]}" "${SIGNING[@]}" \
  scripts/__pycache__/check_source_correspondence.cpython-311.pyc scripts/__pycache__/marketplace.cpython-311.pyc \
  scripts/__pycache__/marketplace_scope.cpython-311.pyc scripts/__pycache__/qualify_packs.cpython-311.pyc | sort)
[ "$ign" = "$want" ] || { say "ABORT ignored set changed"; diff <(echo "$want") <(echo "$ign") || true; exit 15; }
if git --git-dir="$GD" rev-parse -q --verify "$REF" >/dev/null; then say "ABORT $REF already exists"; exit 16; fi
say "re-check PASS: head=$HEAD_EXPECT, no cwd/argv, no mtime < 12h, porcelain empty, ignored set = plan"

say "== hash private signing keys (hash only)"
: > mp-wo2-ci-debt.signing-key-sha256.tsv
keylines=""
for k in "${SIGNING[@]}"; do
  h=$(shasum -a 256 "$W/$k" | awk '{print $1}')
  printf '%s\t%s\n' "$k" "$h" >> mp-wo2-ci-debt.signing-key-sha256.tsv
  keylines+="  $k sha256=$h"$'\n'
done
cat mp-wo2-ci-debt.signing-key-sha256.tsv

say "== snapshot without touching the worktree index"
tmpd=$(mktemp -d /private/tmp/claude-501/-Users-sac/1fecd79a-9323-4b57-a949-d7892a3ea283/scratchpad/c2-mpwo2.XXXXXX)
tmpidx=$tmpd/index
GIT_INDEX_FILE=$tmpidx git -C "$W" read-tree HEAD
GIT_INDEX_FILE=$tmpidx git -C "$W" add -A
GIT_INDEX_FILE=$tmpidx git -C "$W" add -f -- "${EVIDENCE[@]}"
staged=$(GIT_INDEX_FILE=$tmpidx git -C "$W" ls-files)
badkeys=$(printf '%s\n' "$staged" | grep -E '(signing|\.key$)' | grep -v 'verifying\.key$' || true)
[ -z "$badkeys" ] || { say "ABORT private key staged: $badkeys"; exit 20; }
tree=$(GIT_INDEX_FILE=$tmpidx git -C "$W" write-tree)
msgf=$tmpd/msg
{
  printf 'preserve: %s cleanup-2 2026-09-23\n\n' "$W"
  printf 'repo ggen-marketplace, branch fix/ci-debt-26922, parent %s\n' "$HEAD_EXPECT"
  printf 'Decision 1 (driver): per-checkout ggen signing keys are ephemeral credentials;\n'
  printf 'evidence = receipts + verifying.key.\n\n'
  printf 'Force-added ignored evidence:\n'
  printf '  %s\n' "${EVIDENCE[@]}"
  printf '\nPrivate signing keys NOT preserved (sha256 of file bytes; key never committed):\n'
  printf '%s' "$keylines"
  printf '\nLeft as removal blockers (regenerable): scripts/__pycache__/*.cpython-311.pyc (4)\n'
  printf 'All 7 ggen.sync signatures verify as Ed25519(ascii chain_hash_hex) with the preserved verifying.key.\n'
} > "$msgf"
c=$(git -C "$W" commit-tree "$tree" -p HEAD -F "$msgf")
git -C "$W" update-ref -m "cleanup-2 preserve mp-wo2-ci-debt" "$REF" "$c" ""
say "preserve commit $c tree $tree -> $REF"

say "== coverage proof (blob hash per evidence path)"
: > mp-wo2-ci-debt.evidence.tsv
for p in "${EVIDENCE[@]}"; do
  b=$(git -C "$W" rev-parse "$c:$p"); f=$(git -C "$W" hash-object -- "$W/$p"); s=$(shasum -a 256 "$W/$p" | awk '{print $1}')
  [ "$b" = "$f" ] || { say "ABORT blob mismatch $p"; exit 30; }
  printf '%s\t%s\t%s\n' "$p" "$b" "$s" >> mp-wo2-ci-debt.evidence.tsv
  say "covered $p blob=$b"
done
git -C "$W" diff-tree -r --no-renames --name-status HEAD "$c"

say "== verify pre + anti-vacuity"
python3 verify_mp-wo2-ci-debt.py --phase pre
for m in blob sig keyhash; do
  if python3 verify_mp-wo2-ci-debt.py --phase pre --mutate $m > "mp-wo2-ci-debt.mutate-$m.out" 2>&1; then
    say "ABORT anti-vacuity: mutate=$m passed"; exit 40; fi
  say "anti-vacuity mutate=$m -> refused ($(grep -c '^FAIL' "mp-wo2-ci-debt.mutate-$m.out") FAIL lines)"
done

say "== remove"
du -sk "$W" | awk '{print "du_kib_before", $1}'
git --git-dir="$GD" worktree remove --force "$W"
say "worktree removed"

say "== verify post"
python3 verify_mp-wo2-ci-debt.py --phase post
say "DONE preserve=$c"
