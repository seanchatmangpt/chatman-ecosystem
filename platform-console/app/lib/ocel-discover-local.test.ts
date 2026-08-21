// Real, Chicago-style integration test for `discoverOcDfgLocal`: no mocking
// of node:child_process, no fabricated OCDFG. This builds (or reuses) the
// real `wasm4pm-cli` (`wpm`) binary from the sibling `wasm4pm` checkout,
// points WPM_BIN_PATH at the real compiled binary, pipes a small real fixture
// OCEL 2.0 log through the real subprocess via `discoverOcDfgLocal`, and
// asserts on the real, returned OC-DFG structure (per-object-type nodes,
// edges, start/end activities) -- not a canned/mocked child_process result.
//
// If the wasm4pm checkout or its release binary is unavailable in this
// environment, the test is a real, visible skip (`t.skip(...)`), never a
// silent mock substitution -- same discipline as
// lib/entitlement-adapters/aws.test.ts's applyEntitlementEvent test.
import assert from "node:assert/strict";
import { test } from "node:test";
import { execFileSync } from "node:child_process";
import * as fs from "node:fs";
import { discoverOcDfgLocal, type OcelLog } from "./ocel-log";

const WASM4PM_REPO =
  process.env.WASM4PM_REPO_PATH ?? "/Users/sac/wasm4pm";
const WPM_RELEASE_BIN = `${WASM4PM_REPO}/target/release/wpm`;

function wpmBinaryAvailable(): string | null {
  if (process.env.WPM_BIN_PATH && fs.existsSync(process.env.WPM_BIN_PATH)) {
    return process.env.WPM_BIN_PATH;
  }
  if (fs.existsSync(WPM_RELEASE_BIN)) {
    return WPM_RELEASE_BIN;
  }
  // Fall back to whatever `wpm` resolves to on PATH (e.g. a CI-installed
  // binary), if any.
  try {
    execFileSync("which", ["wpm"], { stdio: ["ignore", "pipe", "ignore"] });
    return "wpm";
  } catch {
    return null;
  }
}

// Real OCEL 2.0 fixture: 4 events over 2 objects of different types
// (Order, Item) -- the exact same shape wasm4pm's own
// crates/wasm4pm-cli/src/commands/ocdfg_bridge.rs test fixture uses, so the
// expected discovered structure is independently known:
//   Order: Create -> Ship
//   Item:  Create -> Pack
const FIXTURE_LOG: OcelLog = {
  eventTypes: ["Create", "Ship", "Pack"],
  objectTypes: ["Order", "Item"],
  events: [
    {
      id: "e1",
      type: "Create",
      time: "2026-01-01T00:00:00Z",
      attributes: {},
      relationships: [{ objectId: "order1", qualifier: "creates" }],
    },
    {
      id: "e2",
      type: "Create",
      time: "2026-01-01T00:01:00Z",
      attributes: {},
      relationships: [{ objectId: "item1", qualifier: "creates" }],
    },
    {
      id: "e3",
      type: "Pack",
      time: "2026-01-01T00:02:00Z",
      attributes: {},
      relationships: [{ objectId: "item1", qualifier: "packs" }],
    },
    {
      id: "e4",
      type: "Ship",
      time: "2026-01-01T00:03:00Z",
      attributes: {},
      relationships: [{ objectId: "order1", qualifier: "ships" }],
    },
  ],
  objects: [
    { id: "order1", type: "Order", attributes: {} },
    { id: "item1", type: "Item", attributes: {} },
  ],
};

test("discoverOcDfgLocal calls the real wasm4pm-cli subprocess and returns the real discovered OC-DFG", (t) => {
  const bin = wpmBinaryAvailable();
  if (!bin) {
    t.skip(
      `no wasm4pm-cli (wpm) binary found -- checked WPM_BIN_PATH, ${WPM_RELEASE_BIN}, and PATH. ` +
        `Build it with: cd ${WASM4PM_REPO} && cargo build --release -p wasm4pm-cli`,
    );
    return;
  }
  const prevBin = process.env.WPM_BIN_PATH;
  process.env.WPM_BIN_PATH = bin;
  try {
    const ocdfg = discoverOcDfgLocal(FIXTURE_LOG);

    // Real structural assertions on the real subprocess's real output --
    // one DFG per object type, real edges/start/end activities.
    assert.equal(Object.keys(ocdfg.dfgs).length, 2, "expected one DFG per object type");

    const orderDfg = ocdfg.dfgs["Order"];
    assert.ok(orderDfg, "Order DFG present");
    assert.equal(orderDfg.start_activities["Create"], 1);
    assert.equal(orderDfg.end_activities["Ship"], 1);
    assert.ok(
      orderDfg.edges.some((e) => e.from === "Create" && e.to === "Ship" && e.frequency === 1),
      "Order DFG must contain a real Create->Ship edge with frequency 1",
    );

    const itemDfg = ocdfg.dfgs["Item"];
    assert.ok(itemDfg, "Item DFG present");
    assert.equal(itemDfg.start_activities["Create"], 1);
    assert.equal(itemDfg.end_activities["Pack"], 1);
    assert.ok(
      itemDfg.edges.some((e) => e.from === "Create" && e.to === "Pack" && e.frequency === 1),
      "Item DFG must contain a real Create->Pack edge with frequency 1",
    );
  } finally {
    if (prevBin === undefined) delete process.env.WPM_BIN_PATH;
    else process.env.WPM_BIN_PATH = prevBin;
  }
});

test("discoverOcDfgLocal throws (fail-closed) on a malformed OCEL log rather than fabricating a result", (t) => {
  const bin = wpmBinaryAvailable();
  if (!bin) {
    t.skip("no wasm4pm-cli (wpm) binary found");
    return;
  }
  const prevBin = process.env.WPM_BIN_PATH;
  process.env.WPM_BIN_PATH = bin;
  try {
    const malformed = { eventTypes: [], objectTypes: [], events: [], objects: [] } as OcelLog;
    assert.throws(() => discoverOcDfgLocal(malformed));
  } finally {
    if (prevBin === undefined) delete process.env.WPM_BIN_PATH;
    else process.env.WPM_BIN_PATH = prevBin;
  }
});
