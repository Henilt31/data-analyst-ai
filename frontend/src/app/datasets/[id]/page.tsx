"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { Dataset, DatasetProfile, ResearchQuestion, AnalysisRun, Report } from "@/types";
import { DatasetProfileView } from "@/components/DatasetProfileView";
import { QuestionsList } from "@/components/QuestionsList";
import { RunProgress } from "@/components/RunProgress";
import { InsightCard } from "@/components/InsightCard";
import { ReportViewer } from "@/components/ReportViewer";
import { 
  ArrowLeft, 
  Sparkles, 
  FileText, 
  Database, 
  BarChart2, 
  Loader2, 
  AlertCircle
} from "lucide-react";

function DatasetContent() {
  const routerParams = useParams();
  const datasetId = Array.isArray(routerParams?.id) ? routerParams.id[0] : (routerParams?.id as string);

  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [questions, setQuestions] = useState<ResearchQuestion[]>([]);
  const [runs, setRuns] = useState<Record<string, AnalysisRun>>({});
  const [report, setReport] = useState<Report | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeRunQuestionId, setActiveRunQuestionId] = useState<string | null>(null);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);

  // Initial Data Fetch
  useEffect(() => {
    async function loadData() {
      try {
        setIsLoading(true);
        setError(null);

        const [ds, prof, qList] = await Promise.all([
          api.getDataset(datasetId),
          api.getProfile(datasetId).catch(() => null),
          api.getQuestions(datasetId).catch(() => []),
        ]);

        setDataset(ds);
        setProfile(prof);
        setQuestions(qList);

        // Try to fetch report if already generated
        try {
          const rep = await api.getReport(datasetId);
          setReport(rep);
        } catch {
          // Report not created yet
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Failed to load dataset details.";
        setError(msg);
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, [datasetId]);

  // WebSocket Live Connection for Run Updates
  useEffect(() => {
    const wsUrl = api.getWebSocketUrl(datasetId);
    let ws: WebSocket | null = null;

    try {
      ws = new WebSocket(wsUrl);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "run_started") {
            setActiveRunQuestionId(data.question_id);
          } else if (data.type === "run_completed") {
            setActiveRunQuestionId(null);
            // Refresh run data
            if (data.run_id) {
              api.getRun(data.run_id).then((runData) => {
                setRuns((prev) => ({ ...prev, [data.question_id]: runData }));
              });
            }
          }
        } catch (err) {
          console.error("WebSocket message parsing error:", err);
        }
      };

      ws.onerror = (e) => {
        console.warn("WebSocket status connection warning:", e);
      };
    } catch (err) {
      console.warn("WebSocket could not be initialized:", err);
    }

    return () => {
      if (ws) ws.close();
    };
  }, [datasetId]);

  const handleGenerateQuestions = async (ragEnabled: boolean) => {
    try {
      const newQuestions = await api.generateQuestions(datasetId, ragEnabled);
      setQuestions(newQuestions);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to generate research questions";
      alert(msg);
    }
  };

  const handleTriggerRun = async (questionId: string) => {
    try {
      setActiveRunQuestionId(questionId);
      const runResult = await api.triggerRun(questionId, datasetId);
      setRuns((prev) => ({ ...prev, [questionId]: runResult }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Analysis execution failed";
      alert(msg);
    } finally {
      setActiveRunQuestionId(null);
    }
  };

  const handleGenerateReport = async () => {
    try {
      setIsGeneratingReport(true);
      const newReport = await api.generateReport(datasetId);
      setReport(newReport);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to generate analytical report";
      alert(msg);
    } finally {
      setIsGeneratingReport(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="flex flex-col items-center gap-3 text-slate-500">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <p className="text-sm font-medium">Loading dataset & statistical profile...</p>
        </div>
      </div>
    );
  }

  if (error || !dataset) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full p-6 bg-white rounded-xl border border-red-200 shadow-sm text-center">
          <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-3" />
          <h2 className="text-base font-bold text-slate-800 mb-1">Dataset Load Failed</h2>
          <p className="text-xs text-slate-500 mb-4">{error || "Dataset could not be found."}</p>
          <Link
            href="/datasets"
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-semibold"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Datasets
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      {/* Top Navigation */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-2xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/datasets"
              className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold text-slate-900 truncate max-w-md">
                  {dataset.original_filename}
                </h1>
                <span className="text-[11px] uppercase font-bold px-2 py-0.5 bg-blue-50 text-blue-700 rounded border border-blue-200">
                  {dataset.file_type}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Uploaded {new Date(dataset.created_at).toLocaleString()} • Local Sandbox Active
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleGenerateReport}
              disabled={isGeneratingReport}
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-2xs transition-colors disabled:opacity-50"
            >
              {isGeneratingReport ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Compiling Report...
                </>
              ) : (
                <>
                  <FileText className="w-3.5 h-3.5" />
                  Generate Analytical Report
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 space-y-8">
        {/* Section 1: Profiling */}
        <section>
          <div className="flex items-center gap-2 mb-3">
            <Database className="w-4 h-4 text-blue-600" />
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500">
              1. Deterministic Statistical Profile
            </h2>
          </div>
          {profile ? (
            <DatasetProfileView dataset={dataset} profile={profile} />
          ) : (
            <div className="p-8 bg-white rounded-xl border border-slate-200 text-center text-sm text-slate-500">
              Profiling in progress or unavailable for this dataset.
            </div>
          )}
        </section>

        {/* Section 2: Research Questions & Execution */}
        <section>
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-4 h-4 text-indigo-600" />
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500">
              2. Autonomous Analysis Pipeline
            </h2>
          </div>
          <QuestionsList
            datasetId={datasetId}
            questions={questions}
            onGenerateQuestions={handleGenerateQuestions}
            onTriggerRun={handleTriggerRun}
            activeRunQuestionId={activeRunQuestionId}
            runs={runs}
          />
        </section>

        {/* Section 3: Live Runs & Grounded Insights */}
        {Object.keys(runs).length > 0 && (
          <section className="space-y-6">
            <div className="flex items-center gap-2 mb-3">
              <BarChart2 className="w-4 h-4 text-emerald-600" />
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500">
                3. Execution Results & Grounded Insights
              </h2>
            </div>

            <div className="grid grid-cols-1 gap-6">
              {Object.entries(runs).map(([qId, run]) => {
                const questionObj = questions.find((q) => q.id === qId);

                return (
                  <div key={run.id} className="space-y-4">
                    {/* Telemetry Progress Block */}
                    <RunProgress run={run} />

                    {/* Insight Card Block */}
                    {run.insight && (
                      <InsightCard
                        insight={run.insight}
                        visualization={run.visualization}
                        questionText={questionObj?.question}
                      />
                    )}
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* Section 4: Final Analytical Report */}
        {report && (
          <section>
            <div className="flex items-center gap-2 mb-3">
              <FileText className="w-4 h-4 text-purple-600" />
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500">
                4. Final Analytical Report
              </h2>
            </div>
            <ReportViewer
              report={report}
              onGenerateNewReport={handleGenerateReport}
              isGenerating={isGeneratingReport}
            />
          </section>
        )}
      </main>
    </div>
  );
}

export default function DatasetPage() {
  return (
    <React.Suspense
      fallback={
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
          <div className="flex flex-col items-center gap-3 text-slate-500">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            <p className="text-sm font-medium">Loading dataset workspace...</p>
          </div>
        </div>
      }
    >
      <DatasetContent />
    </React.Suspense>
  );
}
