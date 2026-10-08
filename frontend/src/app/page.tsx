import Link from "next/link";
import { ArrowRight, Sparkles, ShieldCheck, Terminal, Cpu } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50 flex flex-col justify-between">
      {/* Top Navbar */}
      <header className="max-w-7xl mx-auto w-full px-6 py-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white font-extrabold text-lg shadow-sm">
            DM
          </div>
          <div>
            <span className="font-bold text-slate-900 text-lg tracking-tight">DataMind</span>
            <span className="text-xs text-slate-400 block -mt-1 font-mono">Autonomous EDA</span>
          </div>
        </div>

        <Link
          href="/datasets"
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
        >
          Open Workspace <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </header>

      {/* Hero Section */}
      <main className="max-w-4xl mx-auto px-6 py-16 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200/80 text-blue-700 text-xs font-semibold mb-6">
          <Sparkles className="w-3.5 h-3.5 text-blue-600" />
          Local-First Autonomous Data Analysis Agent
        </div>

        <h1 className="text-4xl sm:text-5xl font-black text-slate-900 tracking-tight leading-tight mb-6">
          From Raw Dataset to Grounded Insights in Seconds.
        </h1>

        <p className="text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed mb-10">
          Upload CSV, JSON, Parquet, or Excel files. DataMind deterministically profiles schema
          and distributions, formulates deep research questions, generates isolated Python code,
          self-corrects execution failures, and synthesizes verifiable analytical reports.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/datasets"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold shadow-sm transition-all"
          >
            Launch Autonomous Analysis <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Feature Highlights Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mt-16 text-left">
          <div className="p-5 bg-white rounded-xl border border-slate-200 shadow-2xs">
            <div className="w-9 h-9 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center mb-3">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-slate-900 text-sm mb-1">Strict Grounding</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              No LLM hallucinations. All statistical numbers, percentages, and metrics originate directly from executed Python code stdout.
            </p>
          </div>

          <div className="p-5 bg-white rounded-xl border border-slate-200 shadow-2xs">
            <div className="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center mb-3">
              <Terminal className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-slate-900 text-sm mb-1">Self-Correcting Sandbox</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Execution errors and tracebacks are captured, classified, and autonomously debugged through an isolated retry loop.
            </p>
          </div>

          <div className="p-5 bg-white rounded-xl border border-slate-200 shadow-2xs">
            <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center mb-3">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-slate-900 text-sm mb-1">100% Local-First</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              All datasets, profiles, vector embeddings, and artifacts stay locally on your machine.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-100 py-6 text-center text-xs text-slate-400">
        DataMind Autonomous EDA Platform • Local-First Architecture
      </footer>
    </div>
  );
}
