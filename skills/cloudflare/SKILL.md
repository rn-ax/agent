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
| "Cloudflare" item, "Agent" 1Password vault | An Account API Token (`cfat_...` prefix) | Broadest credential on hand — confirmed working for zone-level WAF/Rulesets reads (`GET .../rulesets/phases/http_request_firewall_custom/entrypoint`), unlike the older `~/.config/cloudflare/env` token below. Use `cf-api <method> <path> [curl-args...]` (this skill's own directory) for an already-authenticated REST call. It goes through `~/tasks/op-service-account` (see the `rn-config` skill), so it needs that machine's `op-service-account-agent` Keychain entry set up first. `/user/tokens/verify` returns "Invalid API Token" for this one specifically because that endpoint only validates *User* API Tokens — expected, not a sign the token is bad. |
| `~/.config/cloudflare/env` (`TOKEN`) | A User API Token | Access: Apps Edit, DNS Settings Edit, Account Analytics Read, Cloudflare Tunnel Edit, plus (added later) Access: Policies:Read, Access: Service Tokens:Read, all-zones DNS:Read, all-users API Tokens:Read. No Zone Settings or Firewall/WAF scope. Cannot mint new tokens (see above). |
| `~/.wrangler/config/default.toml` (`api_token`) | A User API Token, `worker:edit` only | Used by `wrangler` for Worker deploys. Can't touch DNS/Email Routing — dashboard-only for those. **Not present in every session** — confirmed missing (`wrangler whoami` → not authenticated) in an agent session on 2026-10-01 despite being documented here; this must live only in the user's own interactive shell setup, not anywhere an agent session can reach, and the broader Account API Token above does **not** substitute for it (`wrangler secret put` with it fails: "No access to the specified resource" — it lacks Workers scope). An agent needing to run `wrangler` unattended needs either this file actually present, or a new Account API Token minted with Workers Scripts:Edit and added to 1Password — neither has been done yet. |
| `~/.config/cloudflare-access/env` | `CF_ACCESS_CLIENT_ID`, `CF_ACCESS_CLIENT_SECRET` | The "Windmill · Public worker" Access **Service Token** (not a User/Account API Token — a distinct credential type for bypassing Access itself). See below. |

## Cloudflare Access (Zero Trust) service-token bypass

Several internal apps (`windmill.rn.ax` and others) sit behind Cloudflare Access, which intercepts every request — including ones carrying an otherwise-valid API bearer token — with a redirect to an interactive login. A **Service Token** lets a non-interactive caller (a Worker, a CI job) through instead, via two headers: `CF-Access-Client-Id` / `CF-Access-Client-Secret`.

**The critical, easy-to-miss step**: creating a Service Token object does nothing by itself. It has to be referenced by an **Include** rule inside a policy that's actually *attached to the specific Access Application* protecting the target hostname. A policy can exist, correctly reference the right token, and still not work if it was never added to that Application's policy list — checking the policy object alone isn't enough; check the Application's `policies` array contains it (`app_count` on the policy object is the tell). This exact gap caused a live bypass failure that looked like a bad credential but wasn't.

To verify a bypass is actually live: `curl -H "CF-Access-Client-Id: ..." -H "CF-Access-Client-Secret: ..." <url>` and check for a real response vs. a 302 to `<subdomain>.cloudflareaccess.com`. Decoding the redirect's `meta` JWT param (base64url, second dot-segment) shows `service_token_status` — `false` means Access didn't recognize the credential as valid for that request, regardless of how correct the token looks in isolation.

## Published hostnames: two layers protect them

A public hostname on a tunnel (a "published application") is protected by an Access application only when both of these line up:
- **The Access application** lists the hostname among its destinations, with the policies that decide who may enter (almost everything uses the reusable `Samuel` policy). Cloudflare matches it by hostname at the edge. Publishing a hostname neither creates nor selects an application; a hostname no application covers reaches the app directly, protected only by the app's own login. One application can cover several hostnames and then shares its policies and AUD tag (`Hive` covers `hive.rn.ax` and `songs.rn.ax`); an app that needs different policies or service tokens gets its own.
- **The tunnel route's `originRequest.access` block** (`required: true`, `teamName: rutinerad`, the application's `audTag`) makes `cloudflared` itself reject any request without a valid Access JWT for that application, so the route fails closed if the application is deleted or misconfigured. It is the "look up the AUD and paste it" option in the route's Access protection setting; "Using defaults" leaves the block out. `cloudflared` uses the **first** ingress rule matching a hostname, so a duplicate route without the block shadows a later one that has it.

The ingress rules are readable per tunnel: `cf-api GET /accounts/<acct>/cfd_tunnel/<tunnel-id>/configurations`. To audit every published hostname, request `/` on each over HTTPS and expect a 302 whose `Location` is `rutinerad.cloudflareaccess.com`, then compare with `GET /accounts/<acct>/access/apps` (destinations, wildcards included) and the route's `audTag`. A path-scoped application passes this check while leaving other paths open.

## Redirects

Zone redirects are Single Redirect rules, phase `http_request_dynamic_redirect` (`GET /zones/<zone>/rulesets/phases/http_request_dynamic_redirect/entrypoint`; the ruleset does not exist until the first rule is saved). They run at the edge before the tunnel, so a redirected hostname never reaches its origin, and the hostname still needs a proxied DNS record. A wildcard pattern must match the entire URL, and `${1}`, `${2}` are the `*` captures in order. `www.rn.ax` redirects to `rn.ax` with pattern `http*://www.rn.ax/*` and target `https://rn.ax/${2}` (301, "Preserve query string" off since the capture carries the query); matching on `https://` alone leaves plain `http://` requests reaching the origin. A saved rule takes a few seconds to apply, so verify with `curl --resolve` against the public edge address.

## WARP private-network access (reaching home hosts from phones and laptops)

Zero Trust org `rutinerad` routes private IPs to hosts through Cloudflare Tunnels. A device enrolled in WARP reaches a host's private IP when two things are true: a **CIDR route** for that IP points at the host's tunnel, and the IP is in the **default WARP profile's Split Tunnel includes** (the profile is in Include mode, so only listed ranges go through WARP). Raw protocols such as SSH then work from native apps with no `cloudflared` on the client; a public hostname through Access serves browsers only.

Current routes (virtual network `default`, id `094aa388-919f-4f8d-9836-2e67b73d6eb7`):

| CIDR | Tunnel | Purpose |
|---|---|---|
| `192.168.1.142/32` | TrueNAS | TrueNAS LAN services |
| `192.168.0.65/32` | Rutinerad Mac Mini (`7b47ae72-def3-4ccd-94a7-736f31f072b5`) | SSH to `rutinerad-mini` from the phone (Heeler/herdr) |
| `192.168.0.150/32` | Server (`4ae5783d-bfc9-4f99-aef8-0ef0ec1f2956`) | SSH to the `server` Mac mini (`server.local`) from the phone; clients use the IP since mDNS names do not resolve over WARP |

Adding a host:
1. Create a remote-managed tunnel in the dashboard (Zero Trust → Networks → Tunnels → Create → Cloudflared) and run the install command it shows on the host (`sudo cloudflared service install <TOKEN>`). The Homebrew service (`brew services start cloudflared`) runs bare `cloudflared` with no token and exits immediately.
2. In the tunnel's **Routes** tab choose **CIDR routes**, enter the host's `/32`, and set the virtual network to `default` explicitly. Published applications and Hostname routes serve other use cases.
3. Add the same `/32` to the default WARP profile's Split Tunnels. In the newer Cloudflare One dashboard (`one.dash.cloudflare.com`): Team & Resources → Devices → Device profiles → Default → Split Tunnels → Manage → Add new → IP Address, then Save in the dialog and Save profile on the page.
4. Give the host a DHCP reservation, since the route is pinned to its IP.

Tunnel creation, route creation and Split Tunnel edits are dashboard steps: both the `~/.config/cloudflare/env` token and the Account API Token return `Authentication error` (code 10000) on `POST .../cfd_tunnel` and `POST .../teamnet/routes`, despite the "Cloudflare Tunnel Edit" scope listed above. Reads work: `GET .../cfd_tunnel`, `GET .../teamnet/routes` and `cf-api GET /accounts/<acct>/devices/policy/include` verify the result. The Split Tunnel list lives on the default device policy (`GET /accounts/<acct>/devices/policies` shows one profile).

## Who may log in: email lists, not literal emails

Identity-based Access rules reference **Zero Trust Lists of type EMAIL** (one per person or group: `Samuel`, `David`, `Madde`, `Barnen`), so a person's addresses are updated in the list and every policy using it follows. The account has no legacy Access Groups (`GET /access/groups` is empty); lists are under `GET /accounts/<acct>/gateway/lists` and are readable with the Account API Token (the `~/.config/cloudflare/env` token gets `Authentication error` on `access/groups`). Reusable Access policies are built on them, among them `Samuel` (allow: the Samuel list plus a service token), `Barnen` (allow: the Barnen list) and `Authorized` (allow: all four lists). Create new allow rules with an Include of type Emails list.

Device enrollment is the Access application **Warp Login App** (`rutinerad.cloudflareaccess.com/warp`). It starts with only the non-identity `Contabo Runners` policy, so a person enrolling a phone or laptop gets `403 Forbidden` at `rutinerad.cloudflareaccess.com` until an Allow policy for their email list is added there (dashboard: Team & Resources → Devices → Management → Device enrollment). The `Samuel's devices` reusable policy (Allow, Include → Emails list → Samuel) is attached at precedence 2, and the iPhone enrolled through it on 2026-10-13. The iOS client is **Cloudflare One Agent** (the App Store's separate Zero Trust app; the consumer 1.1.1.1 app has no team login), enrolled with team name `rutinerad`. Enrolled devices are listed by `cf-api GET /accounts/<acct>/devices`.

## Workers & wrangler

- Local `wrangler` binary: `brew install cloudflare-wrangler` (not the `wrangler` formula, which doesn't exist) — needed because this machine's shadowed `node`/`npm` resolution otherwise breaks modern `wrangler` (≥4.x requires Node ≥22). Auth via `CLOUDFLARE_API_TOKEN=<token> wrangler <command>`.
- A Worker's actual bindings (secrets/vars) don't always match what the source code references — verify after every deploy with `GET https://api.cloudflare.com/client/v4/accounts/<acct>/workers/scripts/<name>/bindings`, not just a successful `wrangler deploy` exit code. A Worker has shipped once with a secret referenced in code but never actually bound, which would have thrown on first real use.
- Worker source for this account's Workers lives in the `rn-ax/workers` GitHub repo (see `github` skill for the org's repo-naming convention) — see the `windmill` skill for what's actually deployed there and why.

## WAF / Bot Fight Mode blocking non-browser clients

The `rn.ax` zone's Bot Fight Mode / WAF can block non-browser clients (a feed validator, a webhook source's fetcher, etc.) with a 403 at Cloudflare's edge, before the request ever reaches the origin/Worker — invisible to browser-like tools (curl, WebFetch) since the block is IP/TLS-fingerprint based, not User-Agent based, so it can't be reproduced by spoofing headers from an unflagged network. The `~/.config/cloudflare/env` token has no Zone Settings or Firewall/WAF scope, but the Account API Token above does — read the live rules with `cf-api GET /zones/f63c5a76e0abf4d2fe0ed250f9346a11/rulesets/phases/http_request_firewall_custom/entrypoint` rather than assuming what's configured; editing still needs the dashboard (Security → WAF) until write access is confirmed.

This zone has both User-Agent-based and geo-based custom rules (confirmed: a block and a challenge rule, each scoped to a different geography, plus a User-Agent-based exemption for Windmill's feed endpoints — check current state with the command above, don't rely on this staying accurate). Custom rules evaluate top-to-bottom within the phase, and a `skip` action only exempts rules positioned *after* it — so a new public endpoint needing its own exemption must have that exemption added ahead of whatever block/challenge rule it's meant to bypass, not just appended to the list, and its reachability from wherever it needs to be reachable from should be checked against the live rules rather than assumed.

## GitHub Actions secrets for Cloudflare credentials

See the `github` skill's note on org-level secrets not reaching private repos on GitHub's Free plan — this bit a Cloudflare Workers deploy token directly (`rn-ax/workers`, a private repo), so it's a real trap for any Cloudflare credential a CI workflow needs, not just a theoretical one.
