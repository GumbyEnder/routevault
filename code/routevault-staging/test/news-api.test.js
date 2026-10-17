const { describe, it, before, after } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const { createApp } = require("../server");
const { createMemoryStore } = require("../lib/store");

describe("news + discoveries API", () => {
  let server;
  let base;
  const newsPath = path.join(__dirname, "..", "data", "news.json");
  const discPath = path.join(__dirname, "..", "data", "discovered_models.json");
  const hadNews = fs.existsSync(newsPath);
  const hadDisc = fs.existsSync(discPath);
  let prevNews;
  let prevDisc;

  before(async () => {
    fs.mkdirSync(path.dirname(newsPath), { recursive: true });
    if (hadNews) prevNews = fs.readFileSync(newsPath);
    if (hadDisc) prevDisc = fs.readFileSync(discPath);
    fs.writeFileSync(
      newsPath,
      JSON.stringify({
        generated_at: "2026-09-21T00:00:00Z",
        count: 1,
        items: [{ id: "abc", title: "New LLM ships", url: "https://example.com/a", source: "Test" }],
      }),
    );
    fs.writeFileSync(
      discPath,
      JSON.stringify({ generated_at: "2026-09-21T00:00:00Z", count: 1, promoted: 1, models: [{ openrouter_id: "x-ai/test" }] }),
    );
    server = await createApp({ store: createMemoryStore(), env: { RV_STORE: "memory" } });
    await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
    const { port } = server.address();
    base = `http://127.0.0.1:${port}`;
  });

  after(async () => {
    await new Promise((resolve) => server.close(resolve));
    if (hadNews) fs.writeFileSync(newsPath, prevNews);
    else if (fs.existsSync(newsPath) && prevNews === undefined) {
      /* leave generated files */
    }
  });

  it("serves news.json", async () => {
    const res = await fetch(`${base}/api/news`);
    assert.equal(res.status, 200);
    const body = await res.json();
    assert.equal(body.count, 1);
    assert.equal(body.items[0].title, "New LLM ships");
  });

  it("serves discoveries", async () => {
    const res = await fetch(`${base}/api/discoveries`);
    assert.equal(res.status, 200);
    const body = await res.json();
    assert.equal(body.models[0].openrouter_id, "x-ai/test");
  });

  it("health includes news count", async () => {
    const res = await fetch(`${base}/api/health`);
    const body = await res.json();
    assert.equal(body.ok, true);
    assert.equal(body.news, 1);
  });
});
