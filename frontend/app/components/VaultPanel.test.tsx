import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { VaultPanel } from "./VaultPanel";
import { makeDocument, makeField } from "./testFixtures";

function renderPanel(
  documents = [makeDocument()],
  overrides: {
    onSave?: (docId: number, fieldId: number, namedPerson: string) => Promise<void>;
    onUndo?: (docId: number, fieldId: number) => Promise<void>;
    busy?: boolean;
  } = {},
) {
  const onSave = overrides.onSave ?? vi.fn().mockResolvedValue(undefined);
  const onUndo = overrides.onUndo ?? vi.fn().mockResolvedValue(undefined);
  const onRerun = vi.fn().mockResolvedValue(undefined);
  render(
    <VaultPanel
      documents={documents}
      onSave={onSave}
      onUndo={onUndo}
      busy={overrides.busy ?? false}
    />,
  );
  return { onSave, onUndo, onRerun };
}

describe("VaultPanel", () => {
  it("states that edits touch only the synthetic extracted record", () => {
    renderPanel();

    expect(document.body.textContent).toContain("No uploaded document and no real institution record is modified");
  });

  it("sends a simulated fix with the edited value", async () => {
    const user = userEvent.setup();
    const { onSave } = renderPanel();

    await user.click(screen.getByRole("button", { name: "Simulate fix" }));
    const input = screen.getByLabelText(/Named person/i);
    await user.clear(input);
    await user.type(input, "Anika Demo-Mehta");
    await user.click(screen.getByRole("button", { name: "Save fix" }));

    expect(onSave).toHaveBeenCalledWith(10, 1, "Anika Demo-Mehta");
  });

  it("hides undo for a field that was never edited", () => {
    renderPanel();

    expect(screen.queryByRole("button", { name: "Undo fix" })).not.toBeInTheDocument();
  });

  it("reverts an edited field through the undo handler", async () => {
    const user = userEvent.setup();
    const { onUndo } = renderPanel([
      makeDocument({ fields: [makeField({ is_user_edited: true })] }),
    ]);

    await user.click(screen.getByRole("button", { name: "Undo fix" }));

    expect(onUndo).toHaveBeenCalledWith(10, 1);
  });

  it("keeps showing the originally extracted quote next to an edited value", () => {
    renderPanel([makeDocument({ fields: [makeField({ is_user_edited: true })] })]);

    expect(screen.getByText("Simulated Edit")).toBeInTheDocument();
    expect(document.body.textContent).toContain("Kavya Demo-Mehta");
    expect(document.body.textContent).toContain("Use \"Undo fix\" to restore it");
  });

  it("labels fallback seed data as not a live extraction", () => {
    renderPanel([makeDocument({ extraction_source: "manual_fallback", model_name: null })]);

    expect(document.body.textContent).toContain("Pre-verified fallback data");
  });

  it("names the model when the extraction was live", () => {
    renderPanel();

    expect(document.body.textContent).toContain("Extracted live by");
  });

  it("flags a joint holding as outside the documented rule scope", () => {
    renderPanel([makeDocument({ fields: [makeField({ holding_pattern: "joint" })] })]);

    expect(screen.getByText("Joint Holding (Out of Scope)")).toBeInTheDocument();
    expect(document.body.textContent).toContain("documented rules cover single-holder assets only");
  });

  it("does not flag scope for a single or unknown holding pattern", () => {
    renderPanel([makeDocument({ fields: [makeField({ holding_pattern: "unknown" })] })]);

    expect(
      screen.queryByText("Joint Holding (Out of Scope)"),
    ).not.toBeInTheDocument();
  });

  it("disables the actions while a request is in flight", () => {
    renderPanel([makeDocument({ fields: [makeField({ is_user_edited: true })] })], {
      busy: true,
    });

    expect(screen.getByRole("button", { name: "Undo fix" })).toBeDisabled();
  });
});
