import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { revokeSession } from "@/lib/active-sessions";

export async function POST(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;

  // Best-effort: also mark this real registry row revoked (see
  // lib/active-sessions.ts), so /sessions doesn't keep showing a
  // deliberately-logged-out session as "active" for the rest of its
  // natural 8h token lifetime. Never blocks the redirect below on this --
  // deleting the cookie is what actually matters for this response, and a
  // registry write failure here is no different from any other transient
  // registry outage (see middleware.ts's own fail-open handling).
  if (session?.sessionId) {
    revokeSession(session.sessionId, session.sub).catch(() => {
      // revokeSession never throws (failures come back as {ok:false}), so
      // this catch is defensive only.
    });
  }

  const response = NextResponse.redirect(new URL("/login", request.url));
  response.cookies.delete(SESSION_COOKIE_NAME);
  return response;
}
