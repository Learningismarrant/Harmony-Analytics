/**
 * @jest-environment node
 *
 * Must use node environment: NextRequest requires the Web Fetch API
 * (globalThis.Request) which is available in Node 18+ but not in jsdom.
 *
 * Next.js middleware — auth guard unit tests
 *
 * We construct lightweight NextRequest stubs and assert on the response.
 * No real HTTP calls are made.
 */

import { middleware } from "./middleware";
import { NextRequest } from "next/server";

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeRequest(pathname: string, hasCookie = false): NextRequest {
  const url = `http://localhost${pathname}`;
  const headers = new Headers();
  if (hasCookie) headers.set("cookie", "harmony_session=1");
  return new NextRequest(url, { headers });
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("middleware", () => {
  describe("public paths — always pass through", () => {
    it.each([
      ["/login"],
      ["/register"],
      ["/invite/abc123"],
    ])("%s passes through without cookie", (path) => {
      const req = makeRequest(path, false);
      const res = middleware(req);
      // next() responses have no Location header
      expect(res.headers.get("Location")).toBeNull();
    });
  });

  describe("static / API routes — always pass through", () => {
    it.each([
      ["/_next/static/chunk.js"],
      ["/_next/image"],
      ["/api/auth/refresh"],
      ["/favicon.ico"],
    ])("%s passes through without cookie", (path) => {
      const req = makeRequest(path, false);
      const res = middleware(req);
      expect(res.headers.get("Location")).toBeNull();
    });
  });

  describe("protected routes — redirect when no cookie", () => {
    it("redirects /dashboard to /login?next=/dashboard", () => {
      const req = makeRequest("/dashboard", false);
      const res = middleware(req);
      const location = res.headers.get("Location");
      expect(location).toContain("/login");
      expect(location).toContain("next=%2Fdashboard");
    });

    it("redirects /vessel/5 to /login?next=/vessel/5", () => {
      const req = makeRequest("/vessel/5", false);
      const res = middleware(req);
      const location = res.headers.get("Location");
      expect(location).toContain("/login");
      expect(location).toContain("next=%2Fvessel%2F5");
    });
  });

  describe("protected routes — pass through with cookie", () => {
    it.each([["/dashboard"], ["/vessel/5"]])(
      "%s passes through when harmony_session cookie is present",
      (path) => {
        const req = makeRequest(path, true);
        const res = middleware(req);
        expect(res.headers.get("Location")).toBeNull();
      },
    );
  });
});
