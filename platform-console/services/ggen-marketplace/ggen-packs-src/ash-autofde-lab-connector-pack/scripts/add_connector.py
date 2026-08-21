#!/usr/bin/env python3
"""Real, small, reusable generator: one cnv-any tool name -> one new aac:AshConnector
individual appended to this pack's ontology.ttl.

Eliminates hand-editing ontology.ttl per new connector (ERRC: Eliminate). Takes exactly
one real input: a tool name from the real cnv-any manifest, e.g. "fabric__cache-stats"
(ERRC: Reduce). Derives resourceModule/domainModule/actionName/outputFile/tableName by
reading the naming convention already established by the 3 existing individuals
(AutofdePlannerCandidate/fabric__solve, AutofdePlannerCatalog/fabric__catalog,
AutofdePlannerMatch/fabric__match) -- it does not invent a new convention (ERRC: Raise --
the pack becomes self-extending instead of requiring a new hand-authored block per tool).

Naming convention observed in ontology.ttl (verified against the 3 existing individuals):
  - tool "fabric__<name>" (name may contain '-')
  - class local name:  Autofde Planner + PascalCase(name with '-'/'_' as word breaks)
      e.g. "cache-stats"  -> AutofdePlannerCacheStats
           "cache-hotset" -> AutofdePlannerCacheHotset
  - resourceModule:    "Xaas.Operations." + class local name
  - domainModule:      "Xaas.Operations"                         (constant, all 3 existing)
  - actionName:        "request_" + snake_case(name)             e.g. request_cache_stats
  - cnvDeployBaseUrlEnv: "cnv_deploy_base_url"                    (constant, all 3 existing)
  - outputFile:         "lib/xaas/operations/autofde_planner_" + snake_case(name) + ".ex"
  - tableName:          zero-required-argument tools (catalog-shaped, like fabric__catalog
                         and fabric__match) get the "_requests" suffix used by both existing
                         zero/optional-arg individuals:
                         "autofde_planner_" + snake_case(name) + "_requests"
                         (fabric__solve's "_candidates" tableName is solve-specific --
                         a real solve call, not a bare status/report tool -- and is not
                         reused here; both remaining tools, cache-stats/cache-hotset, are
                         confirmed zero-required-argument report tools, matching catalog).

This script is deliberately conservative: it REFUSES to run rather than guess if the tool
does not exist in the real manifest, if it already has an aac:AshConnector individual, or
if it carries required arguments this template does not yet know how to shape (only
fabric__solve and fabric__match, both already hand-added, use required/positional args
today).
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PACK_DIR = Path(__file__).resolve().parent.parent
ONTOLOGY_PATH = PACK_DIR / "ontology.ttl"
MANIFEST_PATH = (
    Path.home()
    / "clap-noun-verb"
    / "clap-noun-verb-any"
    / "examples"
    / "autofde_lab_planners"
    / "cnv-any.json"
)
# Real, separate repo (xaas). Overridable via XAAS_ROOT so a real regression test can
# point this script at a real temp directory tree instead of the real ~/xaas checkout
# (Chicago-style: a real subprocess against real files on disk, never a mocked path).
XAAS_ROOT = Path(os.environ.get("XAAS_ROOT", str(Path.home() / "xaas")))
# Kept in sync by this same generator so the class of gap (new Ash resource table with
# zero SparqlBridge coverage) cannot recur silently -- see resource_module_generated()
# and the guard in apply_sparql_bridge_extension() below (FMEA RPN=576 fix).
SPARQL_BRIDGE_PATH = XAAS_ROOT / "lib" / "xaas" / "sparql_bridge.ex"

# Real ggen-cli-lib invocation, confirmed this session (DIFFERENTIAL-REGEN-PROOF.md).
GGEN_MANIFEST_PATH = (
    Path.home() / "chatman-ecosystem" / "platform-console" / "services" / "ggen"
    / "ggen-src" / "Cargo.toml"
)
# Real destination repo. Confirmed tilde-expansion bug: ggen sync run, run from this
# pack's own directory, writes relative to the pack dir (this pack's own scratch
# lib/xaas/operations/*.ex), never to ~/xaas, no matter what outputFile says in
# ontology.ttl -- so the generated file must be copied to the real xaas checkout by
# hand (or, now, by this script) as a separate, explicit step.
XAAS_OPERATIONS_DIR = XAAS_ROOT / "lib" / "xaas" / "operations"


def run_ggen_sync() -> bool:
    """Real `ggen sync run`, via `cargo +nightly-2026-06-22 run --manifest-path
    .../ggen-src/Cargo.toml -p ggen-cli-lib --bin ggen -- sync run`, executed from this
    pack's own directory (PACK_DIR) so relative output paths resolve under the pack,
    matching the real, confirmed invocation used throughout this session. Returns True
    on success (real subprocess exit code 0), False otherwise -- never fabricates a
    successful run."""
    cmd = [
        "cargo", "+nightly-2026-06-22", "run",
        "--manifest-path", str(GGEN_MANIFEST_PATH),
        "-p", "ggen-cli-lib", "--bin", "ggen",
        "--", "sync", "run",
    ]
    print(f"RUNNING: {' '.join(cmd)} (cwd={PACK_DIR})")
    result = subprocess.run(cmd, cwd=PACK_DIR, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        print(f"REFUSED: ggen sync run exited {result.returncode}", file=sys.stderr)
        return False
    print("OK: ggen sync run completed")
    return True


def copy_generated_file_to_xaas(output_file: str) -> bool:
    """Real workaround for the disclosed tilde-expansion bug: ggen sync run writes the
    generated .ex file under this pack's own scratch lib/ dir (PACK_DIR / output_file),
    never to the real ~/xaas checkout. Copies the real generated bytes to the real xaas
    path. Refuses (does not fabricate a copy) if the source file does not exist."""
    src = PACK_DIR / output_file
    if not src.exists():
        print(f"REFUSED: expected generated file not found at {src}", file=sys.stderr)
        return False
    dest = XAAS_ROOT / output_file
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(src.read_bytes())
    print(f"OK: copied {src} -> {dest}")
    return True


def snake(name: str) -> str:
    return name.replace("-", "_")


def pascal(name: str) -> str:
    return "".join(word.capitalize() for word in re.split(r"[-_]", name) if word)


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text())


def find_command(manifest: dict, tool_name: str):
    """tool_name is the aac:invokeTool form, e.g. fabric__cache-stats."""
    if "__" not in tool_name:
        return None
    for cmd in manifest["commands"]:
        if "__".join(cmd["path"]) == tool_name:
            return cmd
    return None


def already_exists(ontology_text: str, invoke_tool: str) -> bool:
    return f'aac:invokeTool "{invoke_tool}"' in ontology_text


def build_individual(cmd: dict, tool_name: str) -> str:
    group, short_name = tool_name.split("__", 1)
    class_local = "AutofdePlanner" + pascal(short_name)
    resource_module = f"Xaas.Operations.{class_local}"
    domain_module = "Xaas.Operations"
    action_name = f"request_{snake(short_name)}"
    output_file = f"lib/xaas/operations/autofde_planner_{snake(short_name)}.ex"
    table_name = f"autofde_planner_{snake(short_name)}_requests"
    about = cmd.get("about", "")

    return f"""
aac:{class_local} a aac:AshConnector ;
  dcterms:description "Real connector: xaas Ash resource -> cnv-deploy POST /invoke tool {tool_name} ({about}, zero required arguments, confirmed clap-noun-verb-any/examples/autofde_lab_planners/cnv-any.json, generated by scripts/add_connector.py)" ;
  aac:resourceModule "{resource_module}" ;
  aac:domainModule "{domain_module}" ;
  aac:invokeTool "{tool_name}" ;
  aac:actionName "{action_name}" ;
  aac:cnvDeployBaseUrlEnv "cnv_deploy_base_url" ;
  aac:outputFile "{output_file}" ;
  aac:tableName "{table_name}" .
"""


def sparql_bridge_already_covers(bridge_text: str, alias_module: str) -> bool:
    return f"alias Xaas.Operations.{alias_module}" in bridge_text


def build_sparql_bridge_function(class_local: str, short_name: str) -> tuple[str, str, str, str]:
    """Return (class_name, fn_name, doc, private_fn) for the new table,
    following the exact real pattern established by catalog_to_turtle/0 and
    match_to_turtle/0 in lib/xaas/sparql_bridge.ex (zero-required-arg, report-shaped
    connector: no solver/domain extraction, same field set as PlannerCatalogRequest/
    PlannerMatchRequest)."""
    fn_name = f"{snake(short_name)}_to_turtle"
    class_name = f"AutofdePlanner{class_local[len('AutofdePlanner'):]}"  # e.g. AutofdePlannerCacheStats
    aacm_class = f"aacm:PlannerCacheStatsRequest" if False else None  # placeholder unused
    rdf_class = "aacm:Planner" + class_local[len("AutofdePlanner"):] + "Request"

    doc = f"""
  @doc \"\"\"
  Query the real autofde_planner_{snake(short_name)}_requests table (via Ash) and return
  real Turtle text -- one {rdf_class} individual per row.
  \"\"\"
  @spec {fn_name}() :: String.t()
  def {fn_name} do
    {{:ok, rows}} = Ash.read({class_name})
    turtle_document(Enum.map(rows, &{snake(short_name)}_row_to_turtle/1))
  end
"""

    private_fn = f"""
  defp {snake(short_name)}_row_to_turtle(%{class_name}{{}} = row) do
    subject = "{rdf_class}_#{{row.id}}"

    render_individual(subject, [
      {{"a", "{rdf_class}"}},
      {{"aacm:query", turtle_string(row.query)}},
      {{"aacm:trajectorySha256", turtle_maybe_string(row.trajectory_sha256)}},
      {{"aacm:requestedAt", turtle_maybe_datetime(row.requested_at)}}
    ])
  end
"""

    return class_name, fn_name, doc, private_fn


def resource_module_generated(short_name: str) -> bool:
    """True iff the real Ash resource module this connector needs already exists on
    disk in the real xaas checkout (XAAS_ROOT). This is the precondition FMEA RPN=576
    found missing: apply_sparql_bridge_extension() used to wire an `alias` plus an
    `Ash.read(<Class>)` call into the live to_turtle/0 monitor function with no check
    that the aliased module exists anywhere -- a module that, on the documented default
    (non---deploy) path, is never generated at all, leaving to_turtle/0 crashing on the
    next real invocation. Mirrors the real outputFile naming convention used throughout
    this script (see build_individual())."""
    output_file = f"lib/xaas/operations/autofde_planner_{snake(short_name)}.ex"
    return (XAAS_ROOT / output_file).exists()


def apply_sparql_bridge_extension(class_local: str, short_name: str) -> bool:
    """Real, working code-generation step: append a new per-table public query function
    + private row-renderer to lib/xaas/sparql_bridge.ex, following the exact pattern of
    catalog_to_turtle/0 and match_to_turtle/0, and wire it into the aggregate to_turtle/0.
    Refuses (does not guess) if sparql_bridge.ex is missing, already covers this table,
    or -- FMEA RPN=576 guard -- the real Ash resource module this would wire in has not
    actually been generated yet in the real xaas checkout. Returns True iff the bridge
    already covered the table or was successfully extended; False on any refusal, so
    callers (main()) can propagate a real non-zero exit code instead of silently
    continuing."""
    if not SPARQL_BRIDGE_PATH.exists():
        print(f"REFUSED: sparql_bridge.ex not found at {SPARQL_BRIDGE_PATH}", file=sys.stderr)
        return False

    if not resource_module_generated(short_name):
        output_file = f"lib/xaas/operations/autofde_planner_{snake(short_name)}.ex"
        print(
            f"REFUSED: real Ash resource module not found at {XAAS_ROOT / output_file} -- "
            f"wiring sparql_bridge.ex now would add an `alias Xaas.Operations.{class_local}` "
            f"plus an `Ash.read({class_local})` call to the live to_turtle/0 monitor function "
            f"for a module that does not exist yet, crashing it on the next real invocation "
            f"(FMEA RPN=576). Run add_connector.py with --deploy first (it generates and "
            f"copies the module before wiring the bridge), or once the module exists in "
            f"xaas by another means, retry with --backfill-bridge={short_name}.",
            file=sys.stderr,
        )
        return False

    bridge_text = SPARQL_BRIDGE_PATH.read_text()
    class_name, fn_name, doc, private_fn = build_sparql_bridge_function(class_local, short_name)

    if sparql_bridge_already_covers(bridge_text, class_name):
        print(f"OK: sparql_bridge.ex already covers {class_name}, no change needed")
        return True

    # 1. add alias, right after the existing aliases
    alias_line = f"  alias Xaas.Operations.{class_name}\n"
    marker = "  alias Xaas.Operations.AutofdePlannerMatch\n"
    if marker not in bridge_text:
        print(f"REFUSED: expected alias anchor not found in {SPARQL_BRIDGE_PATH}", file=sys.stderr)
        return False
    bridge_text = bridge_text.replace(marker, marker + alias_line)

    # 2. wire into the aggregate to_turtle/0 read + body list. Anchor on the LAST
    # "{:ok, <var>} = Ash.read(...)" line inside to_turtle/0 (whichever table was added
    # most recently -- this generator may run more than once), not a fixed table name, so
    # repeated extensions compose instead of clobbering each other.
    read_var = f"{snake(short_name)}_requests"
    read_line = f"    {{:ok, {read_var}}} = Ash.read({class_name})\n"
    read_pattern = re.compile(r"(    \{:ok, \w+\} = Ash\.read\(\w+\)\n)(?=\n    header = \"\"\"\n    @prefix aacm:)")
    read_match = read_pattern.search(bridge_text)
    if read_match is None:
        print(f"REFUSED: expected to_turtle/0 read anchor not found in {SPARQL_BRIDGE_PATH}", file=sys.stderr)
        return False
    insert_at = read_match.end(1)
    bridge_text = bridge_text[:insert_at] + read_line + bridge_text[insert_at:]

    # Anchor on the LAST "Enum.map(<var>, &.../1))" line that closes the `body =` group
    # (ends the parenthesised ++ chain with "))\n").
    body_line = f"         Enum.map({read_var}, &{snake(short_name)}_row_to_turtle/1))\n"
    body_pattern = re.compile(r"(         Enum\.map\(\w+, &[\w/]+\)\))\n(?=\s*\|> Enum\.join\(\"\\n\"\)\n\s*\n\s*header <> body\n  end)")
    body_match = body_pattern.search(bridge_text)
    if body_match is None:
        print(f"REFUSED: expected to_turtle/0 body anchor not found in {SPARQL_BRIDGE_PATH}", file=sys.stderr)
        return False
    # old_close is currently the LAST line of the ++ chain, so it carries two closing
    # parens: one for its own Enum.map(...) call, one for the outer grouping paren
    # opened by "body = (Enum.map(...". It is about to stop being last, so it keeps
    # only its own Enum.map close; the new line becomes the last one and inherits the
    # outer-group close instead.
    old_close = body_match.group(1)  # e.g. "...Enum.map(match_requests, &match_to_turtle/1))"
    assert old_close.endswith("))")
    old_close_demoted = old_close[:-1]  # drop the outer-group close, keep Enum.map's own
    new_close = old_close_demoted + " ++\n" + body_line.rstrip("\n")
    bridge_text = bridge_text[: body_match.start(1)] + new_close + "\n" + bridge_text[body_match.end(0):]

    # 3. append the new public @doc/@spec/def function right after match_to_turtle/0
    match_fn_end_marker = "  def match_to_turtle do\n    {:ok, rows} = Ash.read(AutofdePlannerMatch)\n    turtle_document(Enum.map(rows, &match_to_turtle/1))\n  end\n"
    if match_fn_end_marker not in bridge_text:
        print(f"REFUSED: expected match_to_turtle/0 anchor not found in {SPARQL_BRIDGE_PATH}", file=sys.stderr)
        return False
    bridge_text = bridge_text.replace(match_fn_end_marker, match_fn_end_marker + doc)

    # 4. append the new private row-renderer right after match_to_turtle/1 (private)
    match_private_marker = '  defp match_to_turtle(%AutofdePlannerMatch{} = row) do\n    subject = "aacm:PlannerMatchRequest_#{row.id}"\n\n    render_individual(subject, [\n      {"a", "aacm:PlannerMatchRequest"},\n      {"aacm:query", turtle_string(row.query)},\n      {"aacm:trajectorySha256", turtle_maybe_string(row.trajectory_sha256)},\n      {"aacm:requestedAt", turtle_maybe_datetime(row.requested_at)}\n    ])\n  end\n'
    if match_private_marker not in bridge_text:
        print(f"REFUSED: expected match_to_turtle/1 anchor not found in {SPARQL_BRIDGE_PATH}", file=sys.stderr)
        return False
    bridge_text = bridge_text.replace(match_private_marker, match_private_marker + private_fn)

    SPARQL_BRIDGE_PATH.write_text(bridge_text)
    print(f"OK: extended {SPARQL_BRIDGE_PATH} with {fn_name}/0 and wired into to_turtle/0")
    return True


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(
            "usage: add_connector.py <tool-name e.g. fabric__cache-stats> [--deploy]\n"
            "       add_connector.py --backfill-bridge=<tool-name>   "
            "(sparql_bridge.ex only, ontology.ttl individual already exists)\n"
            "\n"
            "--deploy: after editing ontology.ttl, run the real `ggen sync run`\n"
            "  (cargo +nightly-2026-06-22, ggen-cli-lib), copy the real generated .ex file\n"
            "  to the real ~/xaas checkout, THEN wire sparql_bridge.ex (only once the real\n"
            "  Ash resource module exists on disk -- FMEA RPN=576 guard). Default off:\n"
            "  without --deploy this script only edits the ontology; sparql_bridge.ex is\n"
            "  left untouched until the module actually exists, to avoid wiring a live\n"
            "  monitor function (to_turtle/0) to a module that isn't generated yet.",
            file=sys.stderr,
        )
        return 2

    if args[0] == "--backfill-bridge":
        print("usage: add_connector.py --backfill-bridge <tool-name>", file=sys.stderr)
        return 2

    deploy = "--deploy" in args
    positional = [a for a in args if a != "--deploy"]
    if len(positional) != 1:
        print("usage: add_connector.py <tool-name> [--deploy]", file=sys.stderr)
        return 2
    tool_name = positional[0]

    if tool_name.startswith("--backfill-bridge="):
        short_name = tool_name.split("=", 1)[1]
        class_local = "AutofdePlanner" + pascal(short_name)
        if not apply_sparql_bridge_extension(class_local, short_name):
            return 1
        return 0

    if not MANIFEST_PATH.exists():
        print(f"REFUSED: real manifest not found at {MANIFEST_PATH}", file=sys.stderr)
        return 1
    manifest = load_manifest()

    cmd = find_command(manifest, tool_name)
    if cmd is None:
        print(f"REFUSED: tool '{tool_name}' not found in real manifest {MANIFEST_PATH}", file=sys.stderr)
        return 1

    required_args = [a for a in cmd.get("arguments", []) if a.get("required")]
    if required_args:
        print(
            f"REFUSED: tool '{tool_name}' has {len(required_args)} required argument(s) "
            f"({[a['id'] for a in required_args]}) -- this generator only knows the "
            f"zero-required-argument connector shape (like fabric__catalog). Required-arg "
            f"tools (fabric__solve, fabric__match) were hand-shaped; extend the generator "
            f"deliberately before using it for another required-arg tool.",
            file=sys.stderr,
        )
        return 1

    ontology_text = ONTOLOGY_PATH.read_text()
    if already_exists(ontology_text, tool_name):
        print(f"REFUSED: aac:invokeTool \"{tool_name}\" already has an individual in {ONTOLOGY_PATH}", file=sys.stderr)
        return 1

    block = build_individual(cmd, tool_name)
    ONTOLOGY_PATH.write_text(ontology_text.rstrip("\n") + "\n" + block)
    print(f"OK: appended aac:AshConnector individual for '{tool_name}' to {ONTOLOGY_PATH}")
    print(block)

    _, short_name = tool_name.split("__", 1)
    class_local = "AutofdePlanner" + pascal(short_name)

    # FMEA RPN=576 fix: sparql_bridge.ex wiring used to happen right here, on every
    # run, before the --deploy gate below -- so the documented default (non---deploy)
    # path wired an `alias` + `Ash.read(<Class>)` call into the live to_turtle/0
    # monitor function for an Ash resource module that had not been generated yet
    # (it's only generated by run_ggen_sync()+copy_generated_file_to_xaas() below,
    # and only under --deploy). Wiring is now deferred until after those two steps
    # actually put the module on disk in the real xaas checkout, so
    # apply_sparql_bridge_extension()'s own resource_module_generated() guard is
    # never tripped on this path. On the default path it is skipped outright.
    if not deploy:
        print(
            "(--deploy not passed: ontology.ttl edited only. sparql_bridge.ex wiring is "
            "deferred until the real Ash resource module exists on disk in xaas -- rerun "
            "with --deploy, or once it exists by another means, with "
            f"--backfill-bridge={short_name}.)"
        )
        return 0

    output_file = f"lib/xaas/operations/autofde_planner_{snake(short_name)}.ex"
    if not run_ggen_sync():
        return 1
    if not copy_generated_file_to_xaas(output_file):
        return 1

    if not apply_sparql_bridge_extension(class_local, short_name):
        return 1

    print(f"OK: --deploy pipeline complete for '{tool_name}' "
          f"-> {XAAS_ROOT / output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
