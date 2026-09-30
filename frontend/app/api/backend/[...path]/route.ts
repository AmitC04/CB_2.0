/**
 * Server-side proxy to the JeevanSetu API, used for hosted deployments only.
 *
 * The local demo talks to the backend directly (NEXT_PUBLIC_API_URL=http://localhost:8000).
 * For a hosted deployment, set NEXT_PUBLIC_API_URL=/api/backend so browser calls land here,
 * and set BACKEND_URL plus API_TOKEN as server-only variables. The token is attached here
 * and is never sent to the browser. See docs/DEPLOYMENT.md.
 */

import { resolveBackendUrl } from "../../../lib/backendUrl";

const API_TOKEN = process.env.API_TOKEN ?? "";
const BACKEND_URL = resolveBackendUrl(process.env.BACKEND_URL);

function targetUrl(request: Request, segments: string[]): string {
  const query = new URL(request.url).search;
  const path = segments.map(encodeURIComponent).join("/");
  return `${BACKEND_URL}/${path}${query}`;
}

async function forward(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  // Only GET, POST and PATCH are exported below, so Next.js answers anything else with 405.
  const { path } = await context.params;
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) {
    headers.set("content-type", contentType);
  }
  if (API_TOKEN) {
    headers.set("authorization", `Bearer ${API_TOKEN}`);
  }

  let upstream: Response;
  try {
    upstream = await fetch(targetUrl(request, path), {
      method: request.method,
      headers,
      body: request.method === "GET" ? undefined : await request.arrayBuffer(),
      cache: "no-store",
    });
  } catch {
    return Response.json(
      {
        code: "backend_unreachable",
        message: "The API could not be reached. Stored synthetic records were not changed.",
      },
      { status: 502 },
    );
  }

  const responseHeaders = new Headers();
  const upstreamType = upstream.headers.get("content-type");
  if (upstreamType) {
    responseHeaders.set("content-type", upstreamType);
  }
  responseHeaders.set("cache-control", "no-store");

  return new Response(await upstream.arrayBuffer(), {
    status: upstream.status,
    headers: responseHeaders,
  });
}

export const GET = forward;
export const POST = forward;
export const PATCH = forward;
export const dynamic = "force-dynamic";
