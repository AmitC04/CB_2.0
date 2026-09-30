import { describe, expect, it } from "vitest";
import { authDecision, isHealthPath } from "./basicAuth";

const credentials = { user: "judge", password: "s3cret:with:colons" };

function header(user: string, password: string): string {
  return `Basic ${btoa(`${user}:${password}`)}`;
}

describe("authDecision", () => {
  it("stays out of the way when no credentials are configured locally", () => {
    expect(
      authDecision({
        header: null,
        user: undefined,
        password: undefined,
        publicDeployment: undefined,
      }),
    ).toBe("allow");
  });

  it("refuses to serve a public instance that has no credentials", () => {
    expect(
      authDecision({
        header: null,
        user: "",
        password: "",
        publicDeployment: "true",
      }),
    ).toBe("misconfigured");
  });

  it("accepts the configured credentials", () => {
    expect(
      authDecision({
        header: header(credentials.user, credentials.password),
        ...credentials,
        publicDeployment: "true",
      }),
    ).toBe("allow");
  });

  it("challenges a request with no credentials", () => {
    expect(
      authDecision({ header: null, ...credentials, publicDeployment: "true" }),
    ).toBe("challenge");
  });

  it("rejects a wrong password and a wrong user", () => {
    expect(
      authDecision({
        header: header(credentials.user, "wrong"),
        ...credentials,
        publicDeployment: "true",
      }),
    ).toBe("challenge");
    expect(
      authDecision({
        header: header("someone-else", credentials.password),
        ...credentials,
        publicDeployment: "true",
      }),
    ).toBe("challenge");
  });

  it("rejects a malformed or non-basic header instead of throwing", () => {
    for (const bad of ["Basic", "Bearer abc", "Basic !!!not-base64!!!", "", "Basic " + btoa("nocolon")]) {
      expect(
        authDecision({ header: bad, ...credentials, publicDeployment: "true" }),
      ).toBe("challenge");
    }
  });

  it("treats a password containing colons as one password", () => {
    expect(
      authDecision({
        header: header("judge", "s3cret:with:colons"),
        ...credentials,
        publicDeployment: "true",
      }),
    ).toBe("allow");
  });

  it("does not let a prefix of the password through", () => {
    expect(
      authDecision({
        header: header(credentials.user, "s3cret"),
        ...credentials,
        publicDeployment: "true",
      }),
    ).toBe("challenge");
  });
});


describe("isHealthPath", () => {
  it("exempts only the health probe, with or without a trailing slash", () => {
    expect(isHealthPath("/healthz")).toBe(true);
    expect(isHealthPath("/healthz/")).toBe(true);
  });

  it("does not exempt anything else, including lookalikes", () => {
    for (const path of [
      "/",
      "/personas/1",
      "/api/backend/personas",
      "/healthz/../personas/1",
      "/healthzz",
      "/a/healthz",
    ]) {
      expect(isHealthPath(path)).toBe(false);
    }
  });
});
