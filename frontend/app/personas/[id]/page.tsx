"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { FindingCard } from "../../components/FindingCard";
import { ScoreCard } from "../../components/ScoreCard";
import { VaultPanel } from "../../components/VaultPanel";
import { Header } from "../../components/Header";
import {
  type DetectionRun,
  type DocumentRecord,
  type Persona,
  type Finding,
  latestDetection,
  listDocuments,
  listPersonas,
  runDetection,
  undoField,
  updateField,
} from "../../lib/api";

type PersonaState = {
  persona: Persona | null;
  documents: DocumentRecord[];
  run: DetectionRun | null;
};

async function fetchPersonaState(personaId: number): Promise<PersonaState> {
  const [{ personas }, { documents }] = await Promise.all([
    listPersonas(),
    listDocuments(personaId),
  ]);
  let run: DetectionRun | null = null;
  try {
    run = await latestDetection(personaId);
  } catch {
    run = null;
  }
  return {
    persona: personas.find((item) => item.id === personaId) ?? null,
    documents,
    run,
  };
}

export default function PersonaPage() {
  const params = useParams<{ id: string }>();
  const personaId = Number(params.id);

  const [persona, setPersona] = useState<Persona | null>(null);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);

  const [run, setRun] = useState<DetectionRun | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [stale, setStale] = useState(false);

  useEffect(() => {
    if (!Number.isFinite(personaId)) {
      return;
    }
    let active = true;

    async function loadPersona() {
      try {
        const state = await fetchPersonaState(personaId);
        if (!active) {
          return;
        }
        setPersona(state.persona);
        setDocuments(state.documents);
        setRun(state.run);
        setError(null);
      } catch {
        if (active) {
          setError("Could not load this persona. Is the backend running?");
        }
      }
    }

    void loadPersona();

    return () => {
      active = false;
    };
  }, [personaId]);

  async function handleRerun() {
    setBusy(true);
    setError(null);
    setNotice(null);
    const previous = run?.readiness_score ?? null;
    try {
      const next = await runDetection(personaId);
      setRun(next);
      setStale(false);
      const current = next.readiness_score;
      if (previous !== null && current !== null && current > previous) {
        setNotice(`Score improved from ${previous} to ${current}.`);
      } else if (previous !== null && current !== null && current < previous) {
        setNotice(`Score decreased from ${previous} to ${current}.`);
      } else {
        setNotice("Re-run complete. Score is unchanged.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleSave(
    documentId: number,
    fieldId: number,
    value: string,
  ) {
    setBusy(true);
    setError(null);
    try {
      await updateField(fieldId, value);
      const nextDocs = await listDocuments(personaId);
      setDocuments(nextDocs.documents);
      setStale(true);
      setNotice("Simulated fix applied to document.");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleUndo(documentId: number, fieldId: number) {
    setBusy(true);
    setError(null);
    try {
      await undoField(fieldId);
      const nextDocs = await listDocuments(personaId);
      setDocuments(nextDocs.documents);
      setStale(true);
      setNotice("Undo complete. Reverted field to extracted version.");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  const conflicts = run?.conflicts ?? [];
  const gaps = run?.scope_gaps ?? [];

  return (
    <div className="flex min-h-screen flex-col selection:bg-gov-saffron/30 selection:text-gov-navy">
      <Header />

      <main className="mx-auto w-full max-w-7xl flex-grow px-6 lg:px-8 py-8">
        
        {/* PAGE HEADER */}
        <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="flex items-center justify-center rounded-full glass-panel p-2.5 text-slate-500 transition-colors hover:text-gov-navy shadow-sm"
              aria-label="Back to home"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
              </svg>
            </Link>
            
            <div className="flex items-center gap-4">
              <div>
                <h1 className="text-2xl font-black tracking-tight text-gov-navy flex items-center gap-3">
                  {persona ? persona.name : "Loading..."}
                  <span className="rounded glass-panel border-gov-blue/20 bg-gov-blue/5 px-2 py-0.5 text-[10px] font-bold text-gov-blue uppercase tracking-wider">
                    Demo ID: {personaId}
                  </span>
                </h1>
                <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mt-1">
                  Rules Version: {run?.rules_version ?? "Pending"}
                </p>
              </div>
            </div>
          </div>
          
          <button
            onClick={() => void handleRerun()}
            disabled={busy}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-gov-blue px-6 py-2.5 text-sm font-bold text-white shadow-md shadow-gov-blue/20 transition-all hover:bg-gov-true-blue hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-gov-blue focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 active:scale-95 w-full md:w-auto"
          >
            {busy ? (
              <>
                <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing...
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
                </svg>
                Re-run Analysis
              </>
            )}
          </button>
        </div>

        {error ? (
          <div className="mb-8 rounded-xl glass-panel border-l-4 border-l-red-500 p-5 shadow-sm relative overflow-hidden">
            <div className="flex">
              <svg className="h-6 w-6 text-red-500" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div className="ml-4">
                <h3 className="text-sm font-bold text-red-900 uppercase tracking-widest">System Error</h3>
                <p className="mt-1 text-sm font-medium text-red-800">{error}</p>
              </div>
            </div>
          </div>
        ) : null}

        {notice ? (
          <div className="mb-8 rounded-xl glass-panel border-l-4 border-l-gov-blue p-5 shadow-sm relative overflow-hidden">
            <div className="flex">
              <svg className="h-6 w-6 text-gov-blue" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
              </svg>
              <div className="ml-4">
                <h3 className="text-sm font-bold text-gov-navy uppercase tracking-widest">Notice</h3>
                <p className="mt-1 text-sm font-medium text-slate-700">{notice}</p>
              </div>
            </div>
          </div>
        ) : null}

        {run ? (
          <ScoreCard run={run} stale={stale} />
        ) : (
          <section className="rounded-2xl glass-panel p-16 text-center shadow-sm mb-8 border-dashed border-2 border-slate-300">
            <div className="mx-auto w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
              <svg className="h-8 w-8 text-slate-400" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m5.231 13.481L15 17.25m-4.5-15H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
            </div>
            <h3 className="mt-4 text-xl font-bold text-gov-navy">No Analysis Record Found</h3>
            <p className="mt-2 text-sm font-medium text-slate-500 max-w-lg mx-auto">
              Execute &quot;Re-run Analysis&quot; to evaluate the uploaded synthetic documents against the deterministic rule set.
            </p>
          </section>
        )}

        <div className="grid gap-8 lg:grid-cols-3 mt-8">
          
          {/* MAIN CONTENT AREA - CONFLICTS (65%) */}
          <div className="lg:col-span-2 space-y-10">
            
            {/* HIGH CONFLICTS */}
            <section aria-labelledby="conflicts-heading">
              <div className="flex items-center justify-between border-b border-slate-200/50 pb-4 mb-6">
                <h2 id="conflicts-heading" className="text-lg font-bold text-gov-navy tracking-tight flex items-center gap-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-100 text-red-600 shadow-sm border border-red-200">
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </span>
                  Identified Conflicts
                </h2>
                <span className="inline-flex items-center rounded-full glass-panel px-3 py-1 text-[10px] font-bold text-slate-700 uppercase tracking-widest shadow-sm">
                  {conflicts.length} critical items
                </span>
              </div>
              
              {run && conflicts.length === 0 ? (
                <div className="rounded-xl glass-panel p-8 text-center shadow-sm">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-gov-green/10">
                    <svg className="h-6 w-6 text-gov-green" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="mt-4 text-base font-bold text-gov-navy">No High-Priority Conflicts</h3>
                  <p className="mt-2 text-sm font-medium text-slate-500 max-w-md mx-auto">
                    The deterministic engine found no high-priority conflicting records in the current document set.
                  </p>
                </div>
              ) : null}
              
              <div className="space-y-6">
                {conflicts.map((finding: Finding) => (
                  <FindingCard key={finding.id} finding={finding} />
                ))}
              </div>
            </section>

            {/* REVIEW GAPS */}
            {gaps.length > 0 ? (
              <section aria-labelledby="gaps-heading">
                <div className="flex items-center justify-between border-b border-slate-200/50 pb-4 mb-6">
                  <h2 id="gaps-heading" className="text-lg font-bold text-gov-navy tracking-tight flex items-center gap-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gov-saffron/10 text-gov-saffron shadow-sm border border-gov-saffron/20">
                      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m5.231 13.481L15 17.25m-4.5-15H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                      </svg>
                    </span>
                    Manual Review Required
                  </h2>
                  <span className="inline-flex items-center rounded-full glass-panel px-3 py-1 text-[10px] font-bold text-slate-700 uppercase tracking-widest shadow-sm">
                    {gaps.length} pending items
                  </span>
                </div>
                <div className="space-y-6">
                  {gaps.map((finding: Finding) => (
                    <FindingCard key={finding.id} finding={finding} />
                  ))}
                </div>
              </section>
            ) : null}
          </div>

          {/* RIGHT SIDEBAR - VAULT (35%) */}
          <div className="space-y-8">
            <VaultPanel
              documents={documents}
              onSave={handleSave}
              onUndo={handleUndo}
              busy={busy}
            />

            <section className="rounded-2xl glass-panel p-6 shadow-sm relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-5">
                <svg className="w-24 h-24" fill="currentColor" viewBox="0 0 24 24"><path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
              </div>
              <div className="relative z-10">
                <div className="flex items-center gap-3 mb-4">
                  <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-gov-blue/10 text-gov-blue">
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                    </svg>
                  </span>
                  <h3 className="text-sm font-bold text-gov-navy uppercase tracking-widest">
                    Concept Preview
                  </h3>
                </div>
                <p className="text-sm leading-relaxed text-slate-600 font-medium">
                  A separate illustration shows what a per-institution settlement checklist could
                  look like in future implementations.
                </p>
                <Link
                  href={`/personas/${personaId}/estate-case`}
                  className="mt-6 inline-flex items-center justify-center w-full rounded-lg bg-white border border-gov-blue/20 px-4 py-3 text-sm font-bold text-gov-blue shadow-sm hover:bg-gov-blue/5 transition-colors group"
                >
                  View the concept
                  <svg className="ml-2 h-4 w-4 transform transition-transform group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                  </svg>
                </Link>
              </div>
            </section>
          </div>
        </div>
      </main>

      <footer className="mt-auto border-t border-white/40 glass-panel">
        <div className="mx-auto max-w-7xl px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div>
              <p className="text-sm font-bold text-gov-navy">
                JeevanSetu
              </p>
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mt-1">
                Continuity starts before a crisis
              </p>
            </div>
            
            <div className="text-center md:text-right">
              <p className="text-xs font-semibold text-slate-600">
                {run?.disclaimer ?? "Synthetic demonstration environment"}
              </p>
              <p className="text-[10px] text-slate-500 mt-1">
                Results are informational and require professional review. Not legal advice.
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
