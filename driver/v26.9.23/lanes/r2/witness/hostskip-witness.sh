#!/bin/sh
W=/private/tmp/claude-501/-Users-sac/1fecd79a-9323-4b57-a949-d7892a3ea283/scratchpad/r2w
G=/Users/sac/wt/v26922/v26923/lanes/r2/gates; C=/Users/sac/wt/v26922/v26923/lanes/r2/candidates
cd $W/xaas || exit 9
echo "## pwd=$(pwd) head=$(git rev-parse HEAD) start=$(date -u +%FT%TZ)"
git apply -R $C/r2-x-hostskip.patch; sh $G/r2-x-hostskip.sh . > $W/x-hostskip-base2.log 2>&1; echo "BASE hostskip rc=$? $(date -u +%T)"
git apply $C/r2-x-hostskip.patch || exit 8
sh $G/r2-x-hostskip.sh . > $W/x-hostskip-cand2.log 2>&1; echo "CAND hostskip rc=$? $(date -u +%T)"
