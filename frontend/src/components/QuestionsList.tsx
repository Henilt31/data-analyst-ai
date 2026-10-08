"use client";

import React, { useState } from "react";
import { ResearchQuestion, AnalysisRun } from "@/types";
import { 
  Sparkles, 
  Play, 
  CheckCircle2, 
  Loader2 
} from "lucide-react";

interface QuestionsListProps {
  datasetId: string;
  questions: ResearchQuestion[];
  onGenerateQuestions: (ragEnabled: boolean) => Promise<void>;
  onTriggerRun: (questionId: string) => Promise<void>;
  activeRunQuestionId?: string | null;
  runs: Record<string, AnalysisRun>;
}

export const QuestionsList: React.FC<QuestionsListProps> = ({
  questions,
  onGenerateQuestions,
  onTriggerRun,
  activeRunQuestionId,
  runs,
}) => {
  const [ragEnabled, setRagEnabled] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = async () => {
    try {
      setIsGenerating(true);
      await onGenerateQuestions(ragEnabled);
    } finally {
      setIsGenerating(false);
    }
  };

  const getCategoryBadgeColor = (category?: string) => {
    switch (category?.toLowerCase()) {
      case "distribution":
        return "bg-blue-50 text-blue-700 border-blue-200";
      case "correlation":
        return "bg-purple-50 text-purple-700 border-purple-200";
      case "segmentation":
        return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case "outlier_analysis":
        return "bg-amber-50 text-amber-700 border-amber-200";
      case "temporal_trend":
        return "bg-cyan-50 text-cyan-700 border-cyan-200";
      default:
        return "bg-slate-50 text-slate-700 border-slate-200";
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-600" />
            Autonomous Research Questions
          </h3>
          <p className="text-sm text-slate-500 mt-0.5">
            Formulated from dataset schema, statistical distributions, and variance patterns.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs text-slate-600 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={ragEnabled}
              onChange={(e) => setRagEnabled(e.target.checked)}
              className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-3.5 h-3.5"
            />
            <span className="font-medium">Use RAG Memory</span>
          </label>

          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors shadow-2xs disabled:opacity-50"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Formulating...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                {questions.length > 0 ? "Regenerate Questions" : "Generate Questions"}
              </>
            )}
          </button>
        </div>
      </div>

      {questions.length === 0 ? (
        <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50/50">
          <Sparkles className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <h4 className="text-sm font-semibold text-slate-700">No Research Questions Yet</h4>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
            Click &quot;Generate Questions&quot; above to have the LLM inspect the profile and propose grounded analytical hypotheses.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {questions.map((q, idx) => {
            const run = runs[q.id];
            const isRunning = activeRunQuestionId === q.id || run?.status === "running";
            const isCompleted = run?.status === "success" || run?.status === "completed";

            return (
              <div
                key={q.id}
                className="p-5 border border-slate-200/80 rounded-xl hover:border-slate-300 bg-slate-50/30 transition-all duration-150"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs font-bold text-slate-400">Q{idx + 1}</span>
                      <span
                        className={`text-xs px-2.5 py-0.5 rounded-full border font-medium capitalize ${getCategoryBadgeColor(
                          q.category
                        )}`}
                      >
                        {q.category?.replace("_", " ") || "Exploratory"}
                      </span>
                    </div>

                    <h4 className="text-base font-semibold text-slate-900 leading-snug mb-2">
                      {q.question}
                    </h4>

                    {q.rationale && (
                      <p className="text-xs text-slate-600 mb-3 leading-relaxed">
                        {q.rationale}
                      </p>
                    )}

                    {q.columns_involved && q.columns_involved.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5 mt-2">
                        <span className="text-[11px] text-slate-400 font-medium mr-1">Columns:</span>
                        {q.columns_involved.map((col) => (
                          <span
                            key={col}
                            className="text-[11px] px-2 py-0.5 bg-white border border-slate-200 rounded font-mono text-slate-600"
                          >
                            {col}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="shrink-0 self-center">
                    {isRunning ? (
                      <div className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 border border-blue-200 text-blue-700 text-xs font-medium rounded-lg">
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        Analyzing...
                      </div>
                    ) : isCompleted ? (
                      <div className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-medium rounded-lg">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Completed
                      </div>
                    ) : (
                      <button
                        onClick={() => onTriggerRun(q.id)}
                        className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
                      >
                        <Play className="w-3.5 h-3.5 fill-current" />
                        Run Analysis
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
