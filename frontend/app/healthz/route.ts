/**
 * Liveness probe for the platform, deliberately outside the credential gate.
 *
 * Render requires a 2xx from its health check path. Every other path is behind Basic
 * auth, which answers 401, so a gated path can never pass a health check and the deploy
 * would hang forever. This returns a fixed string and reads nothing: no database, no
 * backend call, no document data, nothing worth authenticating.
 */
export function GET() {
  return new Response("ok", {
    status: 200,
    headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" },
  });
}

export const dynamic = "force-dynamic";
