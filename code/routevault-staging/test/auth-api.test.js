const { describe, it, before, after } = require("node:test");
const assert = require("node:assert/strict");
const { createApp, COOKIE } = require("../server");
const { createMemoryStore } = require("../lib/store");

function cookieFrom(res) {
  const raw = res.headers.getSetCookie?.() || [];
  const line = raw.find((c) => c.startsWith(`${COOKIE}=`)) || "";
  return line.split(";")[0];
}

async function json(res) {
  const text = await res.text();
  try {
    return JSON.parse(text);
  } catch {
    return { _raw: text, status: res.status };
  }
}

describe("auth + profile API", () => {
  let server;
  let base;

  before(async () => {
    process.env.COOKIE_SECURE = "0";
    process.env.RV_RETURN_RESET_TOKEN = "1";
    server = await createApp({ store: createMemoryStore(), env: { RV_STORE: "memory" } });
    await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
    const { port } = server.address();
    base = `http://127.0.0.1:${port}`;
  });

  after(async () => {
    await new Promise((resolve) => server.close(resolve));
  });

  it("rejects unauthenticated writes", async () => {
    const res = await fetch(`${base}/api/profile`, {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ stack: ["nope"] }),
    });
    assert.equal(res.status, 401);
  });

  it("registers, logs in, logs out, and rejects a bad password", async () => {
    const register = await fetch(`${base}/api/register`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email: "ada@example.com", password: "correcthorse" }),
    });
    assert.equal(register.status, 201);
    const created = await json(register);
    assert.equal(created.user.email, "ada@example.com");
    const session = cookieFrom(register);
    assert.match(session, new RegExp(`^${COOKIE}=`));

    const dup = await fetch(`${base}/api/register`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email: "ada@example.com", password: "correcthorse" }),
    });
    assert.equal(dup.status, 409);

    const bad = await fetch(`${base}/api/login`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email: "ada@example.com", password: "wrong-password" }),
    });
    assert.equal(bad.status, 401);

    const login = await fetch(`${base}/api/login`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email: "ada@example.com", password: "correcthorse" }),
    });
    assert.equal(login.status, 200);
    const loggedIn = cookieFrom(login);

    const me = await fetch(`${base}/api/me`, { headers: { cookie: loggedIn } });
    assert.equal((await json(me)).user.email, "ada@example.com");

    const out = await fetch(`${base}/api/logout`, {
      method: "POST",
      headers: { cookie: loggedIn },
    });
    assert.equal(out.status, 200);
    const after = await fetch(`${base}/api/me`, { headers: { cookie: loggedIn } });
    assert.equal((await json(after)).user, null);
  });

  it("syncs stack and merges 3 local + 2 cloud ids", async () => {
    const register = await fetch(`${base}/api/register`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email: "merge@example.com", password: "correcthorse" }),
    });
    const cookie = cookieFrom(register);
    const put = await fetch(`${base}/api/profile`, {
      method: "PUT",
      headers: { "content-type": "application/json", cookie },
      body: JSON.stringify({ stack: ["delta", "echo"] }),
    });
    assert.equal(put.status, 200);

    const merge = await fetch(`${base}/api/profile/merge`, {
      method: "POST",
      headers: { "content-type": "application/json", cookie },
      body: JSON.stringify({
        strategy: "union",
        local: { stack: ["alpha", "beta", "gamma"], weights: {}, alerts: [], routes: [] },
      }),
    });
    assert.equal(merge.status, 200);
    const body = await json(merge);
    assert.deepEqual(body.profile.stack, ["alpha", "beta", "gamma", "delta", "echo"]);
  });

  it("resets a password and signs the user in", async () => {
    await fetch(`${base}/api/register`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email: "reset@example.com", password: "oldpassword" }),
    });
    const forgot = await fetch(`${base}/api/password/forgot`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email: "reset@example.com" }),
    });
    const { reset_token } = await json(forgot);
    assert.ok(reset_token);
    const reset = await fetch(`${base}/api/password/reset`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ token: reset_token, password: "newpassword" }),
    });
    assert.equal(reset.status, 200);
    const old = await fetch(`${base}/api/login`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email: "reset@example.com", password: "oldpassword" }),
    });
    assert.equal(old.status, 401);
    const fresh = await fetch(`${base}/api/login`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email: "reset@example.com", password: "newpassword" }),
    });
    assert.equal(fresh.status, 200);
  });

  it("serves the public catalog without an account", async () => {
    const res = await fetch(`${base}/models.html`);
    assert.equal(res.status, 200);
    const html = await res.text();
    assert.match(html, /Models explorer/);
  });
});
