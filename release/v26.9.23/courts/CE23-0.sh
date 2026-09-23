#!/bin/sh
# CE23-0 court: Re-establish root identity (release/v26.9.23/sjira/goal.ttl ce:CE23-0).
# Run from the chatman-ecosystem root by the CE23 root court. Exit 0 = ALIVE;
# exit 75 = machinery absent (standing UNKNOWN); any other exit = the court ran
# and witnessed nothing (standing UNKNOWN).
# Initial body (lane CE-INTAKE, wave CE0): the gate's machinery lands in a lane
# of the wave generated from the compiled CE23 orders
# (release/v26.9.23/sjira/compiled/*/orders.ttl), which replaces this body.
echo "UNKNOWN: CE23-0 machinery lands in a generated CE23 lane"
exit 75
