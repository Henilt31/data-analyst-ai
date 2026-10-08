"use client";

import React, { useState } from "react";
import { DatasetProfile, Dataset } from "@/types";
import { 
  Database, 
  Hash, 
  Type, 
  AlertTriangle, 
  Layers, 
  FileCheck2
} from "lucide-react";

interface DatasetProfileViewProps {
  dataset: Dataset;
  profile: DatasetProfile;
}

export const DatasetProfileView: React.FC<DatasetProfileViewProps> = ({ dataset, profile }) => {
  const [activeTab, setActiveTab] = useState<"schema" | "numerical" | "categorical" | "quality">("schema");

  const schemaInfo = profile.schema_info || {};
  const missingData = profile.missing_data || {};
  const numericStats = profile.numeric_stats || {};
  const categoricalStats = profile.categorical_stats || {};
  const dataQuality = profile.data_quality || {
    duplicated_rows: 0,
    constant_columns: [],
    high_cardinality_columns: [],
    suspicious_null_columns: [],
    potential_id_columns: [],
    potential_target_columns: [],
  };

  const columns = Object.keys(schemaInfo);
  const numericColumns = Object.keys(numericStats);
  const categoricalColumns = Object.keys(categoricalStats);

  // Compute total missing cells
  const totalMissing = Object.values(missingData).reduce((sum, item) => sum + (item.missing_count || 0), 0);
  const totalCells = (dataset.row_count || 0) * (dataset.column_count || 0);
  const overallMissingPct = totalCells > 0 ? ((totalMissing / totalCells) * 100).toFixed(2) : "0.00";

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
      {/* Header Metric Cards */}
      <div className="p-6 border-b border-slate-100 bg-gradient-to-b from-slate-50/50 to-white">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 bg-slate-50 border border-slate-200/60 rounded-lg">
            <div className="flex items-center gap-2 text-slate-500 text-xs font-medium uppercase tracking-wider mb-1">
              <Database className="w-3.5 h-3.5 text-blue-500" />
              Rows
            </div>
            <div className="text-2xl font-bold text-slate-900">
              {dataset.row_count?.toLocaleString() ?? "N/A"}
            </div>
          </div>

          <div className="p-4 bg-slate-50 border border-slate-200/60 rounded-lg">
            <div className="flex items-center gap-2 text-slate-500 text-xs font-medium uppercase tracking-wider mb-1">
              <Layers className="w-3.5 h-3.5 text-indigo-500" />
              Columns
            </div>
            <div className="text-2xl font-bold text-slate-900">
              {dataset.column_count ?? columns.length}
            </div>
          </div>

          <div className="p-4 bg-slate-50 border border-slate-200/60 rounded-lg">
            <div className="flex items-center gap-2 text-slate-500 text-xs font-medium uppercase tracking-wider mb-1">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
              Missing Values
            </div>
            <div className="text-2xl font-bold text-slate-900">
              {totalMissing.toLocaleString()}
              <span className="text-xs font-normal text-slate-500 ml-1.5">({overallMissingPct}%)</span>
            </div>
          </div>

          <div className="p-4 bg-slate-50 border border-slate-200/60 rounded-lg">
            <div className="flex items-center gap-2 text-slate-500 text-xs font-medium uppercase tracking-wider mb-1">
              <FileCheck2 className="w-3.5 h-3.5 text-emerald-500" />
              File Type / Size
            </div>
            <div className="text-2xl font-bold text-slate-900 uppercase">
              {dataset.file_type}
              <span className="text-xs font-normal text-slate-500 ml-1.5 lowercase">
                ({(dataset.file_size / 1024).toFixed(1)} KB)
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 px-6 gap-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab("schema")}
          className={`py-3.5 border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === "schema"
              ? "border-blue-600 text-blue-600 font-semibold"
              : "border-transparent text-slate-600 hover:text-slate-900"
          }`}
        >
          <Layers className="w-4 h-4" />
          Column Schema ({columns.length})
        </button>

        <button
          onClick={() => setActiveTab("numerical")}
          className={`py-3.5 border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === "numerical"
              ? "border-blue-600 text-blue-600 font-semibold"
              : "border-transparent text-slate-600 hover:text-slate-900"
          }`}
        >
          <Hash className="w-4 h-4" />
          Numerical Stats ({numericColumns.length})
        </button>

        <button
          onClick={() => setActiveTab("categorical")}
          className={`py-3.5 border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === "categorical"
              ? "border-blue-600 text-blue-600 font-semibold"
              : "border-transparent text-slate-600 hover:text-slate-900"
          }`}
        >
          <Type className="w-4 h-4" />
          Categorical Values ({categoricalColumns.length})
        </button>

        <button
          onClick={() => setActiveTab("quality")}
          className={`py-3.5 border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === "quality"
              ? "border-blue-600 text-blue-600 font-semibold"
              : "border-transparent text-slate-600 hover:text-slate-900"
          }`}
        >
          <AlertTriangle className="w-4 h-4" />
          Data Quality Checks
        </button>
      </div>

      {/* Tab Panels */}
      <div className="p-6">
        {/* 1. SCHEMA TAB */}
        {activeTab === "schema" && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 font-medium text-xs uppercase bg-slate-50/50">
                  <th className="py-3 px-4">Column</th>
                  <th className="py-3 px-4">Data Type</th>
                  <th className="py-3 px-4">Semantic Type</th>
                  <th className="py-3 px-4">Missing Count</th>
                  <th className="py-3 px-4">Missing Rate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {columns.map((col) => {
                  const meta = schemaInfo[col];
                  const miss = missingData[col] || { missing_count: 0, missing_percentage: 0 };
                  return (
                    <tr key={col} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3 px-4 font-medium text-slate-900">{col}</td>
                      <td className="py-3 px-4 font-mono text-xs text-slate-600">
                        <span className="px-2 py-0.5 bg-slate-100 rounded text-slate-700">
                          {meta?.dtype || "unknown"}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700">
                          {meta?.semantic_type || "generic"}
                        </span>
                      </td>
                      <td className="py-3 px-4">{miss.missing_count}</td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                            <div
                              className="bg-amber-500 h-1.5 rounded-full"
                              style={{ width: `${Math.min(miss.missing_percentage, 100)}%` }}
                            />
                          </div>
                          <span className="text-xs text-slate-500">{miss.missing_percentage}%</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* 2. NUMERICAL STATS TAB */}
        {activeTab === "numerical" && (
          <div className="space-y-4">
            {numericColumns.length === 0 ? (
              <p className="text-sm text-slate-500 italic">No numeric columns detected in this dataset.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-500 font-medium text-xs uppercase bg-slate-50/50">
                      <th className="py-3 px-4">Column</th>
                      <th className="py-3 px-4">Mean</th>
                      <th className="py-3 px-4">Std Dev</th>
                      <th className="py-3 px-4">Min</th>
                      <th className="py-3 px-4">25%</th>
                      <th className="py-3 px-4">Median</th>
                      <th className="py-3 px-4">75%</th>
                      <th className="py-3 px-4">Max</th>
                      <th className="py-3 px-4">Unique</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-800">
                    {numericColumns.map((col) => {
                      const stats = numericStats[col];
                      return (
                        <tr key={col} className="hover:bg-slate-50/80 transition-colors">
                          <td className="py-3 px-4 font-medium text-slate-900">{col}</td>
                          <td className="py-3 px-4 font-mono text-xs">{stats.mean?.toFixed(2)}</td>
                          <td className="py-3 px-4 font-mono text-xs">{stats.std?.toFixed(2)}</td>
                          <td className="py-3 px-4 font-mono text-xs">{stats.min?.toFixed(2)}</td>
                          <td className="py-3 px-4 font-mono text-xs">{stats.q25?.toFixed(2)}</td>
                          <td className="py-3 px-4 font-mono text-xs">{stats.median?.toFixed(2)}</td>
                          <td className="py-3 px-4 font-mono text-xs">{stats.q75?.toFixed(2)}</td>
                          <td className="py-3 px-4 font-mono text-xs">{stats.max?.toFixed(2)}</td>
                          <td className="py-3 px-4">{stats.unique_count}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* 3. CATEGORICAL STATS TAB */}
        {activeTab === "categorical" && (
          <div className="space-y-4">
            {categoricalColumns.length === 0 ? (
              <p className="text-sm text-slate-500 italic">No categorical columns detected in this dataset.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {categoricalColumns.map((col) => {
                  const cat = categoricalStats[col];
                  return (
                    <div key={col} className="p-4 border border-slate-200 rounded-lg bg-slate-50/40">
                      <div className="flex justify-between items-center mb-2">
                        <h4 className="font-semibold text-slate-900 text-sm">{col}</h4>
                        <span className="text-xs text-slate-500">
                          {cat.unique_count} unique values
                        </span>
                      </div>
                      <div className="space-y-1.5 mt-3">
                        {Object.entries(cat.frequencies || {}).slice(0, 5).map(([val, count]) => (
                          <div key={val} className="flex justify-between items-center text-xs">
                            <span className="truncate max-w-[200px] text-slate-700">{val || "(empty)"}</span>
                            <span className="font-mono text-slate-500">{count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* 4. DATA QUALITY CHECKS */}
        {activeTab === "quality" && (
          <div className="space-y-4 text-sm">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-lg border border-slate-200 bg-slate-50/50">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                  Duplicated Rows
                </span>
                <span className="text-xl font-bold text-slate-900">
                  {dataQuality.duplicated_rows} rows
                </span>
              </div>

              <div className="p-4 rounded-lg border border-slate-200 bg-slate-50/50">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                  Constant Columns (Zero Variance)
                </span>
                <span className="text-sm font-medium text-slate-800">
                  {dataQuality.constant_columns.length > 0
                    ? dataQuality.constant_columns.join(", ")
                    : "None detected"}
                </span>
              </div>

              <div className="p-4 rounded-lg border border-slate-200 bg-slate-50/50">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                  Potential ID / Key Columns
                </span>
                <span className="text-sm font-medium text-slate-800">
                  {dataQuality.potential_id_columns.length > 0
                    ? dataQuality.potential_id_columns.join(", ")
                    : "None detected"}
                </span>
              </div>

              <div className="p-4 rounded-lg border border-slate-200 bg-slate-50/50">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                  High Cardinality Columns
                </span>
                <span className="text-sm font-medium text-slate-800">
                  {dataQuality.high_cardinality_columns.length > 0
                    ? dataQuality.high_cardinality_columns.join(", ")
                    : "None detected"}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
