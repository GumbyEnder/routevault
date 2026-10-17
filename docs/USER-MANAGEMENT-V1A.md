# RouteVault — User Management v1a (locked)

**Status:** Shipped 2026-08-14 on Railway  
**Owner:** GumbyEnder  
**Canonical product path:** `/mnt/nas/agents/Projects/RouteVault/`  
**Live site:** https://routevault-production.up.railway.app (`/api/health` → `store: postgres`, `accounts: true`)

This is the work goal for **real** user management. Execute this cut only. Do not expand into v1b.

---

## Goal

A signed-in RouteVault user can keep the same Stack, weights, alerts, and resolve history across browsers, while unsigned visitors keep today’s local-only flow.

This is identity + a cloud copy of objects that already exist in the browser. It is not Team, billing, SSO, or a token proxy.

---

## Why this, and not “add auth”

Personal state already exists. It dies with the browser:

| Object | Key | Shape / cap |
|--------|-----|-------------|
| Stack | `routevault.stack.v1` | Up to 20 model ids |
| Weights | `routevault.weights.v1` | Quiz / explorer lens |
| Alerts | `routevault.alerts.v1` | Last 30 local rules (evaluate on Stack page open; no email) |
| Resolves | `routevault.routes.v1` | Last 50 resolver copies |
| Waitlist | `routevault.waitlist` | Email string, local only |

`login.html` is a waitlist form. `register.html` has no password. Pricing posts Free / Pro $19 / Team $49 and does not charge. v0 locked **no fake auth**. Real user management starts when the four personal objects have an owner.

---

## In scope (v1a)

1. **Identity** — email + password or magic link. One person, one account. Session cookie or token. Logout. Password reset.
2. **Account home** — replace waitlist pages with real register / login / “you are signed in as…”. Nav shows signed-in vs guest.
3. **Cloud profile** — server copy of stack, weights, alerts, resolve history. Same shapes the client already uses.
4. **First-login merge** — if this browser already has local data, offer **Keep local and upload**, **Use cloud**, or **Merge (union, cap 20 / 30 / 50)**. Never silent-overwrite.
5. **Guest still works** — explorer, quiz, one local stack, resolver stay usable with no account. Sign-in is optional, as Free already promises.
6. **Waitlist conversion** — if `routevault.waitlist` matches the new email, mark that address converted. Stop calling the page a waitlist once accounts are live.
7. **Honesty** — no card, no Pro gate, no “synced to Pro” copy until billing exists. Signed-in = cloud backup of Free personal state.

---

## Out of scope (v1b — do not start)

- Team seats, shared rules, audit log, SSO
- Stripe / posted-price charging
- Email or Telegram alert delivery (rules stay “evaluate when you open Stack”)
- Token proxy, BYOK vault, OpenRouter key storage
- Admin user CRUD as a product
- OAuth social login unless email/password is already shipping
- Changing the public catalog, scoring, or price history

---

## Definition of done

A person can:

1. Create an account on the live Railway site and log back in on a second browser.
2. Save a stack, change weights, add an alert, resolve a route — then see the same four objects after login on the second browser.
3. Stay a guest and keep using localStorage with no account.
4. Hit first login with existing local data and choose keep / cloud / merge without losing both copies.
5. Log out and see guest UI again; another user on that browser does not inherit the previous profile.
6. Fail closed on bad password, duplicate email, and unauthenticated write.

Automated coverage: register, login, logout, unauthorized write rejected, merge of a 3-id local stack with a 2-id cloud stack. Browser check: guest path still works; signed-in path survives a hard refresh.

---

## Constraints

- **No fake login.** If the API is not up, leave the current waitlist pages. Do not toast “logged in” against localStorage.
- **Public catalog stays public.** Accounts do not hide models, trends, or quiz.
- **Do not mint users in SQLite on CIFS.** New user store is a real hosted DB (Railway Postgres or equivalent), not `routevault.db` on the NAS share.
- **Static site can stay static** for catalog pages. Auth needs a small API beside it (or a thin app service). Do not rewrite Explorer / Trends / scoring to get sessions.
- **Forgejo remains primary.** Secrets only in Railway env, never in the tree.
- **Catalog pipeline is unchanged.** User tables must not live in the price/benchmark SQLite used by `pipeline.run`.

---

## Suggested implementation notes (not a rewrite mandate)

- Keep `code/routevault-staging/` as the public catalog UI unless a thin app service is required for cookies.
- Add a small API service in the same Railway project; do not bolt users onto the static file host’s filesystem.
- Client keys stay as the source of truth for *shape*. Server persists the same JSON.
- Session must be HTTP-only if cookies; never store password hashes in localStorage.

---

## Cut

| Slice | Ship |
|-------|------|
| **v1a (this doc)** | Accounts + sync of the four objects + merge on first login |
| **v1b (later)** | Pro gate, email alerts, Team |

Do not start v1b until a real billing or Team request lands.

## Shipped notes (2026-08-14)

- Same-origin Node server (`server.js`) serves the existing static catalog and `/api/*`.
- Users live in Railway **Postgres**, not NAS SQLite.
- Session cookie: `rv_session` (HttpOnly, SameSite=Lax, Secure in production).
- Password reset API exists. **Email delivery is not wired** — production will not show or send a token. That stays v1b.
- Automated: `cd code/routevault-staging && node --test test/*.test.js` (9/9).
- Live browser: guest stack → register → refresh → logout clears local → second browser sees the same stack.
