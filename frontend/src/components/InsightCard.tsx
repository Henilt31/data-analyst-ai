"use client";

import React from "react";
import { Insight, Visualization } from "@/types";
import { 
  Lightbulb, 
  AlertTriangle, 
  Target, 
  BarChart, 
  Image as ImageIcon 
} from "lucide-react";

interface InsightCardProps {
  insight: Insight;
  visualization?: Visualization;
  questionText?: string;
}

export const InsightCard: React.FC<InsightCardProps> = ({
  insight,
  visualization,
  questionText,
}) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-slate-100 bg-gradient-to-r from-blue-50/60 to-indigo-50/60">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-700 mb-1">
          <Lightbulb className="w-4 h-4 text-blue-600" />
          Grounded Analytical Finding
        </div>
        {questionText && (
          <h3 className="text-base font-bold text-slate-900 mt-1">
            {questionText}
          </h3>
        )}
      </div>

      <div className="p-6 space-y-6">
        {/* Core Grounded Insight Text */}
        <div>
          <p className="text-sm text-slate-800 leading-relaxed font-normal">
            {insight.text}
          </p>
        </div>

        {/* Quantitative Evidence Badges */}
        {insight.important_numbers && Object.keys(insight.important_numbers).length > 0 && (
          <div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2.5">
              Verified Computed Metrics (Ground Truth)
            </span>
            <div className="flex flex-wrap gap-2.5">
              {Object.entries(insight.important_numbers).map(([k, v]) => (
                <div
                  key={k}
                  className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs"
                >
                  <span className="text-slate-500 font-medium mr-1.5">{k}:</span>
                  <span className="font-bold font-mono text-slate-900">
                    {typeof v === "number" ? v.toLocaleString() : String(v)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Strategic Takeaway & Caveats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {insight.takeaway && (
            <div className="p-4 bg-emerald-50/60 border border-emerald-200/60 rounded-xl">
              <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-800 mb-1">
                <Target className="w-3.5 h-3.5 text-emerald-600" />
                Strategic Takeaway
              </div>
              <p className="text-xs text-emerald-900 leading-relaxed font-medium">
                {insight.takeaway}
              </p>
            </div>
          )}

          {insight.caveats && (
            <div className="p-4 bg-amber-50/60 border border-amber-200/60 rounded-xl">
              <div className="flex items-center gap-1.5 text-xs font-bold text-amber-800 mb-1">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                Analytical Caveats
              </div>
              <p className="text-xs text-amber-900 leading-relaxed">
                {insight.caveats}
              </p>
            </div>
          )}
        </div>

        {/* Visualization Embed */}
        {visualization && (
          <div className="pt-4 border-t border-slate-100">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                <BarChart className="w-3.5 h-3.5 text-indigo-500" />
                Generated Visualization ({visualization.chart_type})
              </span>
              {visualization.title && (
                <span className="text-xs font-medium text-slate-600">
                  {visualization.title}
                </span>
              )}
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-center min-h-[160px]">
              <div className="text-center text-xs text-slate-500">
                <ImageIcon className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                <p className="font-medium text-slate-700">
                  Chart artifact rendered to <code className="text-indigo-600">{visualization.chart_path}</code>
                </p>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Type: {visualization.chart_type}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
