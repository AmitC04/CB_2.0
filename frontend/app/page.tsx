"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Header } from "./components/Header";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface Persona {
  id: string;
  name: string;
  description: string;
  created_at: string;
}

export default function Home() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadPersonas() {
      try {
        const res = await fetch(`${API_URL}/personas`, {
          cache: "no-store",
        });
        if (!res.ok) throw new Error("Failed to load personas");
        const data = await res.json();
        setPersonas(data.personas ?? []);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    }
    void loadPersonas();
  }, []);

  return (
    <div className="flex min-h-screen flex-col selection:bg-gov-saffron/30 selection:text-gov-navy">
      <Header />

      <main className="flex-grow">
        {/* HERO SECTION */}
        <section className="relative overflow-hidden py-16 sm:py-24 lg:py-32">
          {/* Subtle background abstract shapes */}
          <div className="absolute inset-0 z-0">
            <div className="absolute -top-[20%] -right-[10%] w-[60%] h-[60%] rounded-full bg-gov-saffron/5 blur-[120px]" />
            <div className="absolute top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-gov-blue/5 blur-[100px]" />
          </div>

          <div className="relative z-10 mx-auto max-w-7xl px-6 lg:px-8">
            <div className="flex flex-col lg:flex-row items-center gap-16">
              
              {/* Left Content */}
              <div className="flex-1 text-center lg:text-left">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass-panel border-gov-saffron/30 text-gov-saffron text-xs font-bold tracking-widest uppercase mb-6 shadow-sm">
                  <span className="w-2 h-2 rounded-full bg-gov-saffron animate-pulse" />
                  Official Demo Environment
                </div>
                
                <h2 className="text-4xl font-black tracking-tight text-gov-navy sm:text-6xl lg:text-[4rem] lg:leading-[1.1]">
                  Proactive estate conflict resolution for digital continuity.
                </h2>
                <p className="mt-6 text-lg leading-relaxed text-slate-600 max-w-2xl mx-auto lg:mx-0 font-medium">
                  Wills, nominations, and beneficiary forms are compared against a documented,
                  India-scoped rule set. Conflict decisions are deterministic Python; AI is used only
                  to extract fields and to reword findings.
                </p>
              </div>

              {/* Right Abstract Visual */}
              <div className="flex-1 w-full max-w-lg lg:max-w-none relative">
                <div className="relative w-full aspect-square md:aspect-[4/3] rounded-2xl overflow-hidden glass-panel border border-white/60 p-6 flex items-center justify-center shadow-2xl shadow-gov-navy/5">
                  <div className="absolute inset-0 bg-gradient-to-br from-white/40 to-white/10" />
                  
                  {/* Abstract Document Architecture Visualization */}
                  <div className="relative w-full h-full flex flex-col items-center justify-center gap-6 opacity-90">
                    <div className="w-3/4 h-24 rounded-xl glass-panel border-white/80 shadow-lg transform -rotate-6 translate-y-4 hover:rotate-0 transition-transform duration-700 ease-out flex items-center p-4 gap-4">
                      <div className="w-10 h-10 rounded bg-gov-blue/10 flex items-center justify-center">
                        <svg className="w-5 h-5 text-gov-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
                      </div>
                      <div className="flex-1 space-y-2">
                        <div className="h-2 bg-slate-200 rounded w-1/3" />
                        <div className="h-2 bg-slate-100 rounded w-3/4" />
                      </div>
                    </div>
                    
                    <div className="w-3/4 h-24 rounded-xl glass-panel border-white/80 shadow-lg transform rotate-3 -translate-y-4 hover:rotate-0 transition-transform duration-700 ease-out flex items-center p-4 gap-4 z-10 backdrop-blur-xl bg-white/80">
                      <div className="w-10 h-10 rounded bg-gov-green/10 flex items-center justify-center">
                        <svg className="w-5 h-5 text-gov-green" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                      </div>
                      <div className="flex-1 space-y-2">
                        <div className="h-2 bg-slate-200 rounded w-1/2" />
                        <div className="h-2 bg-slate-100 rounded w-5/6" />
                      </div>
                      <div className="w-8 h-8 rounded-full border-2 border-gov-saffron/30 flex items-center justify-center">
                        <div className="w-3 h-3 rounded-full bg-gov-saffron" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </section>

        {/* TRUST STRIP */}
        <section className="border-y border-white/40 bg-white/40 backdrop-blur-md">
          <div className="mx-auto max-w-7xl px-6 lg:px-8 py-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center text-sm font-semibold text-slate-600 uppercase tracking-wider">
              <div className="flex flex-col items-center gap-2">
                <svg className="w-6 h-6 text-gov-blue opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
                Secure document processing
              </div>
              <div className="flex flex-col items-center gap-2">
                <svg className="w-6 h-6 text-gov-saffron opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9"/></svg>
                India-scoped rule engine
              </div>
              <div className="flex flex-col items-center gap-2">
                <svg className="w-6 h-6 text-gov-navy opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/></svg>
                Deterministic conflict detection
              </div>
              <div className="flex flex-col items-center gap-2">
                <svg className="w-6 h-6 text-gov-green opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
                Professional review required
              </div>
            </div>
          </div>
        </section>

        {/* MAIN CONTENT AREA */}
        <div className="mx-auto max-w-7xl px-6 lg:px-8 py-16">
          
          {/* IMPORTANT NOTICE */}
          <div className="glass-panel rounded-2xl border-l-4 border-l-gov-saffron p-6 shadow-md mb-16 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-5">
              <svg className="w-24 h-24" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L1 21h22M12 6l7.53 13H4.47M11 10v4h2v-4m-2 6v2h2v-2"/></svg>
            </div>
            <div className="sm:flex sm:items-start gap-5 relative z-10">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gov-saffron/10 text-gov-saffron border border-gov-saffron/20 hidden sm:flex">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-widest">Important Notice</h3>
                <p className="mt-2 text-sm text-slate-700 leading-relaxed max-w-4xl">
                  This system processes <strong className="font-semibold text-slate-900">synthetic demo documents only</strong>. Results are informational, are not legal advice, and require professional review.
                </p>
              </div>
            </div>
          </div>

          {/* PERSONAS SECTION */}
          <section aria-labelledby="personas-heading">
            <div className="flex items-end justify-between border-b border-slate-200/60 pb-6 mb-8">
              <div>
                <h3 id="personas-heading" className="text-2xl font-bold text-gov-navy tracking-tight">
                  Demo Records
                </h3>
                <p className="text-sm text-slate-500 mt-1">Select a synthetic identity to view their estate continuity analysis.</p>
              </div>
              <span className="inline-flex items-center rounded-full glass-panel border-gov-blue/20 bg-gov-blue/5 px-3 py-1 text-xs font-bold text-gov-blue uppercase tracking-wider">
                {personas.length} records
              </span>
            </div>

            {loading ? (
              <div className="flex justify-center py-20" role="status">
                <svg className="h-10 w-10 animate-spin text-gov-blue opacity-50" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span className="sr-only">Loading personas...</span>
              </div>
            ) : null}

            {error ? (
              <div role="alert" className="glass-panel rounded-xl border-l-4 border-l-red-600 p-6 flex gap-4">
                <svg className="h-6 w-6 text-red-600 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <h4 className="font-bold text-red-900">System Error</h4>
                  <p className="text-sm font-medium text-red-800 mt-1">{error}</p>
                </div>
              </div>
            ) : null}

            {!loading && !error && personas.length === 0 ? (
              <div className="rounded-2xl border-2 border-dashed border-slate-300/60 bg-white/40 backdrop-blur-sm p-16 text-center">
                <div className="mx-auto w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
                  <svg className="h-8 w-8 text-slate-400" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m3.75 9v6m3-3H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                </div>
                <h3 className="text-lg font-bold text-slate-900">No Personas Found</h3>
                <p className="mt-2 text-sm text-slate-500 max-w-md mx-auto">
                  Upload the synthetic demo documents from <code className="rounded bg-slate-100/80 px-1.5 py-0.5 font-mono text-xs text-slate-700 border border-slate-200">seed_data/</code> to get started with the system.
                </p>
              </div>
            ) : null}

            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:gap-8">
              {personas.map((persona) => (
                <Link
                  key={persona.id}
                  href={`/personas/${persona.id}`}
                  className="group relative flex flex-col rounded-2xl glass-panel p-6 glass-card-hover overflow-hidden"
                >
                  {/* Card Background Decoration */}
                  <div className="absolute -right-4 -top-4 w-24 h-24 bg-gov-blue/5 rounded-full blur-xl group-hover:bg-gov-blue/10 transition-colors duration-500" />
                  
                  <div className="relative z-10 flex items-start gap-4 border-b border-slate-200/50 pb-5">
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-gov-blue to-gov-navy text-white shadow-md shadow-gov-blue/20">
                      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                      </svg>
                    </div>
                    <div>
                      <h4 className="text-lg font-bold text-gov-navy group-hover:text-gov-blue transition-colors">
                        {persona.name}
                      </h4>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-100 text-slate-500 border border-slate-200">ID: {persona.id}</span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-gov-green/10 text-gov-green uppercase tracking-wider">Record active</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="relative z-10 flex-1 pt-5 pb-6">
                    <p className="text-sm text-slate-600 line-clamp-3 leading-relaxed font-medium">
                      {persona.description ?? "Synthetic demo persona for estate conflict testing."}
                    </p>
                  </div>
                  
                  <div className="relative z-10 mt-auto flex items-center justify-between border-t border-slate-100 pt-4">
                    <span className="inline-flex items-center gap-2 text-sm font-bold text-gov-blue group-hover:text-gov-navy transition-colors">
                      View full record
                      <svg className="h-4 w-4 transform transition-transform group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                      </svg>
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          </section>
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
                Synthetic demonstration environment
              </p>
              <p className="text-[10px] text-slate-500 mt-1">
                Results are informational and require professional review. Not legal advice.
              </p>
            </div>
          </div>
          
          <div className="mt-6 border-t border-slate-200/50 pt-6 flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-xs font-medium text-slate-400">
               {new Date().getFullYear()} JeevanSetu
            </p>
            <div className="flex items-center gap-1 opacity-50">
              <div className="h-1.5 w-1.5 rounded-full bg-gov-saffron" />
              <div className="h-1.5 w-1.5 rounded-full bg-slate-300" />
              <div className="h-1.5 w-1.5 rounded-full bg-gov-green" />
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
