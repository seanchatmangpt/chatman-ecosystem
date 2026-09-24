#!/bin/sh
W=/private/tmp/claude-501/-Users-sac/1fecd79a-9323-4b57-a949-d7892a3ea283/scratchpad/r2w
G=/Users/sac/wt/v26922/v26923/lanes/r2/gates; C=/Users/sac/wt/v26922/v26923/lanes/r2/candidates
cd $W/gi || exit 9
echo "## pwd=$(pwd) head=$(git rev-parse HEAD) start=$(date -u +%FT%TZ)"
sh $G/r2-gi-probe-isolation.sh . > $W/gi-probe-base.log 2>&1; echo "BASE probe rc=$? $(date -u +%T)"
git apply $C/r2-gi-probe-isolation.patch || exit 8
sh $G/r2-gi-probe-isolation.sh . > $W/gi-probe-cand.log 2>&1; echo "CAND probe rc=$? $(date -u +%T)"
git apply $C/r2-gi-bloom.patch || exit 7
sh $G/r2-gi-bloom.sh . > $W/gi-bloom-cand.log 2>&1; echo "CAND bloom rc=$? $(date -u +%T)"
F=test/ggen_igniter_semantic_jira_bootstrap_test.exs; cp $F $W/bloom-cand.exs
grep -v -e '"core.commitGraph", "false"' -e '"maintenance.auto", "false"' -e '"gc.auto", "0"' $W/bloom-cand.exs > $F
echo "mutant removed lines: $(diff $W/bloom-cand.exs $F | grep -c '^<')"
PATH=/Users/sac/.asdf/installs/elixir/1.18.4-otp-27/bin:/Users/sac/.asdf/installs/erlang/27.2.4/bin:$PATH mix test $F > $W/gi-bloom-mutant.log 2>&1; echo "MUTANT(no fixture pin) mix test rc=$? $(grep -E '[0-9]+ tests, [0-9]+ failure' $W/gi-bloom-mutant.log | tail -1) $(date -u +%T)"
cp $W/bloom-cand.exs $F
