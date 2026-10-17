const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const {
  mergeProfiles,
  needsMerge,
  hasPersonalData,
  emptyProfile,
  DEFAULT_WEIGHTS,
} = require("../lib/profile");

describe("profile merge", () => {
  it("detects empty vs personal data", () => {
    assert.equal(hasPersonalData(emptyProfile()), false);
    assert.equal(hasPersonalData({ stack: ["a"] }), true);
    assert.equal(hasPersonalData({ weights: { ...DEFAULT_WEIGHTS, coding: 40 } }), true);
  });

  it("needs merge only when both sides have different personal data", () => {
    const local = { stack: ["a", "b", "c"], weights: DEFAULT_WEIGHTS, alerts: [], routes: [] };
    const cloud = { stack: ["d", "e"], weights: DEFAULT_WEIGHTS, alerts: [], routes: [] };
    assert.equal(needsMerge(local, cloud), true);
    assert.equal(needsMerge(local, emptyProfile()), false);
    assert.equal(needsMerge(emptyProfile(), cloud), false);
    assert.equal(needsMerge(local, local), false);
  });

  it("unions a 3-id local stack with a 2-id cloud stack", () => {
    const local = { stack: ["alpha", "beta", "gamma"], weights: { coding: 40 }, alerts: [], routes: [] };
    const cloud = { stack: ["delta", "echo"], weights: DEFAULT_WEIGHTS, alerts: [], routes: [] };
    const merged = mergeProfiles(local, cloud, "union");
    assert.deepEqual(merged.stack, ["alpha", "beta", "gamma", "delta", "echo"]);
    assert.equal(merged.weights.coding, 40);
  });

  it("keep-local and use-cloud do not silent-mix", () => {
    const local = { stack: ["only-local"], weights: DEFAULT_WEIGHTS, alerts: [], routes: [] };
    const cloud = { stack: ["only-cloud"], weights: DEFAULT_WEIGHTS, alerts: [], routes: [] };
    assert.deepEqual(mergeProfiles(local, cloud, "local").stack, ["only-local"]);
    assert.deepEqual(mergeProfiles(local, cloud, "cloud").stack, ["only-cloud"]);
  });
});
