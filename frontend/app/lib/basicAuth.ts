/**
 * Access control for a hosted deployment.
 *
 * The backend's API_TOKEN gate stops anyone calling the API directly, but the proxy route
 * at /api/backend relays whatever reaches it. Without something in front of the frontend,
 * a published instance is still an open upload endpoint. This is that something: one
 * shared username and password, checked on every request including the proxy.
 *
 * It is not user authentication. There are no accounts. It exists so a demo URL can be
 * shared with judges without leaving the upload path open to the internet.
 */

export type AuthDecision = "allow" | "challenge" | "misconfigured";

/**
 * The one path that must answer without a credential.
 *
 * A platform health check needs a 2xx. If it were gated it would receive 401 and the
 * deploy would never go live. The route returns a fixed string and touches nothing.
 */
export function isHealthPath(pathname: string): boolean {
  return pathname === "/healthz" || pathname === "/healthz/";
}

export type AuthInput = {
  /** The raw Authorization header, if the request carried one. */
  header: string | null;
  user: string | undefined;
  password: string | undefined;
  /** "true" when the instance is reachable from the internet. Set by render.yaml. */
  publicDeployment: string | undefined;
};

/** Length-independent comparison, so a wrong password cannot be found byte by byte. */
function constantTimeEquals(a: string, b: string): boolean {
  const encoder = new TextEncoder();
  const left = encoder.encode(a);
  const right = encoder.encode(b);
  // Comparing lengths directly would leak them, so fold the length into the result.
  let mismatch = left.length ^ right.length;
  const length = Math.max(left.length, right.length);
  for (let index = 0; index < length; index += 1) {
    mismatch |= (left[index] ?? 0) ^ (right[index] ?? 0);
  }
  return mismatch === 0;
}

function decodeBasic(header: string): string | null {
  const [scheme, encoded] = header.split(" ");
  if (!encoded || scheme.toLowerCase() !== "basic") {
    return null;
  }
  try {
    return atob(encoded.trim());
  } catch {
    return null;
  }
}

/**
 * Decide what to do with one request.
 *
 * - `allow`: credentials are not configured for a private instance, or they matched.
 * - `challenge`: credentials are configured and the request did not satisfy them.
 * - `misconfigured`: the instance is public but has no credentials. Fails closed on
 *   purpose: a deployment that forgot to set them must not silently serve traffic.
 */
export function authDecision({
  header,
  user,
  password,
  publicDeployment,
}: AuthInput): AuthDecision {
  const configuredUser = (user ?? "").trim();
  const configuredPassword = password ?? "";

  if (!configuredUser || !configuredPassword) {
    return publicDeployment === "true" ? "misconfigured" : "allow";
  }

  const presented = header ? decodeBasic(header) : null;
  if (presented === null) {
    return "challenge";
  }

  // Only the first colon separates the two, because a password may contain one.
  const separator = presented.indexOf(":");
  if (separator === -1) {
    return "challenge";
  }
  const presentedUser = presented.slice(0, separator);
  const presentedPassword = presented.slice(separator + 1);

  const userMatches = constantTimeEquals(presentedUser, configuredUser);
  const passwordMatches = constantTimeEquals(presentedPassword, configuredPassword);
  return userMatches && passwordMatches ? "allow" : "challenge";
}
