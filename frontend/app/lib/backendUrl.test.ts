import { describe, expect, it } from "vitest";
import { LOCAL_BACKEND_URL, resolveBackendUrl } from "./backendUrl";

describe("resolveBackendUrl", () => {
  it("falls back to loopback when nothing is configured", () => {
    expect(resolveBackendUrl(undefined)).toBe(LOCAL_BACKEND_URL);
    expect(resolveBackendUrl("   ")).toBe(LOCAL_BACKEND_URL);
  });

  it("defaults a bare hostname to https, which is what Render supplies", () => {
    expect(resolveBackendUrl("jeevansetu-backend.onrender.com")).toBe(
      "https://jeevansetu-backend.onrender.com",
    );
  });

  it("respects an explicit scheme, so a private network can stay on http", () => {
    expect(resolveBackendUrl("http://js-be:10000")).toBe("http://js-be:10000");
    expect(resolveBackendUrl("https://api.example.com")).toBe("https://api.example.com");
  });

  it("strips trailing slashes so paths are not doubled", () => {
    expect(resolveBackendUrl("https://api.example.com///")).toBe("https://api.example.com");
  });
});
