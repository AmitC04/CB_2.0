import type { Finding, Severity } from "../lib/api";

const severityStyles: Record<Severity, string> = {
  high: "bg-red-500/10 text-red-600 border-red-500/30 ring-1 ring-inset ring-red-500/20",
  medium: "bg-amber-500/10 text-amber-600 border-amber-500/30 ring-1 ring-inset ring-amber-500/20",
  low: "bg-gov-blue/10 text-gov-blue border-gov-blue/30 ring-1 ring-inset ring-gov-blue/20",
};

const findingTypeLabels: Record<Finding["finding_type"], string> = {
  review_conflict: "Review conflict",
  validity_warning: "Validity warning",
  scope_gap: "Manual review required",
};

function SourceBlock({
  heading,
  label,
  locator,
  text,
}: {
  heading: string;
  label: string;
  locator: string;
  text: string;
}) {
  return (
    <div className={`relative rounded-xl border border-white/60 bg-white/50 p-5 shadow-sm backdrop-blur-sm z-10 w-full`}>
      <div className="flex items-center gap-2 mb-3">
        <span className="flex h-6 w-6 items-center justify-center rounded bg-slate-200/50 text-slate-500">
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
        </span>
        <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">
          {heading}
        </p>
      </div>
      <p className="text-sm font-bold text-gov-navy leading-tight">{label}</p>
      <p className="mt-1 text-[11px] font-medium text-slate-500">{locator} — extracted text:</p>
      <blockquote className="mt-3 border-l-2 border-gov-blue bg-white/70 p-3 text-xs italic text-slate-700 shadow-sm rounded-r-lg font-serif">
        &quot;{text}&quot;
      </blockquote>
    </div>
  );
}

export function FindingCard({ finding }: { finding: Finding }) {
  const isConflict = finding.finding_type === "review_conflict";

  return (
    <article className="rounded-2xl glass-panel p-6 shadow-sm border border-slate-200/60 relative overflow-hidden group">
      
      {/* Accent Background line */}
      <div className={`absolute top-0 left-0 w-1 h-full ${finding.severity === 'high' ? 'bg-red-500' : finding.severity === 'medium' ? 'bg-amber-500' : 'bg-gov-blue'}`} />

      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200/50 pb-5">
        <div className="flex flex-wrap items-center gap-2.5">
          <span
            className={`rounded px-2.5 py-1 text-[10px] font-black uppercase tracking-widest ${severityStyles[finding.severity]}`}
          >
            {finding.severity}
          </span>
          <span className="rounded bg-slate-100/80 px-2.5 py-1 text-[10px] font-bold text-slate-600 uppercase tracking-wider border border-slate-200/50">
            {findingTypeLabels[finding.finding_type]}
          </span>
          <span className="rounded border border-slate-200/50 bg-white/50 px-2.5 py-1 font-mono text-[10px] font-bold text-slate-500 uppercase tracking-widest">
            Rule: {finding.rule_id}
          </span>
        </div>
        {finding.asset_reference ? (
          <span className="font-mono text-[10px] font-bold text-gov-navy bg-gov-blue/5 border border-gov-blue/10 px-2.5 py-1 rounded tracking-widest uppercase">
            Asset: {finding.asset_reference}
          </span>
        ) : null}
      </header>

      <div className="mt-5">
        <h3 className="text-xl font-bold leading-tight text-gov-navy pr-8">
          {finding.summary}
        </h3>

        {finding.explanation ? (
          <p className="mt-3 text-sm leading-relaxed text-slate-600 font-medium">{finding.explanation}</p>
        ) : finding.finding_type === "scope_gap" ? null : (
          <p className="mt-3 rounded-lg bg-slate-100/50 border border-slate-200/50 p-3 text-sm text-slate-500 italic">
            Plain-language wording is unavailable for this finding. The details below come
            from the deterministic rule engine.
          </p>
        )}
      </div>

      <div className="mt-8 relative">
        <div className="grid gap-6 sm:gap-12 sm:grid-cols-2 relative z-10">
          <SourceBlock
            heading="Source A"
            label={finding.source_a.label}
            locator={finding.source_a.locator}
            text={finding.source_a.text}
          />
          {finding.source_b ? (
            <SourceBlock
              heading="Source B"
              label={finding.source_b.label}
              locator={finding.source_b.locator}
              text={finding.source_b.text}
            />
          ) : null}
        </div>

        {/* Visual Connector for Conflicts */}
        {finding.source_b && isConflict && (
          <div className="absolute inset-0 hidden sm:flex items-center justify-center pointer-events-none z-0">
            <div className="w-16 h-px bg-red-300 relative">
              <div className="absolute inset-0 animate-pulse bg-red-400" />
            </div>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-red-50 border border-red-200 shadow-sm relative z-20">
              <svg className="h-4 w-4 text-red-500" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div className="w-16 h-px bg-red-300 relative">
              <div className="absolute inset-0 animate-pulse bg-red-400" />
            </div>
          </div>
        )}
      </div>

      {finding.suggested_fix ? (
        <div className="mt-8 rounded-xl border border-gov-green/20 bg-gov-green/5 p-5">
          <div className="flex items-center gap-2">
            <svg className="h-5 w-5 text-gov-green" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
            </svg>
            <p className="text-[10px] font-bold uppercase tracking-widest text-gov-green">
              Suggested fix
            </p>
          </div>
          <p className="mt-2 text-sm leading-relaxed text-slate-700 font-medium">{finding.suggested_fix}</p>
        </div>
      ) : null}

      <div className="mt-8 rounded-xl border border-slate-200/60 bg-white/40 p-5 shadow-sm">
        <p className="text-[10px] font-bold uppercase tracking-widest text-gov-navy">
          Recommended Action
        </p>
        <ul className="mt-4 space-y-2.5">
          {finding.suggested_actions.map((action, idx) => (
            <li key={idx} className="flex items-start gap-3 text-sm text-slate-700 font-medium leading-relaxed">
              <span className="flex-shrink-0 mt-0.5 h-4 w-4 rounded-full bg-slate-200 flex items-center justify-center text-[8px] font-bold text-slate-500">{idx + 1}</span>
              {action}
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-6 border-t border-slate-200/50 pt-5 space-y-3 bg-slate-50/50 -mx-6 -mb-6 px-6 pb-6 rounded-b-2xl">
        <p className="text-[11px] leading-relaxed text-slate-500">
          <strong className="font-bold text-slate-700 uppercase tracking-wider text-[10px]">Scope:</strong> {finding.legal_scope_note}
        </p>
        <p className="text-[11px] leading-relaxed text-red-600/80 font-bold uppercase tracking-wide">
          Disclaimer: {finding.disclaimer}
        </p>
      </div>
    </article>
  );
}
