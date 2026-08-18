"""Bridge the 149-dir ~/ggen-marketplace/packs/ content repository into the flat
<pack-id>.toml format ggen's resolver (ggen_marketplace::packs_registry::metadata) actually
consumes.

Real format check performed before writing this (not assumed):
  - Resolver's real `Pack` struct (crates/ggen-marketplace/src/packs_registry/types.rs):
    required fields id/name/version/description/category/packages (packages may be an empty
    Vec -- `#[serde(default)]` is NOT on it, so it must be present in the TOML, but `[]` is a
    valid present value); everything else (author/repository/license/templates/
    sparql_queries/dependencies/tags/keywords/production_ready/metadata) is `Option` or has
    `#[serde(default)]`.
  - Confirmed live: `ggen pack list`/`pack query` load pack metadata purely from the
    <id>.toml file's `[pack]` table (`load_pack_metadata`/`list_packs` in metadata.rs) and
    build the queryable RDF graph FROM THAT STRUCT (`SparqlExecutor::execute_query`,
    sparql_executor.rs) -- they never open a pack directory's ontology.ttl. So bridging only
    needs the TOML manifest, not the 147 real per-pack ontology.ttl files, for both
    GET /packs and POST /query to see a pack.
  - Confirmed live (python3 -c using tomllib over all 149 dirs, this session): every single
    ~/ggen-marketplace/packs/<dir>/pack.toml has EXACTLY ONE schema variant across 145/149
    dirs -- a bare `[pack]` table with only `name`/`version`/`description` (no id, no
    category, no packages array, no templates). 4 outliers (chatman-ecosystem-v26-9-1-
    release-gate, cyberpunk-tv-platform, dfcm-pack, ggen-self-pack) additionally carry a
    `license`/`category`/`tags`/etc. key already, which is compatible (a superset), not a
    different shape. `pack.name` matches the directory name for all 149 (zero mismatches).
    This means bridging is 100% mechanical for all 149: no per-pack semantic translation
    needed, because the marketplace pack.toml never had the resolver's richer schema (id,
    category, packages, templates, sparql_queries) to translate FROM -- those fields are
    synthesized generically (id = dirname, category = "marketplace" unless the source
    pack.toml already declares one, packages = [], no fabricated template/sparql entries).

What is honestly NOT bridged: the real domain-specific RDF triples inside each pack's own
ontology.ttl (147/149 dirs have one) are NOT transcribed into the resolver's toml-derived
graph -- POST /query against a bridged pack sees only the generic Pack-struct-derived facts
(id/name/version/description/category/tags/...), not that pack's actual ontology.ttl
content. Making ontology.ttl itself queryable would require extending the resolver's own
SparqlExecutor to load an external ontology file per pack -- a resolver code change, out of
scope for this bridge script (which only produces resolver-consumable TOML, doesn't patch
the resolver).

Usage:
    python3 bridge_packs.py --src ~/ggen-marketplace/packs --dst /path/to/bridged/packs
"""
import argparse
import os
import shutil
import sys
import tomllib


def load_source_pack(pack_dir: str) -> dict:
    toml_path = os.path.join(pack_dir, "pack.toml")
    with open(toml_path, "rb") as f:
        data = tomllib.load(f)
    return data.get("pack", {})


def bridge_one(pack_dir: str, pack_id: str) -> str:
    """Return resolver-format TOML text for one marketplace pack dir."""
    src = load_source_pack(pack_dir)

    name = src.get("name", pack_id)
    version = src.get("version", "0.0.0")
    description = src.get("description", "")
    category = src.get("category", "marketplace")
    license_ = src.get("license")
    tags = src.get("tags", [])

    has_ontology = os.path.exists(os.path.join(pack_dir, "ontology.ttl"))

    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    lines = []
    lines.append("[pack]")
    lines.append(f'id = "{esc(pack_id)}"')
    lines.append(f'name = "{esc(name)}"')
    lines.append(f'version = "{esc(version)}"')
    lines.append(f'description = """{description.replace(chr(34)*3, chr(92)+chr(34)*3)}"""')
    lines.append(f'category = "{esc(category)}"')
    if license_:
        lines.append(f'license = "{esc(license_)}"')
    lines.append("packages = []")
    lines.append("")
    lines.append("[pack.metadata]")
    lines.append(
        f"bridged_from = \"{esc(os.path.join('~/ggen-marketplace/packs', pack_id))}\""
    )
    lines.append(f"has_ontology_ttl = {'true' if has_ontology else 'false'}")
    if tags:
        tag_list = ", ".join(f'"{esc(t)}"' for t in tags)
        lines.append(f"tags = [{tag_list}]")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.expanduser("~/ggen-marketplace/packs"))
    ap.add_argument("--dst", required=True)
    ap.add_argument(
        "--seed-existing",
        default=os.path.expanduser("~/.ggen/packs"),
        help="Directory containing the resolver's pre-existing <id>.toml files "
        "(framework-lsp.toml, tower-lsp-max.toml) to copy alongside the bridged set "
        "so the combined dir is a superset, not a replacement.",
    )
    args = ap.parse_args()

    os.makedirs(args.dst, exist_ok=True)

    seeded = []
    if args.seed_existing and os.path.isdir(args.seed_existing):
        for fname in os.listdir(args.seed_existing):
            if fname.endswith(".toml"):
                shutil.copy2(
                    os.path.join(args.seed_existing, fname),
                    os.path.join(args.dst, fname),
                )
                seeded.append(fname)

    bridged = []
    skipped = []
    for entry in sorted(os.listdir(args.src)):
        pack_dir = os.path.join(args.src, entry)
        if not os.path.isdir(pack_dir):
            continue
        toml_path = os.path.join(pack_dir, "pack.toml")
        if not os.path.exists(toml_path):
            skipped.append((entry, "no pack.toml"))
            continue
        try:
            text = bridge_one(pack_dir, entry)
        except Exception as e:  # noqa: BLE001 - report, don't swallow
            skipped.append((entry, f"bridge error: {e}"))
            continue
        out_path = os.path.join(args.dst, f"{entry}.toml")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        bridged.append(entry)

    print(f"seeded (pre-existing resolver packs copied): {len(seeded)} -> {seeded}")
    print(f"bridged (marketplace packs converted): {len(bridged)}")
    print(f"skipped: {len(skipped)}")
    for s in skipped:
        print("  SKIP", s)
    print(f"total .toml files now in {args.dst}: {len(seeded) + len(bridged)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
