/**
 * Resolve the backend base URL used by the server-side proxy route.
 *
 * Render's blueprint supplies a service host with no scheme, so a bare hostname defaults
 * to https rather than failing later with an opaque fetch error. An explicit scheme is
 * always respected, which is what the local rehearsal and a private network use.
 */
export const LOCAL_BACKEND_URL = "http://127.0.0.1:8000";

export function resolveBackendUrl(raw: string | undefined): string {
  const configured = (raw ?? "").trim();
  if (!configured) {
    return LOCAL_BACKEND_URL;
  }
  const withScheme = /^https?:\/\//i.test(configured)
    ? configured
    : `https://${configured}`;
  return withScheme.replace(/\/+$/, "");
}
