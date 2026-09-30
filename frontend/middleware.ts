import { NextResponse, type NextRequest } from "next/server";
import { authDecision, isHealthPath } from "./app/lib/basicAuth";

/**
 * Gate every request, including the /api/backend proxy, behind one shared credential.
 *
 * Inert unless BASIC_AUTH_USER and BASIC_AUTH_PASSWORD are set, so the local demo is
 * unchanged. On a public instance (PUBLIC_DEPLOYMENT=true) with no credentials set, this
 * refuses to serve rather than quietly exposing the upload path. See docs/DEPLOYMENT.md.
 */
export function middleware(request: NextRequest) {
  // The platform health check must get a 2xx, so it cannot be gated.
  if (isHealthPath(request.nextUrl.pathname)) {
    return NextResponse.next();
  }

  const decision = authDecision({
    header: request.headers.get("authorization"),
    user: process.env.BASIC_AUTH_USER,
    password: process.env.BASIC_AUTH_PASSWORD,
    publicDeployment: process.env.PUBLIC_DEPLOYMENT,
  });

  if (decision === "allow") {
    return NextResponse.next();
  }

  if (decision === "misconfigured") {
    return new NextResponse(
      "This deployment is public but has no access credentials configured. Set " +
        "BASIC_AUTH_USER and BASIC_AUTH_PASSWORD, or take the instance off the internet. " +
        "See docs/DEPLOYMENT.md.",
      { status: 503, headers: { "content-type": "text/plain; charset=utf-8" } },
    );
  }

  return new NextResponse("Authentication required.", {
    status: 401,
    headers: {
      "www-authenticate": 'Basic realm="JeevanSetu demo", charset="UTF-8"',
      "content-type": "text/plain; charset=utf-8",
    },
  });
}

export const config = {
  // Everything except Next's own static output. The proxy route is deliberately included.
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
