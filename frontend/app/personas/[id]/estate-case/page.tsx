"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { type EstateCase, estateCaseConcept } from "../../../lib/api";

export default function EstateCasePage() {
  const params = useParams<{ id: string }>();
  const personaId = Number(params.id);

  const [estateCase, setEstateCase] = useState<EstateCase | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!Number.isFinite(personaId)) {
      return;
    }
    let active = true;

    async function loadConcept() {
      try {
        const loaded = await estateCaseConcept(personaId);
        if (active) {
          setEstateCase(loaded);
          setError(null);
        }
      } catch {
        if (active) {
          setError("Could not load the concept view. Is the backend running?");
        }
      }
    }

    void loadConcept();

    return () => {
      active = false;
    };
  }, [personaId]);

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900 font-sans selection:bg-blue-100 selection:text-blue-900">
      <div
        className="bg-blue-900 px-6 py-2.5 text-center text-xs font-bold uppercase tracking-[0.2em] text-white shadow-sm"
        role="note"
      >
        Concept Preview • Not a Live Integration
      </div>

      <header className="border-b border-slate-200 bg-white shadow-sm sticky top-0 z-10">
        <div className="mx-auto w-full max-w-5xl px-4 sm:px-6 lg:px-8 py-5">
          <Link href={`/personas/${personaId}`} className="group inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-blue-700 transition-colors">
            <svg className="h-4 w-4 transform transition-transform group-hover:-translate-x-1" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
            </svg>
            Back to Detection Results
          </Link>
          <div className="mt-3 flex items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
                Estate Settlement Concept
                <span className="inline-flex items-center rounded-md bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700 ring-1 ring-inset ring-blue-700/10">
                  Concept
                </span>
              </h1>
              <p className="mt-1 text-sm text-slate-500">
                An illustration of what an automated settlement checklist could look like.
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {error ? (
          <div role="alert" className="flex items-start gap-3 rounded-lg border-l-4 border-red-600 bg-red-50 p-4 shadow-sm ring-1 ring-inset ring-red-600/20">
            <svg className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <p className="text-sm font-medium text-red-800">{error}</p>
          </div>
        ) : null}

        {estateCase ? (
          <>
            <section className="rounded-xl border border-blue-200 bg-gradient-to-br from-blue-50 to-white p-6 shadow-sm ring-1 ring-inset ring-blue-600/10 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-8 opacity-5">
                <svg className="h-24 w-24 text-blue-900" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M11 17h2v-6h-2v6zm1-15C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zM11 9h2V7h-2v2z"/>
                </svg>
              </div>
              <h2 className="text-xs font-bold uppercase tracking-wider text-blue-900 flex items-center gap-2">
                <svg className="h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
                </svg>
                {estateCase.label}
              </h2>
              <p className="mt-3 text-sm leading-6 text-slate-700 relative z-10 max-w-3xl">{estateCase.notice}</p>
            </section>

            {estateCase.unresolved_conflicts > 0 ? (
              <div className="flex items-start gap-3 rounded-lg border-l-4 border-amber-500 bg-amber-50 p-4 shadow-sm">
                <svg className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <h3 className="text-sm font-bold text-amber-900">Pending Resolutions</h3>
                  <p className="mt-1 text-sm text-amber-800">
                    This persona still has <strong className="font-semibold">{estateCase.unresolved_conflicts} unresolved conflict(s)</strong>
                    {estateCase.readiness_score !== null ? ` and a readiness score of ${estateCase.readiness_score}` : ""}. 
                    The real product would require resolving these first; this illustration does not depend on them being fixed.
                  </p>
                </div>
              </div>
            ) : null}

            <section className="space-y-6" aria-labelledby="items-heading">
              <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                <h2 id="items-heading" className="text-sm font-bold uppercase tracking-wider text-slate-900">
                  Illustrative Process per Asset
                </h2>
                <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600">
                  {estateCase.items.length} assets
                </span>
              </div>

              <div className="grid gap-6 md:grid-cols-2">
                {estateCase.items.map((item) => (
                  <article
                    key={`${item.asset_type}-${item.asset_reference}`}
                    className="flex flex-col rounded-xl border border-slate-200 bg-white shadow-sm ring-1 ring-slate-900/5 transition-shadow hover:shadow-md"
                  >
                    <header className="border-b border-slate-100 bg-slate-50/50 p-5">
                      <div className="flex flex-wrap items-start justify-between gap-4">
                        <div>
                          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                            <span className="flex h-6 w-6 items-center justify-center rounded bg-slate-200">
                              <svg className="h-4 w-4 text-slate-600" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
                              </svg>
                            </span>
                            {item.institution_name}
                          </h3>
                          <p className="mt-1 flex items-center gap-2 text-xs font-medium text-slate-500">
                            <span className="uppercase tracking-wider">{item.asset_type_label}</span>
                          </p>
                        </div>
                        <span className="font-mono text-xs font-semibold text-slate-600 bg-white border border-slate-200 px-2 py-1 rounded shadow-sm">
                          {item.asset_reference}
                        </span>
                      </div>
                    </header>

                    <div className="flex-1 p-5">
                      <div className="mb-5 rounded-md bg-slate-50 p-3 text-sm border border-slate-100">
                        <p className="text-slate-700">
                          <strong className="font-semibold text-slate-900">Extracted Names:</strong> {item.named_people.join(", ") || "None"}
                        </p>
                        <p className={`mt-1 flex items-center gap-1.5 text-xs font-medium ${item.has_nomination_on_record ? 'text-emerald-700' : 'text-slate-500'}`}>
                          {item.has_nomination_on_record ? (
                            <>
                              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                              </svg>
                              Nomination record present
                            </>
                          ) : (
                            <>
                              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 12h-15" />
                              </svg>
                              No nomination record found
                            </>
                          )}
                        </p>
                      </div>

                      <div className="relative">
                        <p className="text-xs font-bold uppercase tracking-wider text-blue-800 mb-3 flex items-center gap-2">
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
                          </svg>
                          Checklist Steps
                        </p>
                        <ol className="space-y-3">
                          {item.illustrative_steps.map((step, index) => (
                            <li key={step} className="flex gap-3 text-sm text-slate-700">
                              <span className="flex-shrink-0 flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700">
                                {index + 1}
                              </span>
                              <span className="mt-0.5">{step}</span>
                            </li>
                          ))}
                        </ol>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </section>

            <div className="border-t border-slate-200 pt-8 mt-8">
              <p className="rounded-lg border border-red-200 bg-white p-4 text-xs leading-5 text-red-800 shadow-sm flex items-start gap-3 font-medium">
                <svg className="h-5 w-5 flex-shrink-0 text-red-600 mt-0.5" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                {estateCase.disclaimer}
              </p>
            </div>
          </>
        ) : null}
      </main>

      <footer className="mt-auto border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm font-medium text-slate-500">
            JeevanSetu © {new Date().getFullYear()}
          </p>
          <p className="text-xs text-slate-400 text-center sm:text-right max-w-sm">
            Concept illustration from synthetic records. No institution is connected. Not legal advice.
          </p>
        </div>
      </footer>
    </div>
  );
}
