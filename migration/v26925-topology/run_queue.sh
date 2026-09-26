#!/bin/bash
# usage: run_queue.sh <cmd> <logname> <repo>... ; runs topology.py <cmd> --repo R serially (one writer per repo)
cmd=$1; shift; name=$1; shift
L=/private/tmp/claude-501/-Users-sac/90d06f90-3c25-4b15-bede-3d0e7e58ac78/scratchpad/v26925/lanes/topo/logs
for r in "$@"; do
  echo "=== $(date +%T) $cmd $r" >> $L/$name.log
  python3 /Users/sac/.claude/migration/v26925-topology/topology.py $cmd --repo "$r" ${EXTRA} >> $L/$name.log 2>&1
  echo "=== $(date +%T) exit $? $r" >> $L/$name.log
done
echo "QUEUE-DONE $name" >> $L/$name.log
