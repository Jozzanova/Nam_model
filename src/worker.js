// Every request to the site passes through here before the static assets are served.
//
// Cloudflare Access sits in front of nam-type-model.jskjeltorp.workers.dev and asks visitors to log in
// (only invited emails). Access adds a signed token (Cf-Access-Jwt-Assertion) to each request it lets
// through. This worker verifies that token, so the site only answers requests that really came through
// Access. If Access is missing or misconfigured, every request is refused ("fail closed") rather than
// the site quietly becoming public. Same design as the equity factors dashboard's middleware.
//
// Variables (wrangler.jsonc "vars"): ACCESS_TEAM_DOMAIN, ACCESS_AUD (the Access application's audience tag).

const CERTS_MAX_AGE_MS = 60 * 60 * 1000;     // re-read Access's signing keys hourly
const CERTS_MIN_REFETCH_MS = 5 * 60 * 1000;  // ...but at most every 5 minutes for unknown keys
let certs = { keys: null, team: null, fetchedAt: 0 };

export default {
  async fetch(request, env) {
    if (!env.ACCESS_TEAM_DOMAIN || !env.ACCESS_AUD) {
      return deny("This site is not open yet: its login (Cloudflare Access) has not been configured.");
    }
    const token = request.headers.get("Cf-Access-Jwt-Assertion");
    if (!token) return deny("This site is only available to invited people.");
    try {
      await verifyToken(token, env.ACCESS_TEAM_DOMAIN, env.ACCESS_AUD);
    } catch {
      return deny("Your login could not be verified. Reload the page to log in again.");
    }
    return env.ASSETS.fetch(request);
  },
};

function deny(message) {
  return new Response(message, {
    status: 403,
    headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" },
  });
}

function base64url(text) {
  const b64 = text.replace(/-/g, "+").replace(/_/g, "/") + "=".repeat((4 - (text.length % 4)) % 4);
  return Uint8Array.from(atob(b64), c => c.charCodeAt(0));
}
const decodeJson = part => JSON.parse(new TextDecoder().decode(base64url(part)));

async function verifyToken(token, team, audience) {
  const [headerPart, payloadPart, signaturePart] = token.split(".");
  if (!signaturePart) throw new Error("malformed token");
  const header = decodeJson(headerPart), payload = decodeJson(payloadPart);
  if (header.alg !== "RS256") throw new Error("unexpected algorithm");

  const key = await signingKey(team, header.kid);
  const signed = new TextEncoder().encode(`${headerPart}.${payloadPart}`);
  if (!(await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, base64url(signaturePart), signed))) {
    throw new Error("bad signature");
  }
  const now = Date.now() / 1000;
  if (!(payload.exp > now)) throw new Error("expired");
  if (payload.nbf && payload.nbf > now + 60) throw new Error("not valid yet");
  if (payload.iss !== `https://${team}`) throw new Error("wrong issuer");
  const audiences = Array.isArray(payload.aud) ? payload.aud : [payload.aud];
  if (!audiences.includes(audience)) throw new Error("wrong audience");
}

async function signingKey(team, kid) {
  const age = Date.now() - certs.fetchedAt;
  const known = certs.keys?.some(k => k.kid === kid);
  if (certs.team !== team || !certs.keys || age > CERTS_MAX_AGE_MS || (!known && age > CERTS_MIN_REFETCH_MS)) {
    const res = await fetch(`https://${team}/cdn-cgi/access/certs`);
    if (!res.ok) throw new Error("could not load Access signing keys");
    certs = { keys: (await res.json()).keys, team, fetchedAt: Date.now() };
  }
  const jwk = certs.keys.find(k => k.kid === kid);
  if (!jwk) throw new Error("unknown signing key");
  return crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
}
