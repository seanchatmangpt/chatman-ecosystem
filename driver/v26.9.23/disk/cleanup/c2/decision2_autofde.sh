#!/bin/zsh
# Decision 2 (cleanup-2, 2026-09-23): git worktree remove --force for autofde-lab wo05-170 and wo10,
# gated on: superproject clean + HEAD reachable from a durable ref; every initialized submodule clean,
# no stash, HEAD contained in one of its own remote refs after fetch --no-prune; no live process cwd;
# no content change in the last 12h. Snapshot ref under refs/preserve/v26.9.23/cleanup/<slug> first.
# Usage: decision2_autofde.sh [--dry-run]
set -u
REPO=/Users/sac/autofde-lab
OUT=/Users/sac/wt/v26922/v26923/disk/cleanup/c2
DRY=0; [[ "${1:-}" == "--dry-run" ]] && DRY=1
typeset -A SLUG
SLUG[/Users/sac/wt/v26922/autofde-lab/wo05-170]=autofde-lab-wo05-170
SLUG[/Users/sac/wt/v26922/autofde-lab/wo10]=autofde-lab-wo10
rc_all=0
for wt in /Users/sac/wt/v26922/autofde-lab/wo05-170 /Users/sac/wt/v26922/autofde-lab/wo10; do
  slug=${SLUG[$wt]}; n=${wt:t}; ad=$REPO/.git/worktrees/$n; fail=""
  echo "=== $wt slug=$slug $(date '+%FT%T%z')"
  [[ -d $wt ]] || { echo "ABSENT (already removed)"; continue; }
  # gate 1: live process cwd / argv
  if lsof -a -d cwd -Fn 2>/dev/null | grep -qE "^n${wt}(/|\$)"; then fail+=" live_cwd"; fi
  if ps -axo command | grep -v grep | grep -q -- "$wt"; then fail+=" live_argv"; fi
  # gate 2: no content change in the last 12h (worktree files; admin dir excluding index stat refreshes)
  cutoff=$(date -v-12H '+%Y-%m-%d %H:%M:%S')
  recent=$(find $wt -newermt "$cutoff" 2>/dev/null | head -3)
  [[ -n $recent ]] && fail+=" recent_change:$recent"
  last_reflog=$(git -C $wt reflog -1 --format=%ct HEAD)
  (( last_reflog > $(date -v-12H +%s) )) && fail+=" recent_reflog"
  # gate 3: superproject clean + HEAD durable
  head=$(git -C $wt rev-parse HEAD)
  [[ -n $(git -C $wt status --porcelain --ignore-submodules=none) ]] && fail+=" super_dirty"
  nonpyc=$(git -C $wt status --porcelain --ignored=matching --untracked-files=all | grep -v '__pycache__/$')
  [[ -n $nonpyc ]] && fail+=" super_nonpycache_ignored"
  durable=$(git -C $wt for-each-ref --contains $head --format='%(refname)' refs/heads refs/remotes refs/tags refs/preserve | head -1)
  [[ -z $durable ]] && fail+=" head_not_durable"
  echo "head=$head durable_example=$durable"
  # gate 4: submodules
  for s in $(git -C $wt submodule foreach --quiet --recursive 'echo $displaypath'); do
    sp=$wt/$s; sh=$(git -C $sp rev-parse HEAD)
    git -C $sp fetch --no-prune --tags origin >/dev/null 2>&1; frc=$?
    sdirty=$(git -C $sp status --porcelain --ignored | head -1)
    sstash=$(git -C $sp stash list | head -1)
    sremote=$(git -C $sp branch -r --contains $sh | head -1 | sed 's/^ *//')
    verdict=PASS
    [[ -n $sdirty ]] && verdict=FAIL_dirty
    [[ -n $sstash ]] && verdict=FAIL_stash
    [[ -z $sremote ]] && verdict=FAIL_not_on_remote
    echo "SUB $s head=$sh fetch_rc=$frc remote_contains=${sremote:-none} verdict=$verdict"
    [[ $verdict != PASS ]] && fail+=" sub:$s:$verdict"
  done
  if [[ -n $fail ]]; then echo "REFUSED:$fail"; rc_all=1; continue; fi
  # preserve snapshot (never touches the worktree or its index)
  tmpidx=$(mktemp)
  GIT_INDEX_FILE=$tmpidx git -C $wt read-tree HEAD
  GIT_INDEX_FILE=$tmpidx git -C $wt add -A
  tree=$(GIT_INDEX_FILE=$tmpidx git -C $wt write-tree)
  rm -f $tmpidx
  c=$(git -C $wt commit-tree $tree -p HEAD -m "preserve: $wt cleanup-2 2026-09-23")
  ref=refs/preserve/v26.9.23/cleanup/$slug
  existing=$(git -C $wt rev-parse -q --verify $ref)
  if [[ -n $existing ]]; then
    [[ $(git -C $wt rev-parse $existing^{tree}) == $tree ]] || { echo "REFUSED: $ref exists with a different tree"; rc_all=1; continue; }
    c=$existing
  else
    git -C $wt update-ref $ref $c "" || { echo "REFUSED: update-ref failed"; rc_all=1; continue; }
  fi
  echo "preserve_ref=$ref commit=$c tree=$tree head_tree=$(git -C $wt rev-parse HEAD^{tree})"
  # coverage proof: every tracked path's blob in $c equals the on-disk hash; no dirty/untracked paths exist
  mism=$(cd $wt && git ls-tree -r -z $c | python3 -c '
import sys,os,subprocess
ents=[e for e in sys.stdin.buffer.read().split(b"\0") if e]
reg=[];bad=[]
for e in ents:
    meta,path=e.split(b"\t",1); mode,typ,sha=meta.split()
    if typ!=b"blob": continue
    p=path.decode()
    if mode==b"120000":
        h=subprocess.run(["git","hash-object","--stdin"],input=os.readlink(p).encode(),capture_output=True).stdout.strip().decode() if os.path.islink(p) else "missing"
        if h!=sha.decode(): bad.append(p)
    else:
        reg.append((p,sha.decode()))
out=subprocess.run(["git","hash-object","--stdin-paths"],input="\n".join(p for p,_ in reg).encode(),capture_output=True).stdout.decode().split()
if len(out)!=len(reg): bad.append("HASH_COUNT_MISMATCH")
for (p,sha),h in zip(reg,out):
    if sha!=h: bad.append(p)
print(len(reg),"regular_checked",file=sys.stderr)
print("\n".join(bad[:5]))
')
  gl=$(git -C $wt ls-tree -r $c | awk '$2=="commit"{print $3" "$4}' | while read h p; do
         if [[ -e $wt/$p/.git ]]; then [[ $(git -C $wt/$p rev-parse HEAD) == $h ]] || echo "$p";
         else [[ -z $(ls -A $wt/$p 2>/dev/null) ]] || echo "uninit_nonempty:$p"; fi; done)
  keys=$(git -C $wt diff-tree -r --name-only HEAD $c | grep -E '(signing|\.key$)' | grep -v 'verifying\.key$')
  echo "coverage_blob_mismatch=[${mism}] gitlink_mismatch=[${gl}] private_keys=[${keys}]"
  if [[ -n $mism || -n $gl || -n $keys ]]; then echo "REFUSED: coverage"; rc_all=1; continue; fi
  if (( DRY )); then echo "DRY-RUN: would run git -C $REPO worktree remove --force $wt"; continue; fi
  git -C $REPO worktree remove --force $wt; rrc=$?
  echo "remove_rc=$rrc dir_exists=$([[ -e $wt ]] && echo yes || echo no) admin_exists=$([[ -e $ad ]] && echo yes || echo no)"
  echo "post: ref=$(git -C $REPO rev-parse $ref) branch=$(git -C $REPO rev-parse refs/heads/$(git -C $REPO for-each-ref --points-at $head --format='%(refname:short)' refs/heads | head -1) 2>/dev/null)"
  (( rrc == 0 )) || rc_all=1
done
exit $rc_all
