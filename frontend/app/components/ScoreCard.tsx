import type { DetectionRun } from "../lib/api";

function toneFor(score: number): { text: string; bg: string; stroke: string; label: string } {
  if (score >= 90) {
    return { text: "text-gov-green", bg: "bg-gov-green/10", stroke: "stroke-gov-green", label: "Clear Profile" };
  }
  if (score >= 70) {
    return { text: "text-gov-saffron", bg: "bg-gov-saffron/10", stroke: "stroke-gov-saffron", label: "Needs Attention" };
  }
  return { text: "text-red-600", bg: "bg-red-500/10", stroke: "stroke-red-500", label: "Critical Conflicts" };
}

export function ScoreCard({ run, stale = false }: { run: DetectionRun; stale?: boolean }) {
  const breakdown = run.score_breakdown;

  if (run.readiness_score === null) {
    return (
      <section
        className="rounded-2xl glass-panel p-8 shadow-sm relative overflow-hidden"
        aria-labelledby="score-heading"
      >
        <h2 id="score-heading" className="text-sm font-bold uppercase tracking-widest text-slate-500">
          Continuity Readiness Score
        </h2>
        <p className="mt-3 text-sm font-medium text-slate-600">
          This analysis was recorded before scoring was implemented. Re-run detection to calculate the score.
        </p>
      </section>
    );
  }

  const score = run.readiness_score;
  const tone = toneFor(score);

  // SVG Circle calculations
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <section
      className="rounded-2xl glass-panel p-8 shadow-sm relative overflow-hidden"
      aria-labelledby="score-heading"
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-8">
        
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-6">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-gov-blue/10 text-gov-blue">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
              </svg>
            </span>
            <h2 id="score-heading" className="text-sm font-bold uppercase tracking-widest text-gov-navy">
              Continuity Readiness Score
            </h2>
          </div>

          <div className="flex items-center gap-8">
            {/* Visual Score Arc */}
            <div className="relative h-32 w-32 flex-shrink-0">
              {/* Background circle */}
              <svg className="h-full w-full -rotate-90 transform" viewBox="0 0 140 140">
                <circle
                  className="text-slate-200"
                  strokeWidth="8"
                  stroke="currentColor"
                  fill="transparent"
                  r={radius}
                  cx="70"
                  cy="70"
                />
                <circle
                  className={`${tone.stroke} score-arc`}
                  strokeWidth="8"
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="transparent"
                  r={radius}
                  cx="70"
                  cy="70"
                />
              </svg>
              {/* Center text */}
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={`text-3xl font-black tabular-nums tracking-tight ${tone.text}`}>
                  {score}
                </span>
                <span className="text-[10px] font-bold uppercase text-slate-400">/ 100</span>
              </div>
            </div>
            
            <div className="flex flex-col gap-2">
              <span className={`inline-flex px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider w-fit ${tone.bg} ${tone.text}`}>
                {tone.label}
              </span>
              <p className="text-xs font-medium text-slate-500 max-w-xs mt-2 leading-relaxed">
                Score based on <strong className="text-slate-700">deterministic evaluation</strong> of 
                detected field extractions against the rules engine.
              </p>
            </div>
          </div>
        </div>

        <div className="flex-1 w-full border-t border-slate-200/50 md:border-t-0 md:border-l md:pl-8 pt-6 md:pt-0">
          <div className="grid grid-cols-2 gap-x-6 gap-y-6">
            <div className="glass-panel bg-white/50 rounded-xl p-3 border border-slate-100/50">
              <dt className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Base</dt>
              <dd className="mt-1 text-2xl font-black tracking-tight text-gov-navy">{breakdown.base ?? 100}</dd>
            </div>
            <div className="glass-panel bg-white/50 rounded-xl p-3 border border-slate-100/50">
              <dt className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">High conflicts</dt>
              <dd className="mt-1 text-2xl font-black tracking-tight text-gov-navy">{breakdown.high_conflicts ?? 0}</dd>
            </div>
            <div className="glass-panel bg-white/50 rounded-xl p-3 border border-slate-100/50">
              <dt className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Med conflicts</dt>
              <dd className="mt-1 text-2xl font-black tracking-tight text-gov-navy">{breakdown.medium_conflicts ?? 0}</dd>
            </div>
            <div className="glass-panel bg-white/50 rounded-xl p-3 border border-slate-100/50">
              <dt className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Review gaps</dt>
              <dd className="mt-1 text-2xl font-black tracking-tight text-gov-navy">{breakdown.gaps ?? 0}</dd>
            </div>
          </div>
        </div>
        
      </div>

      {stale ? (
        <div className="mt-6 flex items-start gap-3 rounded-lg border border-gov-saffron/30 bg-gov-saffron/5 p-4 text-sm font-medium text-slate-800 shadow-sm">
          <svg className="h-5 w-5 flex-none text-gov-saffron" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p>
            A field was modified after this analysis. Re-run detection to recalculate the score.
          </p>
        </div>
      ) : null}

      <div className="mt-6 border-t border-slate-200/50 pt-4 flex items-center gap-3">
        <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
        </svg>
        <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">
          Calculation: Base {breakdown.base ?? 100} &minus; {breakdown.deduction ?? 0} (Findings) &bull; Rules v{run.rules_version}
        </p>
      </div>
    </section>
  );
}
