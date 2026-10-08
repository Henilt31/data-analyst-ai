import { Dataset, DatasetProfile, ResearchQuestion, AnalysisRun, Report } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = {
  async getDatasets(): Promise<Dataset[]> {
    const res = await fetch(`${API_BASE}/datasets`);
    if (!res.ok) throw new Error("Failed to fetch datasets");
    return res.json();
  },

  async getDataset(id: string): Promise<Dataset> {
    const res = await fetch(`${API_BASE}/datasets/${id}`);
    if (!res.ok) throw new Error("Failed to fetch dataset");
    return res.json();
  },

  async uploadDataset(file: File): Promise<Dataset> {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE}/datasets`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Upload failed");
    }
    return res.json();
  },

  async getProfile(datasetId: string): Promise<DatasetProfile> {
    const res = await fetch(`${API_BASE}/datasets/${datasetId}/profile`);
    if (!res.ok) throw new Error("Failed to fetch dataset profile");
    return res.json();
  },

  async generateQuestions(datasetId: string, ragEnabled: boolean = false): Promise<ResearchQuestion[]> {
    const res = await fetch(`${API_BASE}/datasets/${datasetId}/questions?rag_enabled=${ragEnabled}`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Failed to generate research questions");
    return res.json();
  },

  async getQuestions(datasetId: string): Promise<ResearchQuestion[]> {
    const res = await fetch(`${API_BASE}/datasets/${datasetId}/questions`);
    if (!res.ok) throw new Error("Failed to fetch questions");
    return res.json();
  },

  async triggerRun(questionId: string, datasetId: string): Promise<AnalysisRun> {
    const res = await fetch(`${API_BASE}/runs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question_id: questionId, dataset_id: datasetId }),
    });
    if (!res.ok) throw new Error("Failed to trigger analysis run");
    return res.json();
  },

  async getRun(runId: string): Promise<AnalysisRun> {
    const res = await fetch(`${API_BASE}/runs/${runId}`);
    if (!res.ok) throw new Error("Failed to fetch run details");
    return res.json();
  },

  async generateReport(datasetId: string): Promise<Report> {
    const res = await fetch(`${API_BASE}/datasets/${datasetId}/report`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Failed to generate report");
    return res.json();
  },

  async getReport(datasetId: string): Promise<Report> {
    const res = await fetch(`${API_BASE}/datasets/${datasetId}/report`);
    if (!res.ok) throw new Error("Report not generated yet");
    return res.json();
  },

  getWebSocketUrl(datasetId: string): string {
    const wsBase = API_BASE.replace(/^http/, "ws");
    return `${wsBase}/ws/datasets/${datasetId}/status`;
  }
};
