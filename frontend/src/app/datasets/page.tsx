"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Dataset } from "@/types";
import { DatasetUpload } from "@/components/DatasetUpload";
import { 
  Database, 
  FileSpreadsheet, 
  ArrowRight, 
  Calendar, 
  Layers, 
  Loader2,
  HardDrive
} from "lucide-react";

export default function DatasetsPage() {
  const router = useRouter();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    api.getDatasets()
      .then((data) => {
        if (isMounted) {
          setDatasets(data);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.error("Failed to load datasets:", err);
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const handleUploadSuccess = (newDataset: Dataset) => {
    setDatasets((prev) => [newDataset, ...prev]);
    router.push(`/datasets/${newDataset.id}`);
  };

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      {/* Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold shadow-xs">
              DM
            </div>
            <div>
              <h1 className="text-base font-bold text-slate-900 leading-tight">DataMind</h1>
              <p className="text-xs text-slate-500">Local-First Autonomous EDA Platform</p>
            </div>
          </div>

          <div className="text-xs font-medium px-3 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full">
            ● Local Engine Ready
          </div>
        </div>
      </header>

      {/* Main Body */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 space-y-8">
        {/* Upload Section */}
        <section className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
          <h2 className="text-base font-bold text-slate-900 mb-1">Upload New Dataset</h2>
          <p className="text-xs text-slate-500 mb-6">
            Upload CSV, JSON, Parquet, or Excel files. Automated statistical profiling will trigger immediately.
          </p>
          <DatasetUpload onUploadSuccess={handleUploadSuccess} />
        </section>

        {/* Existing Datasets Section */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
              <Database className="w-4 h-4 text-slate-600" />
              Analyzed Datasets ({datasets.length})
            </h2>
          </div>

          {isLoading ? (
            <div className="p-12 text-center text-slate-400 flex flex-col items-center gap-2 bg-white rounded-xl border border-slate-200">
              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
              <span className="text-xs font-medium">Loading datasets...</span>
            </div>
          ) : datasets.length === 0 ? (
            <div className="p-12 text-center bg-white rounded-xl border border-slate-200">
              <FileSpreadsheet className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <h3 className="text-sm font-semibold text-slate-700">No Datasets Uploaded Yet</h3>
              <p className="text-xs text-slate-500 mt-1">
                Upload a dataset using the dropzone above to begin exploratory data analysis.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {datasets.map((ds) => (
                <Link
                  key={ds.id}
                  href={`/datasets/${ds.id}`}
                  className="group bg-white p-5 rounded-xl border border-slate-200 hover:border-blue-400 hover:shadow-sm transition-all duration-150 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <h3 className="font-semibold text-slate-900 text-sm truncate group-hover:text-blue-600 transition-colors">
                        {ds.original_filename}
                      </h3>
                      <span className="text-[11px] uppercase font-bold px-2 py-0.5 bg-slate-100 text-slate-700 rounded border border-slate-200 shrink-0">
                        {ds.file_type}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs text-slate-600 mb-4">
                      <div className="flex items-center gap-1.5">
                        <Layers className="w-3.5 h-3.5 text-slate-400" />
                        <span>
                          <strong>{ds.row_count?.toLocaleString() ?? "-"}</strong> rows
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <HardDrive className="w-3.5 h-3.5 text-slate-400" />
                        <span>
                          <strong>{ds.column_count ?? "-"}</strong> cols
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {new Date(ds.created_at).toLocaleDateString()}
                    </span>
                    <span className="text-blue-600 font-medium inline-flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                      Explore <ArrowRight className="w-3 h-3" />
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
