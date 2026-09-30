import { useState } from "react";
import type { DocumentRecord, ExtractedField } from "../lib/api";

function FieldRow({
  field,
  onSave,
  onUndo,
  busy,
}: {
  field: ExtractedField;
  onSave: (fieldId: number, namedPerson: string) => Promise<void>;
  onUndo: (fieldId: number) => Promise<void>;
  busy: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(field.named_person);
  const inputId = `field-${field.id}-person`;

  async function save() {
    try {
      await onSave(field.id, value.trim());
      setEditing(false);
    } catch {
      // Keep the editor open so the unsaved value is not lost.
    }
  }

  return (
    <li className="rounded-xl border border-white/60 bg-white/50 p-4 shadow-sm backdrop-blur-sm transition-all hover:shadow-md hover:-translate-y-0.5">
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <span className="font-mono text-[10px] font-bold text-gov-navy bg-white border border-slate-200/60 px-2 py-0.5 rounded shadow-sm tracking-widest uppercase">
          {field.asset_reference}
        </span>
        <span className="text-slate-300">|</span>
        <span className="text-slate-500 uppercase tracking-widest text-[9px] font-bold">
          {field.mechanism_type}
        </span>
        {field.holding_pattern === "joint" ? (
          <span className="rounded bg-gov-saffron/10 px-2 py-0.5 text-[9px] font-bold text-gov-saffron uppercase tracking-widest ml-auto border border-gov-saffron/20">
            Joint Holding (Out of Scope)
          </span>
        ) : null}
        {field.is_user_edited ? (
          <span className="rounded bg-gov-blue/10 px-2 py-0.5 text-[9px] font-bold text-gov-blue uppercase tracking-widest ml-auto border border-gov-blue/20">
            Simulated Edit
          </span>
        ) : null}
      </div>

      {editing ? (
        <div className="mt-3 flex flex-wrap items-end gap-3 rounded-lg bg-white/80 p-4 border border-gov-blue/30 shadow-sm relative">
          <div className="absolute top-0 left-0 w-1 h-full bg-gov-blue rounded-l-lg" />
          <div className="flex-1 min-w-[200px]">
            <label className="block text-[10px] font-bold uppercase tracking-widest text-gov-navy" htmlFor={inputId}>
              Named person (Simulation)
            </label>
            <input
              id={inputId}
              className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-800 font-medium focus:border-gov-blue focus:ring-1 focus:ring-gov-blue outline-none transition-shadow"
              value={value}
              onChange={(event) => setValue(event.target.value)}
              placeholder="Enter name to simulate..."
            />
          </div>
          <button
            type="button"
            className="rounded-md bg-gov-blue px-4 py-2 text-sm font-bold text-white transition-all hover:bg-gov-true-blue hover:shadow-md disabled:opacity-50"
            onClick={() => void save()}
            disabled={busy || !value.trim()}
          >
            Save fix
          </button>
          <button
            type="button"
            className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-bold text-slate-600 hover:bg-slate-50 disabled:opacity-50 transition-colors"
            onClick={() => {
              setValue(field.named_person);
              setEditing(false);
            }}
            disabled={busy}
          >
            Cancel
          </button>
        </div>
      ) : (
        <div className="mt-2 flex flex-wrap items-center justify-between gap-3 rounded-lg bg-white/60 p-3 border border-slate-100/50">
          <p className="text-sm font-bold text-gov-navy">
            {field.named_person}
            <span className="text-[11px] font-medium text-slate-500 ml-2 bg-slate-100/80 px-2 py-0.5 rounded-full">{field.relationship}</span>
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              className="rounded bg-white border border-slate-200 px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest text-slate-600 transition-colors hover:bg-slate-50 hover:text-gov-blue disabled:opacity-50 shadow-sm"
              onClick={() => setEditing(true)}
              disabled={busy}
            >
              Simulate fix
            </button>
            {field.is_user_edited ? (
              <button
                type="button"
                className="rounded bg-white border border-red-200 px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest text-red-600 transition-colors hover:bg-red-50 disabled:opacity-50 shadow-sm flex items-center gap-1"
                onClick={() => void onUndo(field.id)}
                disabled={busy}
              >
                <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3" />
                </svg>
                Undo fix
              </button>
            ) : null}
          </div>
        </div>
      )}
      
      {field.is_user_edited ? (
        <div className="mt-3 text-[10px] text-slate-500 bg-blue-50/50 p-2 rounded border border-blue-100 italic leading-relaxed font-serif">
          Extracted: &quot;{field.source_text}&quot;. Use &quot;Undo fix&quot; to restore it. No uploaded document and no real institution record is modified.
        </div>
      ) : field.source_text ? (
        <div className="mt-3 text-[10px] text-slate-500 bg-slate-50/50 p-2 rounded border border-slate-100 italic leading-relaxed font-serif">
          Extracted: &quot;{field.source_text}&quot;
        </div>
      ) : null}
      
      {field.holding_pattern === "joint" ? (
        <div className="mt-2 text-[10px] text-amber-600 bg-amber-50 p-2 rounded border border-amber-100 italic leading-relaxed">
          Note: The documented rules cover single-holder assets only. Joint holdings may not be fully analyzed.
        </div>
      ) : null}
    </li>
  );
}

function DocumentItem({
  document,
  onSave,
  onUndo,
  busy,
}: {
  document: DocumentRecord;
  onSave: (docId: number, fieldId: number, value: string) => Promise<void>;
  onUndo: (docId: number, fieldId: number) => Promise<void>;
  busy: boolean;
}) {
  const [open, setOpen] = useState(true);
  const fields = document.fields ?? [];

  return (
    <div className="rounded-xl border border-white/60 bg-white/40 shadow-sm backdrop-blur-md overflow-hidden transition-all hover:shadow-md">
      <button
        type="button"
        className="flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-white/60 focus:outline-none focus-visible:bg-white/60"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <div className="flex items-center gap-3">
          <div className={`flex h-8 w-8 items-center justify-center rounded-lg transition-colors ${open ? 'bg-gov-blue text-white' : 'bg-gov-blue/10 text-gov-blue'}`}>
            <svg
              className={`h-4 w-4 transform transition-transform duration-300 ${
                open ? "rotate-180" : ""
              }`}
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth="2.5"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
            </svg>
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-bold text-gov-navy">{document.original_filename}</span>
            <div className="mt-1 flex items-center gap-2">
              <span className="rounded bg-slate-200/80 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-widest text-slate-600">
                {document.document_type}
              </span>
              {fields.length > 0 ? (
                <span className="rounded bg-gov-green/10 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-widest text-gov-green border border-gov-green/20">
                  Extracted
                </span>
              ) : null}
            </div>
          </div>
        </div>
        <div className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-widest">
          {document.document_date ? new Date(document.document_date).toISOString().slice(0, 10) : ''}
        </div>
      </button>

      {open && (
        <div className="border-t border-slate-200/50 bg-slate-50/30 p-4">
          {!document.model_name ? (
            <div className="mb-5 flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50/80 p-3 shadow-sm backdrop-blur-sm">
              <svg className="h-4 w-4 text-amber-500 mt-0.5" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <p className="text-[11px] font-medium leading-relaxed text-amber-800">
                Pre-verified fallback data, not a live AI extraction. Re-seed in live mode to
                extract this document with the model.
              </p>
            </div>
          ) : (
            <div className="mb-5 flex items-start gap-3 rounded-lg border border-gov-blue/20 bg-gov-blue/5 p-3 shadow-sm backdrop-blur-sm">
              <p className="text-[11px] font-medium leading-relaxed text-slate-700">
                Extracted live by <span className="font-bold">{document.model_name}</span>.
              </p>
            </div>
          )}

          {fields.length === 0 ? (
            <div className="rounded-lg border border-dashed border-slate-300 p-6 text-center">
              <p className="text-[11px] font-bold uppercase tracking-widest text-slate-500">
                No fields extracted
              </p>
            </div>
          ) : (
            <ul className="space-y-4">
              {fields.map((field) => (
                <FieldRow
                  key={field.id}
                  field={field}
                  onSave={(_, val) => onSave(document.id, field.id, val)}
                  onUndo={() => onUndo(document.id, field.id)}
                  busy={busy}
                />
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

export function VaultPanel({
  documents,
  onSave,
  onUndo,
  busy = false,
}: {
  documents: DocumentRecord[];
  onSave: (docId: number, fieldId: number, value: string) => Promise<void>;
  onUndo: (docId: number, fieldId: number) => Promise<void>;
  busy?: boolean;
}) {
  return (
    <section 
      className="rounded-2xl glass-panel p-6 shadow-sm relative overflow-hidden flex flex-col h-full" 
      aria-labelledby="vault-heading"
    >
      <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
        <svg className="w-32 h-32" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2L2 7l10 5 10-5-10-5zm0 18l-10-5v2l10 5 10-5v-2l-10 5z" />
        </svg>
      </div>

      <header className="mb-8 border-b border-slate-200/50 pb-4 relative z-10">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gov-navy text-white shadow-md">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
            </svg>
          </div>
          <div>
            <h2 id="vault-heading" className="text-sm font-bold uppercase tracking-widest text-gov-navy">
              Secure Document Vault
            </h2>
            <p className="mt-1 text-xs font-medium text-slate-500">
              {documents.length} synthetic documents securely processed
            </p>
          </div>
        </div>
      </header>

      <div className="flex-grow">
        {documents.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 p-12 text-center bg-white/30 backdrop-blur-sm relative z-10">
            <p className="text-[11px] font-bold uppercase tracking-widest text-slate-500">
              No documents uploaded
            </p>
          </div>
        ) : (
          <div className="space-y-4 relative z-10">
            {documents.map((doc) => (
              <DocumentItem
                key={doc.id}
                document={doc}
                onSave={onSave}
                onUndo={onUndo}
                busy={busy}
              />
            ))}
          </div>
        )}
      </div>
      
      <div className="mt-8 pt-4 border-t border-slate-200/50 text-center relative z-10">
        <p className="text-[10px] text-slate-400 font-medium tracking-wide">
          No uploaded document and no real institution record is modified by simulations.
        </p>
      </div>
    </section>
  );
}
