import Link from "next/link";
import { HealthStatus } from "./HealthStatus";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full bg-[#060D18] shadow-[0_8px_30px_rgb(0,0,0,0.4)] border-b border-slate-800/80">
      {/* Official Government Tricolor Top Bar - More prominent */}
      <div className="flex h-1 w-full opacity-90">
        <div className="h-full w-1/3 bg-gov-saffron"></div>
        <div className="h-full w-1/3 bg-white"></div>
        <div className="h-full w-1/3 bg-gov-green"></div>
      </div>
      
      {/* Subtle Background pattern inside header */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: 'radial-gradient(#ffffff 1px, transparent 1px)', backgroundSize: '16px 16px' }} />

      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5 relative z-10">
        <Link href="/" className="flex items-center gap-5 group">
          
          {/* High-fidelity Emblem Logo */}
          <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-[#1E2A3B] to-[#0B192C] shadow-[inset_0_1px_1px_rgba(255,255,255,0.1),0_4px_10px_rgba(0,0,0,0.5)] border border-slate-700/80 relative overflow-hidden transition-all duration-300 group-hover:border-gov-saffron/40 group-hover:scale-[1.02]">
            <div className="absolute inset-0 bg-gov-saffron/10 blur-xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <svg viewBox="0 0 40 40" className="w-9 h-9 relative z-10" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M20 37C20 37 34 30.5 34 18V8L20 3L6 8V18C6 30.5 20 37 20 37Z" fill="url(#shieldBg)" stroke="url(#shieldBorder)" strokeWidth="1.5"/>
              <path d="M14 14L20 17.5L26 14V25L20 28.5L14 25V14Z" fill="rgba(255,255,255,0.03)" stroke="white" strokeWidth="1.5" strokeLinejoin="round"/>
              <path d="M14 18.5L20 22L26 18.5" stroke="url(#accentLine)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M20 22V28.5" stroke="url(#accentLine)" strokeWidth="1.5" strokeLinecap="round"/>
              <circle cx="20" cy="17.5" r="1.5" fill="#FF9933" className="group-hover:fill-white transition-colors duration-300"/>
              <defs>
                <linearGradient id="shieldBg" x1="6" y1="3" x2="34" y2="37" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#0B192C" stopOpacity="0.9"/>
                  <stop offset="1" stopColor="#1E2A3B" stopOpacity="1"/>
                </linearGradient>
                <linearGradient id="shieldBorder" x1="6" y1="3" x2="34" y2="37" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#334155"/>
                  <stop offset="1" stopColor="#1e293b"/>
                </linearGradient>
                <linearGradient id="accentLine" x1="14" y1="18.5" x2="26" y2="28.5" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#FF9933"/>
                  <stop offset="1" stopColor="#138808"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          
          <div className="flex flex-col">
            <h1 className="text-[26px] font-black tracking-tight text-white flex items-center gap-2.5">
              JeevanSetu
              <span className="text-[9px] uppercase tracking-widest font-extrabold text-[#FFE066] bg-[#FFE066]/10 px-2 py-0.5 rounded shadow-[inset_0_1px_1px_rgba(255,255,255,0.1)] border border-[#FFE066]/20 relative -top-1">Gov</span>
            </h1>
            <p className="text-[13px] font-medium text-slate-400 mt-0.5 tracking-wide">
              Continuity starts before a crisis
            </p>
          </div>
        </Link>

        <div className="flex items-center gap-8">
          {/* Decorative Ministry context */}
          <div className="hidden md:flex items-center gap-4 text-right border-r border-slate-700/80 pr-8 mr-1">
            <div className="flex flex-col justify-center">
              <span className="text-[9px] font-bold uppercase tracking-[0.2em] text-slate-500">Department of</span>
              <span className="text-[13px] font-semibold text-slate-200 mt-0.5">Estate Continuity</span>
            </div>
            {/* Detailed seal */}
            <div className="h-11 w-11 rounded-full border-[1.5px] border-slate-700/80 flex items-center justify-center bg-gradient-to-b from-[#111C2D] to-[#0A111D] shadow-[inset_0_2px_4px_rgba(0,0,0,0.5)] relative group">
              <div className="absolute inset-1 rounded-full border border-dashed border-slate-600/60 opacity-60 group-hover:rotate-12 transition-transform duration-700" />
              <svg className="w-5 h-5 text-slate-400 relative z-10 group-hover:text-gov-saffron transition-colors duration-300" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
              </svg>
            </div>
          </div>
          
          <div className="shadow-sm rounded-full">
            <HealthStatus />
          </div>
        </div>
      </div>
    </header>
  );
}
