"use client";

import React, { useState } from "react";
import { AnalysisRun } from "@/types";
import { 
  Terminal, 
  CheckCircle2, 
  XCircle, 
  RotateCw, 
  ChevronDown, 
  ChevronUp, 
  Clock, 
  AlertOctagon
} from "lucide-react";

interface RunProgressProps {
  run: AnalysisRun;
}

export const RunProgress: React.FC<RunProgressProps> = ({ run }) => {
  const [expandedAttempt, setExpandedAttempt] = useState<number | null>(
    run.attempts.length > 0 ? run.attempts[run.attempts.length - 1].attempt_number : null
  );

  const getStatusBadge = () => {
    switch (run.status) {
      case "success":
      case "completed":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Execution Succeeded
          </span>
        );
      case "failed":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
            <XCircle className="w-3.5 h-3.5" />
            Max Attempts Reached
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            <RotateCw className="w-3.5 h-3.5 animate-spin" />
            Running Pipeline...
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 shadow-md text-slate-100 overflow-hidden font-sans">
      {/* Run Header */}
      <div className="p-4 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Terminal className="w-5 h-5 text-blue-400" />
          <div>
            <h4 className="text-sm font-semibold text-slate-200">
              Execution Sandbox & Telemetry
            </h4>
            <span className="text-xs text-slate-500 font-mono">
              Run ID: {run.id.slice(0, 8)}...
            </span>
          </div>
        </div>
        <div>{getStatusBadge()}</div>
      </div>

      {/* Attempts List */}
      <div className="p-4 space-y-3">
        {run.attempts.length === 0 ? (
          <p className="text-xs text-slate-500 py-3 italic text-center">
            Awaiting sandbox spin-up...
          </p>
        ) : (
          run.attempts.map((att) => {
            const isExpanded = expandedAttempt === att.attempt_number;
            const isSuccess = att.status === "success" || att.exit_code === 0;

            return (
              <div
                key={att.attempt_number}
                className="border border-slate-800 rounded-lg overflow-hidden bg-slate-950/40"
              >
                <div
                  onClick={() =>
                    setExpandedAttempt(isExpanded ? null : att.attempt_number)
                  }
                  className="p-3 flex items-center justify-between cursor-pointer hover:bg-slate-800/40 transition-colors"
                >
                  <div className="flex items-center gap-2.5">
                    {isSuccess ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <AlertOctagon className="w-4 h-4 text-amber-400" />
                    )}
                    <span className="text-xs font-semibold text-slate-200">
                      Attempt #{att.attempt_number}
                    </span>
                    {att.failure_type && (
                      <span className="text-[11px] px-2 py-0.5 rounded bg-red-950 text-red-300 border border-red-800 font-mono">
                        {att.failure_type}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-4 text-xs text-slate-400">
                    {att.duration_ms !== undefined && (
                      <span className="flex items-center gap-1 font-mono text-[11px]">
                        <Clock className="w-3 h-3" />
                        {(att.duration_ms / 1000).toFixed(2)}s
                      </span>
                    )}
                    <span className="font-mono text-[11px]">
                      Exit: {att.exit_code ?? 0}
                    </span>
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    )}
                  </div>
                </div>

                {isExpanded && (
                  <div className="p-4 border-t border-slate-800/80 bg-slate-950/80 space-y-3 font-mono text-xs">
                    {att.stderr && (
                      <div>
                        <span className="text-[11px] text-red-400 font-bold uppercase tracking-wider block mb-1">
                          Stderr / Traceback Captured:
                        </span>
                        <pre className="p-3 bg-red-950/30 border border-red-900/50 rounded text-red-200 text-[11px] overflow-x-auto whitespace-pre-wrap max-h-48">
                          {att.stderr}
                        </pre>
                      </div>
                    )}

                    {att.stdout && (
                      <div>
                        <span className="text-[11px] text-slate-400 font-bold uppercase tracking-wider block mb-1">
                          Stdout:
                        </span>
                        <pre className="p-3 bg-slate-900 border border-slate-800 rounded text-slate-300 text-[11px] overflow-x-auto whitespace-pre-wrap max-h-60">
                          {att.stdout}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
