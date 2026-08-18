# Support and Escalation

Last updated: 2026-08-18

This document is the honest counterpart, for support/on-call, to what
`docs/SCOPE-AND-LIMITATIONS.md` already does for platform capability claims: it states plainly
what happens today if this platform breaks, who is contacted, how fast, and what is
*not yet* in place -- rather than leaving that gap implicit the way `docs/DISASTER-RECOVERY.md`
did. That document (`docs/DISASTER-RECOVERY.md`) covers the *technical* recovery steps an
engineer runs once someone is already working the incident; this document covers the layer in
front of that: who gets paged, how fast, and what happens if they don't answer -- the piece a
vendor-management, procurement, or production-scheduling reviewer would actually need to file.

## 1. The honest baseline: what support model actually exists today

**This is a single-person, best-effort support model, not a staffed on-call rotation.** There is
one maintainer (`Sean Chatman`, `xpointsh@gmail.com` -- the sole author of every commit in this
repository's `git log`, verified by re-running `git log --format='%an <%ae>' | sort -u` against
this repo). There is no second engineer, no shift schedule, no paging vendor (PagerDuty,
Opsgenie, VictorOps, or equivalent) wired to any alert in this stack today, and no formal
contractual response-time commitment to any customer or production team. `docs/
DISASTER-RECOVERY.md`'s own "Still Open" / unaddressed-gaps framing already names "no
paging/on-call integration" as a real, current gap -- this document does not paper over that; it
states the actual chain that exists in its place, and names the specific gap items still open at
the bottom (Section 5).

Read every response-time figure in Section 2 as an **internal target this one maintainer aims
for**, not an SLA. Consistent with `docs/SCOPE-AND-LIMITATIONS.md` Section 4's existing "no real
customer-facing SLA" disclosure: an SLA is a contractual promise backed by credits or penalties;
nothing here is that. If a production window (a Sony production window or otherwise) requires a
contractual, staffed, multi-person on-call commitment with penalty-backed response times, that
does not exist on this platform today and procurement should not represent it as such.

## 2. Severity tiers

Three tiers, plain-English definitions, and the internal response-time target the maintainer
aims for once notified. "Response" means acknowledgment and active triage has started -- not
that the issue is resolved by that time.

| Tier | Plain-English definition | Example on this platform | Target response (internal, not contractual) |
|------|---------------------------|---------------------------|-----------------------------------------------|
| **Sev1 -- Critical** | The platform (or a production-critical project on it) is down or unusable for everyone, with no workaround. Data loss is occurring or imminent. | The single `kind-platform-eng-colima` control-plane node is unreachable (the exact failure mode `docs/DISASTER-RECOVERY.md` Section 1 already documents happening once); the `platform-console` Istio Gateway returns 5xx for every route; a project's Postgres Pod is `CrashLoopBackOff` with no recent backup. | Best-effort, target under 2 hours during the maintainer's normal working hours; **no guaranteed after-hours or weekend response** -- see Section 1. |
| **Sev2 -- Degraded** | A specific module or one project is broken or badly degraded, but the rest of the platform and other projects are unaffected; a workaround may exist. | One project's managed Redis/queue addon is unreachable while the project's core database and API are fine; `/observability` dashboards are stale but the underlying workloads are healthy; a single `/api/*` route errors while the console itself loads. | Best-effort, target under 1 business day. |
| **Sev3 -- Minor / cosmetic** | Confusing UI copy, a non-blocking bug, a documentation gap, a feature request. Nothing is down. | A stat tile shows a slightly stale value between polling intervals; a doc (like this one, before it existed) is missing; a nice-to-have module doesn't exist yet. | Best-effort, target under 1 week, often batched with other work. |

These targets are the maintainer's own stated aim, calibrated against this repo's actual
commit cadence (`git log`, this repository) -- they are not measured against a formal incident
tracker today (see Section 5, gap 3), so they cannot yet be reported as an actually-achieved
percentage the way `/status`'s uptime is a real computed Prometheus figure
(`docs/SCOPE-AND-LIMITATIONS.md` Section 4).

## 3. Escalation chain

There is exactly one tier today -- naming it plainly rather than describing an escalation
structure that does not exist:

1. **First and only contact**: Sean Chatman, `xpointsh@gmail.com` -- the sole maintainer and
   sole committer to this repository. All severities, all hours, route here first.
2. **If unresponsive**: there is no second engineer or backup on-call to escalate to on this
   platform today. This is the concrete shape of the "single team" gap named in Section 1 --
   stated here rather than implying a chain that doesn't exist. A production team that needs a
   guaranteed secondary responder should treat that as an unmet requirement, not something to
   assume is covered.
3. **Vendor/infrastructure escalation** (not this maintainer, but relevant to name): the
   underlying cluster (`kind` on `colima`) and its dependencies (Istio, Flux, kube-prometheus-
   stack, the Supabase-operator-style CRDs) are all open-source components with no paid support
   contract behind this deployment. There is no vendor ticket to open if the maintainer is
   unreachable -- `docs/DISASTER-RECOVERY.md` Section 5's runbook is written so that any engineer
   with cluster access (not only the original maintainer) could, in principle, execute the
   recovery steps from the documented commands alone.

## 4. Stakeholder communication during an incident

There is currently no dedicated incident-communication template or channel in this repository
-- naming this as an open gap, not implying one exists. In practice, communication today is:

- **`/status`** (`docs/SCOPE-AND-LIMITATIONS.md` Section 4, `app/app/status/page.tsx`): the one
  real, live artifact a stakeholder can check without contacting the maintainer directly -- a
  genuinely computed uptime percentage from live Prometheus data, not a static page. It reports
  current state; it does not push notifications and it is not itself an incident-communication
  channel.
- **Direct contact** with the maintainer (Section 3) for anything beyond what `/status` shows.
- **Post-incident**: written up as a real, dated section in `docs/DISASTER-RECOVERY.md`
  (Section 1 documents the 2026-08-17 incident this way) rather than a separate incident report
  -- this repo's existing convention is one running document, not a report per incident. There
  is no templated stakeholder-facing incident summary (subject/impact/timeline/resolution
  format) yet; see Section 5, gap 3.

## 5. Known gaps -- stated plainly, not deferred

Matching this repo's existing disclosure discipline (`docs/SCOPE-AND-LIMITATIONS.md`,
`docs/DISASTER-RECOVERY.md`'s own unaddressed-items framing), the gaps this document does
**not** close:

1. **No paging/on-call integration.** No PagerDuty/Opsgenie/VictorOps or equivalent is wired to
   any alert (Prometheus Alertmanager rules, Istio Gateway health, or otherwise) in this stack.
   An outage is discovered by the maintainer noticing, or by a stakeholder reporting it via
   Section 3 -- not by an automated page. This is the same gap `docs/DISASTER-RECOVERY.md`
   already names as unaddressed; this document does not resolve it, only states it precisely.
2. **No second responder.** Section 3 above states this plainly: one person, no backup.
3. **No formal incident-communication template or tracker.** Section 4 above states this
   plainly: no subject/impact/timeline/resolution template exists yet, and incidents are
   recorded as prose in `docs/DISASTER-RECOVERY.md` rather than in a structured, per-incident
   log.
4. **No contractual SLA.** Section 1 and Section 2 both state this: every response-time figure
   here is an internal target, not a penalty-backed commitment.

## See Also

- `docs/DISASTER-RECOVERY.md` -- the technical recovery runbook this document's escalation
  chain feeds into once an incident is being actively worked
- `docs/SCOPE-AND-LIMITATIONS.md` -- the same honest-disclosure discipline applied to platform
  capability claims rather than support/on-call claims
- `README.md` -- module table, including `/status` (Section 4 above)
