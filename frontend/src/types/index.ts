export interface Dataset {
  id: string;
  original_filename: string;
  stored_path: string;
  file_type: string;
  file_size: number;
  created_at: string;
  status: string;
  row_count?: number;
  column_count?: number;
}

export interface DatasetProfile {
  id: number;
  dataset_id: string;
  schema_info?: Record<string, { dtype: string; semantic_type: string }>;
  missing_data?: Record<string, { missing_count: number; missing_percentage: number }>;
  numeric_stats?: Record<string, {
    min: number;
    max: number;
    mean: number;
    median: number;
    std: number;
    q25: number;
    q50: number;
    q75: number;
    unique_count: number;
  }>;
  categorical_stats?: Record<string, {
    unique_count: number;
    top_values: string[];
    frequencies: Record<string, number>;
  }>;
  datetime_stats?: Record<string, {
    min_date: string;
    max_date: string;
    temporal_range_days?: number;
  }>;
  data_quality?: {
    duplicated_rows: number;
    constant_columns: string[];
    high_cardinality_columns: string[];
    suspicious_null_columns: string[];
    potential_id_columns: string[];
    potential_target_columns: string[];
  };
  correlations?: Record<string, Record<string, number>>;
}

export interface ResearchQuestion {
  id: string;
  dataset_id: string;
  question: string;
  rationale?: string;
  columns_involved?: string[];
  category?: string;
}

export interface AnalysisAttempt {
  id: number;
  attempt_number: number;
  exit_code?: number;
  stdout?: string;
  stderr?: string;
  duration_ms?: number;
  status: string;
  failure_type?: string;
}

export interface Insight {
  id: number;
  run_id: string;
  text: string;
  evidence?: Record<string, unknown>;
  important_numbers?: Record<string, unknown>;
  caveats?: string;
  takeaway?: string;
}

export interface Visualization {
  id: number;
  run_id: string;
  chart_type: string;
  chart_path: string;
  title?: string;
  data?: Record<string, unknown>;
}

export interface AnalysisRun {
  id: string;
  question_id: string;
  status: string;
  created_at: string;
  attempts: AnalysisAttempt[];
  insight?: Insight;
  visualization?: Visualization;
}

export interface Report {
  id: number;
  dataset_id: string;
  content: string;
  created_at: string;
}
