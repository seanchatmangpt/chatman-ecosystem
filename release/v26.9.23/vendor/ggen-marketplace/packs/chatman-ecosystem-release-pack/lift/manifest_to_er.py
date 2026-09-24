#!/usr/bin/env python3
"""Lift a committed release manifest (TOML) into er:LegacyRelease Turtle.

Handwritten residue, UNSUPPORTED(generator-capability): ggen renders RDF into
text, it does not parse TOML into RDF, and no marketplace pack does (see
../HANDWRITTEN.md). Output is lifted observation only: er:LegacyRelease and
er:LegacyComponent, never er:Release/er:Component, so gates 010-060 never
re-judge frozen facts. Deterministic: same bytes in, same bytes out.

Usage: manifest_to_er.py <manifest.toml> <release-iri> [source-label] > legacy.ttl
"""
import hashlib, sys, tomllib

path, iri = sys.argv[1], sys.argv[2].rstrip("/")
label = sys.argv[3] if len(sys.argv) > 3 else path
raw = open(path, "rb").read()
m = tomllib.loads(raw.decode("utf-8"))
q = lambda s: '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
comp = lambda cid: f"<{iri}/component/{cid}>"
rel, comps = m["release"], sorted(m["components"], key=lambda c: c["id"])
out = ["@prefix er: <http://seanchatmangpt.github.io/packs/chatman-ecosystem-release#> .",
       "@prefix dcterms: <http://purl.org/dc/terms/> .", "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .", "",
       f"<{iri}> a er:LegacyRelease ;", f"    dcterms:hasVersion {q(rel['version'])} ;",
       f"    dcterms:date {q(rel['target_date'])}^^xsd:date ;", f"    er:legacyStanding er:{rel['standing']} ;",
       f"    dcterms:source {q(label)} ;", f"    er:sourceSha256 {q('sha256:' + hashlib.sha256(raw).hexdigest())} ;"]
out += [f"    er:legacyRequiredRole {q(r)} ;" for r in sorted(rel["required_roles"])]
out += [f"    er:legacyComponent {comp(c['id'])} {'.' if i == len(comps) - 1 else ';'}" for i, c in enumerate(comps)]
for c in comps:
    out += ["", f"{comp(c['id'])} a er:LegacyComponent ;", f"    er:componentId {q(c['id'])} ;",
            f"    er:legacyRepository {q(c['repository'])} ;", f"    er:legacyRole {q(c['role'])} ;",
            f"    er:legacySha {q(c['sha'])} ;", f"    er:legacyStanding er:{c['standing']} ."]
sys.stdout.write("\n".join(out) + "\n")
