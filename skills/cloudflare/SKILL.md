---
name: cloudflare
description: Use whenever the user asks for help with their Cloudflare account — DNS, Zero Trust/Access, Workers, API tokens, zones, or anything about "cloudflare", "rn.ax" DNS, or "wm.rn.ax"/"windmill.rn.ax" infra explicitly. This is the accumulating knowledge base for how this user's Cloudflare account is actually set up, so read it before assuming account structure, credential scoping, or Access configuration from scratch.
---

# Cloudflare

Account name **rutinerad**, account id `65b388166b0c3d20fbfcc5c6b950c493`. Primary zone **`rn.ax`**, zone id `f63c5a76e0abf4d2fe0ed250f9346a11`. The `rn-ax` GitHub org mirrors this naming (see the `github` skill for its repo conventions) but is a separate system — GitHub org membership and Cloudflare account access aren't the same permission boundary.

## API tokens: prefer Account API Tokens over User API Tokens

Cloudflare distinguishes two token types, created in different places in the dashboard:
- **User API Tokens** (My Profile → API Tokens) — tied to the individual user; Cloudflare's own guidance is these suit ad hoc/personal scripting, not durable integrations, since they die if the user's access changes.
- **Account API Tokens** (Manage Account → Account API Tokens) — owned by the account itself, not any user; Cloudflare recommends these for anything durable (CI/CD, service integrations). **This user's stated preference: use Account API Tokens for exactly this reason whenever creating a new credential for an automation/CI use case** — don't default to a User API Token out of habit.

**Neither type can be minted via the API with the credentials on hand.** Creating a token — either kind — requires the acting token to already hold a meta-permission (`User API Tokens: Edit` or `Account API Tokens: Edit` respectively) that none of this user's existing tokens have, even ones with broad other permissions (e.g. being able to list permission groups doesn't imply being able to create tokens — that's a separate, more gated capability). Every new token has had to be created by the user directly in the dashboard, then handed over (or set directly as a secret) — plan for that manual step rather than assuming a way around it. API endpoints, if a suitably-scoped token is ever available: `POST /user/tokens` (user-owned) or `POST /accounts/{account_id}/tokens` (account-owned).

## Credential inventory

| File | Holds | Scope / notes |
|---|---|---|
| `~/.config/cloudflare/env` (`TOKEN`) | A User API Token | Access: Apps Edit, DNS Settings Edit, Account Analytics Read, Cloudflare Tunnel Edit, plus (added later) Access: Policies:Read, Access: Service Tokens:Read, all-zones DNS:Read, all-users API Tokens:Read. Broad, general-purpose — used for inspecting/editing Access apps, policies, service tokens, DNS. Cannot mint new tokens (see above). |
| `~/.wrangler/config/default.toml` (`api_token`) | A User API Token, `worker:edit` only | Used by `wrangler` for Worker deploys. Can't touch DNS/Email Routing — dashboard-only for those. |
| `~/.config/cloudflare-access/env` | `CF_ACCESS_CLIENT_ID`, `CF_ACCESS_CLIENT_SECRET` | The "Windmill · Public worker" Access **Service Token** (not a User/Account API Token — a distinct credential type for bypassing Access itself). See below. |

## Cloudflare Access (Zero Trust) service-token bypass

Several internal apps (`windmill.rn.ax` and others) sit behind Cloudflare Access, which intercepts every request — including ones carrying an otherwise-valid API bearer token — with a redirect to an interactive login. A **Service Token** lets a non-interactive caller (a Worker, a CI job) through instead, via two headers: `CF-Access-Client-Id` / `CF-Access-Client-Secret`.

**The critical, easy-to-miss step**: creating a Service Token object does nothing by itself. It has to be referenced by an **Include** rule inside a policy that's actually *attached to the specific Access Application* protecting the target hostname. A policy can exist, correctly reference the right token, and still not work if it was never added to that Application's policy list — checking the policy object alone isn't enough; check the Application's `policies` array contains it (`app_count` on the policy object is the tell). This exact gap caused a live bypass failure that looked like a bad credential but wasn't.

To verify a bypass is actually live: `curl -H "CF-Access-Client-Id: ..." -H "CF-Access-Client-Secret: ..." <url>` and check for a real response vs. a 302 to `<subdomain>.cloudflareaccess.com`. Decoding the redirect's `meta` JWT param (base64url, second dot-segment) shows `service_token_status` — `false` means Access didn't recognize the credential as valid for that request, regardless of how correct the token looks in isolation.

## Workers & wrangler

- Local `wrangler` binary: `brew install cloudflare-wrangler` (not the `wrangler` formula, which doesn't exist) — needed because this machine's shadowed `node`/`npm` resolution otherwise breaks modern `wrangler` (≥4.x requires Node ≥22). Auth via `CLOUDFLARE_API_TOKEN=<token> wrangler <command>`.
- A Worker's actual bindings (secrets/vars) don't always match what the source code references — verify after every deploy with `GET https://api.cloudflare.com/client/v4/accounts/<acct>/workers/scripts/<name>/bindings`, not just a successful `wrangler deploy` exit code. A Worker has shipped once with a secret referenced in code but never actually bound, which would have thrown on first real use.
- Worker source for this account's Workers lives in the `rn-ax/workers` GitHub repo (see `github` skill for the org's repo-naming convention) — see the `windmill` skill for what's actually deployed there and why.

## WAF / Bot Fight Mode blocking non-browser clients

The `rn.ax` zone's Bot Fight Mode / WAF can block non-browser clients (a feed validator, a webhook source's fetcher, etc.) with a 403 at Cloudflare's edge, before the request ever reaches the origin/Worker — invisible to browser-like tools (curl, WebFetch) since the block is IP/TLS-fingerprint based, not User-Agent based, so it can't be reproduced by spoofing headers from an unflagged network. Fix directly in the Cloudflare dashboard (Security → WAF) rather than via API — the token in `~/.config/cloudflare/env` has no Zone Settings or Firewall/WAF read/edit scope. Any new public endpoint meant for non-browser bots to poll (a feed reader, a validator, a webhook source) should get the same exemption up front rather than waiting for a report. Confirmed case: this blocked the JSON Feed validator (and likely Feedbin's fetcher) from reaching `wm.rn.ax`'s `feeds/` paths (see the `windmill` skill for what's served there) until the exemption was added.

## GitHub Actions secrets for Cloudflare credentials

See the `github` skill's note on org-level secrets not reaching private repos on GitHub's Free plan — this bit a Cloudflare Workers deploy token directly (`rn-ax/workers`, a private repo), so it's a real trap for any Cloudflare credential a CI workflow needs, not just a theoretical one.
