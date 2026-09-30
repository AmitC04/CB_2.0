import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FindingCard } from "./FindingCard";
import { DISCLAIMER, makeFinding } from "./testFixtures";

describe("FindingCard", () => {
  it("always shows the disclaimer and the rule scope note", () => {
    render(<FindingCard finding={makeFinding()} />);

    expect(
      screen.getByText(new RegExp(DISCLAIMER.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))),
    ).toBeInTheDocument();
    expect(screen.getByText(/Documented rule scope note/)).toBeInTheDocument();
    expect(screen.getByText(/BANK-WILL-001/)).toBeInTheDocument();
  });

  it("quotes both sources with their locators", () => {
    render(<FindingCard finding={makeFinding()} />);

    expect(screen.getByText("Bank nomination")).toBeInTheDocument();
    expect(screen.getByText("Will")).toBeInTheDocument();
    expect(screen.getByText(/Kavya Demo-Mehta \(daughter\)/)).toBeInTheDocument();
    expect(screen.getByText(/Anika Demo-Mehta \(daughter\)/)).toBeInTheDocument();
  });

  it("falls back to the rule engine wording when the AI explanation is missing", () => {
    render(<FindingCard finding={makeFinding({ explanation: null })} />);

    expect(
      screen.getByText(/Plain-language wording is unavailable for this finding/),
    ).toBeInTheDocument();
  });

  it("shows the AI explanation when one is available", () => {
    render(
      <FindingCard
        finding={makeFinding({
          explanation: "Two documents name different people for the same account.",
          explanation_source: "gemini",
        })}
      />,
    );

    expect(
      screen.getByText("Two documents name different people for the same account."),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/Plain-language wording is unavailable/),
    ).not.toBeInTheDocument();
  });

  it("labels a scope gap as manual review, not a conflict, with no fallback notice", () => {
    render(
      <FindingCard
        finding={makeFinding({
          rule_id: "GAP-JOINT-HOLDING",
          finding_type: "scope_gap",
          severity: "low",
          summary: "This asset is held jointly, which the documented rules do not cover.",
          source_b: null,
          explanation: null,
        })}
      />,
    );

    expect(screen.getByText("Manual review required")).toBeInTheDocument();
    expect(screen.queryByText("Review conflict")).not.toBeInTheDocument();
    expect(screen.queryByText(/Source B/)).not.toBeInTheDocument();
    expect(
      screen.queryByText(/Plain-language wording is unavailable/),
    ).not.toBeInTheDocument();
  });
});

