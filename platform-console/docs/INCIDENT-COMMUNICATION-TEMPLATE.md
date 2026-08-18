# Incident Communication Template

Last updated: 2026-08-18

This document is deliberately **not** `docs/DISASTER-RECOVERY.md`. That runbook is written for
an engineer, in engineer language, to actually bring the cluster back -- `kubectl`, `etcd`,
namespace `creationTimestamp`s, Istio/Flux/Helm restand order. It should never be forwarded to
leadership or a customer as-is: it exposes internal implementation detail, assumes Kubernetes
literacy, and is organized around recovery steps, not around what a non-technical reader
actually needs to know (what broke, who's affected, when will it be fixed).

This document is the translation layer: a fill-in-the-blank template for the three messages an
incident actually needs -- **initial notification**, **ongoing update**, **resolution notice**
-- written so a non-technical executive or customer can read it without needing to know what
etcd, `kubectl`, or a `ConfigMap` are. Use this template during an incident; use
`docs/DISASTER-RECOVERY.md` to actually fix it. They are cross-linked, not merged, because the
audiences and the content each needs are genuinely different -- collapsing them back into one
document is the exact gap this template exists to close.

**Who fills this in**: whoever is running the incident (on this platform, today, that's the
person with `owner` role -- the same `requireRole(session, "owner")` boundary that gates
`/disaster-recovery`, `/org`, and `/audit`; see `lib/authz.ts`). This document is a template to
copy and fill in by hand for now -- it is not wired into an API route or a UI page. See
"Honest scope" at the end for exactly what that does and doesn't mean.

## Rules for filling this in

1. **No internal tooling names.** Never write `kubectl`, `etcd`, `ConfigMap`, `namespace`,
   `Deployment`, `bbolt`, a pod name, or a cluster name in a message that goes to leadership or
   a customer. If the technical cause needs to be referenced, describe it in plain language
   ("a data-storage failure on the machine our platform runs on") and link the DR runbook for
   anyone who needs the real detail.
2. **State what's impacted, not what's broken.** "Customers cannot create new projects" is
   useful to a leadership chain or a customer. "The Supabase operator's reconcile loop is
   failing" is not -- translate every technical symptom into a user-facing consequence before
   it goes in this template.
3. **Give a real ETA or say plainly that there isn't one yet.** "We expect to have an update
   within 30 minutes" or "We do not yet have a reliable time estimate; the next update will say
   why" -- never leave the ETA line blank or vague ("soon").
4. **Every update after the first must say what changed since the last one.** Repeating the
   same status with a new timestamp is worse than no update.
5. **The resolution notice must state what was and was not recovered**, in plain language, if
   anything was lost. This platform's own `docs/DISASTER-RECOVERY.md` section 3 draws this
   distinction honestly (infrastructure recovered byte-for-byte; a database's actual rows were
   not, because no backup existed at the time) -- carry that same honesty into the customer-
   facing version instead of implying full continuity that didn't happen.

## Template 1: Initial notification

Send as soon as impact is confirmed -- do not wait for a root cause.

```
Subject: [Incident] <one-line plain-language description of what's not working>

We are currently experiencing an issue affecting: <specific feature/product surface,
in the customer's own vocabulary -- e.g. "creating new projects" or "database backups",
never a technical component name>.

What this means for you: <concrete, observable impact -- e.g. "you will not be able to
create a new project until this is resolved" or "existing projects and their data are
not affected">.

When this started: <timestamp, in the reader's timezone if known, otherwise UTC and say so>.

What we know so far: <one or two sentences, plain language, no internal tool/component
names -- if the cause is not yet known, say "we are actively investigating" rather than
guessing>.

Next update: <specific time or interval -- e.g. "within 30 minutes" or "by 3:00 PM
Pacific">.

If you have questions in the meantime: <contact -- name/channel, not "the engineering
team">.
```

## Template 2: Ongoing update

Send at the cadence promised in the prior message, whether or not there's material progress.

```
Subject: [Incident Update <N>] <same one-line description as the initial notification>

Status: <one of: investigating / identified / fix in progress / monitoring>.

What's changed since the last update: <specific -- e.g. "we have identified the cause and
are applying a fix" or "the fix is applied and we are monitoring to confirm the issue does
not recur" -- never repeat the prior update verbatim>.

Current impact: <restate current impact even if unchanged, so a reader who only sees this
message has the full picture -- e.g. "creating new projects is still unavailable; existing
projects continue to be unaffected">.

Revised ETA: <update the estimate given in the previous message, or explicitly confirm it
still holds, or explicitly say it no longer holds and why>.

Next update: <specific time or interval>.
```

## Template 3: Resolution notice

Send once the issue is confirmed fixed by a real check, not once a fix has merely been applied
-- see rule 6 of `docs/DISASTER-RECOVERY.md`'s own runbook ("re-verify, don't assume").

```
Subject: [Resolved] <same one-line description as the initial notification>

This issue is resolved as of <timestamp>.

What happened, in plain terms: <one paragraph, no internal tool/component names -- describe
the failure and the fix the way you'd explain it to someone outside engineering>.

Duration: <start time> to <resolution time> (<total duration>).

What was affected: <restate, same language as the initial notification>.

What was and was not recovered: <if any data or state was permanently lost, say so plainly
here -- do not imply full continuity if it did not happen; if everything was fully
recovered, say that plainly too>.

What we're doing to prevent this from happening again: <concrete, specific -- e.g. "we have
added automated backups for X, which did not exist before this incident" -- not "we are
reviewing our processes">.

Full technical detail, for anyone who wants it: see `docs/DISASTER-RECOVERY.md` (internal /
engineering audience only -- do not forward the runbook itself externally).
```

## Worked example: the 2026-08-17 etcd-corruption incident

The following is `docs/DISASTER-RECOVERY.md`'s real, already-documented incident (section 1:
"The incident (real, cited)"), translated into this template's three messages. Nothing here is
invented -- every fact traces to a line in the runbook, cited inline; the only new content is
the plain-language rewording and the placeholders the runbook has no equivalent for (an ETA
promise, a "who to contact" line), which are marked as such rather than presented as real.

### Initial notification (as it would have read)

```
Subject: [Incident] Platform unavailable -- all projects and services affected

We are currently experiencing an issue affecting: the entire platform -- all projects,
databases, and the console itself.

What this means for you: nothing on the platform is currently reachable. This includes
the console, all project databases, and all project services.

When this started: 2026-08-18, approximately 01:11 UTC (best available estimate; see
"what we know so far").

What we know so far: the machine our platform runs on suffered a data-storage failure
that our monitoring could not recover from automatically. We are rebuilding the platform
from scratch; this will bring back all infrastructure and configuration, but any data
written since the last backup may not be recoverable -- we will confirm exactly what is
and is not affected once the rebuild is complete.

Next update: within 30 minutes. [Illustrative cadence -- not a value recorded in
DISASTER-RECOVERY.md, which has no comms-timing record for the real incident.]

If you have questions in the meantime: [platform on-call contact -- illustrative
placeholder; this repo does not record who was actually notified during the real
incident].
```

### Ongoing update (as it would have read, ~15 minutes in)

Grounded in `docs/DISASTER-RECOVERY.md` section 2's real, cited restand order and the real
elapsed time it documents (cluster bootstrap to `platform-console` namespace: 11 minutes 26
seconds).

```
Subject: [Incident Update 1] Platform unavailable -- all projects and services affected

Status: fix in progress.

What's changed since the last update: we have rebuilt the underlying platform
infrastructure (identity, security, and monitoring layers) and re-provisioned the
database layer. We are now redeploying the console application itself.

Current impact: the platform remains unavailable. No action is needed from you.

Revised ETA: we expect the platform to be reachable again within the next 15-20 minutes.

Next update: as soon as the platform is reachable again, or within 30 minutes, whichever
is sooner.
```

### Resolution notice (as it would have read)

Grounded directly in `docs/DISASTER-RECOVERY.md` sections 1, 2, and 3 (the LOST-vs-RECOVERED
table) -- the duration, the plain-language cause, and the honest "what was/wasn't recovered"
line are all real, cited facts from that document; nothing here is invented.

```
Subject: [Resolved] Platform unavailable -- all projects and services affected

This issue is resolved as of 2026-08-18, approximately 01:23 UTC.

What happened, in plain terms: the machine running our platform experienced an
unrecoverable data-storage failure in a core system component. There was no way to
repair it in place, so we rebuilt the platform from our own configuration files on a
fresh machine.

Duration: approximately 01:11 UTC to 01:23 UTC (about 11-12 minutes of full platform
unavailability, plus additional time afterward to redeploy the console application
itself).

What was affected: the entire platform -- all projects, databases, and the console.

What was and was not recovered: all platform infrastructure, security rules, and
configuration were fully recovered -- this part of our system is rebuilt from files we
keep under version control, independent of any single machine. However, one demo
project's database did not have a backup at the time of this incident, and the data in
that specific database (not customer production data -- see note below) could not be
recovered; it was re-created empty. No other project's data was affected.

[Note: DISASTER-RECOVERY.md documents this incident as affecting `demo-project`, a
non-production demo database on this platform, not a real customer's data. This
resolution notice is written in the general form a customer-facing notice would take;
the specific "what was lost" paragraph should be rewritten per-incident to name only
what was actually affected in that incident.]

What we're doing to prevent this from happening again: we have since built a real
database backup and restore capability (`/projects/[name]/backups`), which did not exist
at the time of this incident -- see `docs/DISASTER-RECOVERY.md` section 3 for the exact
timeline showing this gap and when it was closed. We have also live-tested the recovery
path itself (`docs/DISASTER-RECOVERY.md` section 4: a real resource was deleted,
confirmed broken, and recovered from a real backup) rather than assuming it works.

Full technical detail, for anyone who wants it: see `docs/DISASTER-RECOVERY.md` (internal
/ engineering audience only -- do not forward the runbook itself externally).
```

## Honest scope

This template is a **document**, not a wired-up feature -- there is no `/incident-comms` page,
no API route, and no evidence-bundle-verified "this template was actually used to send a real
message" proof, unlike most of this platform's other modules (see `docs/SCOPE-AND-LIMITATIONS.md`
for that same distinction applied elsewhere). Filling it in and sending it is a manual step for
whoever is running an incident. The gap this closes is narrower and real: previously there was
no separate, pre-approved, non-technical template at all -- only `docs/DISASTER-RECOVERY.md`'s
engineer-facing runbook, or whatever prose an engineer wrote from scratch in the moment. This
document exists so that translation happens once, in advance, reviewable by leadership before an
incident, rather than ad hoc during one.

## See also

- `docs/DISASTER-RECOVERY.md` -- the technical runbook this template translates from. Read it
  for the actual recovery mechanics; do not forward it externally.
- `docs/SCOPE-AND-LIMITATIONS.md` -- the platform's own honest-disclosure convention this
  document's "Honest scope" section follows.
- `evidence/control-evidence-bundle.json` -- control `incident-communication-template-exists`
  records this document's addition.
