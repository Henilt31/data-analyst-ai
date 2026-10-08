"use client";

import React, { useState, useRef } from "react";
import { UploadCloud, AlertCircle, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { Dataset } from "@/types";

interface DatasetUploadProps {
  onUploadSuccess: (dataset: Dataset) => void;
}

export const DatasetUpload: React.FC<DatasetUploadProps> = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      await processFile(e.target.files[0]);
    }
  };

  const processFile = async (file: File) => {
    const validExtensions = [".csv", ".json", ".xlsx", ".xls", ".parquet"];
    const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();

    if (!validExtensions.includes(ext)) {
      setError(`Unsupported file format. Please upload CSV, JSON, Parquet, or Excel files.`);
      return;
    }

    if (file.size > 100 * 1024 * 1024) {
      setError("File exceeds maximum allowed size of 100MB.");
      return;
    }

    try {
      setIsUploading(true);
      setError(null);
      const dataset = await api.uploadDataset(file);
      onUploadSuccess(dataset);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to upload and validate dataset.";
      setError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="w-full">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer transition-all duration-200 ${
          isDragging
            ? "border-blue-500 bg-blue-50/50 scale-[1.01]"
            : "border-slate-300 hover:border-slate-400 bg-slate-50/50 hover:bg-slate-50"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".csv,.json,.xlsx,.xls,.parquet"
          onChange={handleFileChange}
          disabled={isUploading}
        />

        <div className="w-14 h-14 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 mb-4 shadow-sm">
          {isUploading ? (
            <Loader2 className="w-7 h-7 animate-spin" />
          ) : (
            <UploadCloud className="w-7 h-7" />
          )}
        </div>

        <h3 className="text-base font-semibold text-slate-800 mb-1">
          {isUploading ? "Uploading & Profiling Dataset..." : "Drag & drop your dataset here"}
        </h3>
        <p className="text-sm text-slate-500 mb-4 text-center max-w-sm">
          Supports CSV, JSON, Parquet, and Excel up to 100MB. Processed completely local-first.
        </p>

        <div className="flex gap-2">
          {["CSV", "JSON", "Parquet", "Excel"].map((badge) => (
            <span
              key={badge}
              className="text-xs px-2.5 py-1 bg-white border border-slate-200 rounded-md font-medium text-slate-600 shadow-2xs"
            >
              {badge}
            </span>
          ))}
        </div>
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-sm text-red-700">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};
