import os
import math
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from pathlib import Path

class ProfilingService:
    def load_dataset(self, file_path: str, file_type: str, max_rows: Optional[int] = 500000) -> pd.DataFrame:
        """
        Loads dataset with a safety limit to prevent OOM errors on massive files.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_type == "csv":
            return pd.read_csv(file_path, nrows=max_rows)
        elif file_type == "json":
            return pd.read_json(file_path)
        elif file_type == "xlsx":
            return pd.read_excel(file_path, nrows=max_rows)
        elif file_type == "parquet":
            return pd.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file type for profiling: {file_type}")

    def _clean_val(self, val: Any) -> Any:
        if val is None or (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
            return None
        if isinstance(val, (np.integer, int)):
            return int(val)
        if isinstance(val, (np.floating, float)):
            return float(val)
        if isinstance(val, (np.bool_, bool)):
            return bool(val)
        if isinstance(val, (pd.Timestamp, np.datetime64)):
            return str(val)
        return str(val)

    def infer_semantic_type(self, series: pd.Series, col_name: str) -> str:
        name_lower = col_name.lower()
        if name_lower in ["id", "uuid", "guid"] or name_lower.endswith("_id") or name_lower.startswith("id_"):
            return "id"
        
        if pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"
        if pd.api.types.is_bool_dtype(series):
            return "boolean"
        if pd.api.types.is_numeric_dtype(series):
            if series.nunique() == 2:
                return "boolean"
            return "numeric"
        
        # Check if text could be datetime
        if series.dropna().count() > 0 and (pd.api.types.is_string_dtype(series) or series.dtype == "object" or any(w in name_lower for w in ["date", "time", "year", "month"])):
            sample = series.dropna().astype(str).head(20)
            try:
                pd.to_datetime(sample, errors='raise')
                return "datetime"
            except (ValueError, TypeError, Exception):
                pass

        unique_ratio = series.nunique() / max(len(series), 1)
        if unique_ratio < 0.05 or series.nunique() <= 30:
            return "categorical"
        return "text"

    def profile_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        row_count, col_count = df.shape
        
        schema_info: Dict[str, Dict[str, str]] = {}
        missing_data: Dict[str, Dict[str, Any]] = {}
        numeric_stats: Dict[str, Dict[str, Any]] = {}
        categorical_stats: Dict[str, Dict[str, Any]] = {}
        datetime_stats: Dict[str, Dict[str, Any]] = {}
        
        for col in df.columns:
            series = df[col]
            semantic_type = self.infer_semantic_type(series, str(col))
            schema_info[str(col)] = {
                "dtype": str(series.dtype),
                "semantic_type": semantic_type
            }
            
            null_count = int(series.isnull().sum())
            null_pct = float(round((null_count / max(row_count, 1)) * 100, 2))
            missing_data[str(col)] = {
                "missing_count": null_count,
                "missing_percentage": null_pct
            }

            # Numeric columns
            if pd.api.types.is_numeric_dtype(series) and semantic_type != "boolean":
                valid = series.dropna()
                if len(valid) > 0:
                    numeric_stats[str(col)] = {
                        "min": self._clean_val(valid.min()),
                        "max": self._clean_val(valid.max()),
                        "mean": self._clean_val(round(float(valid.mean()), 4)),
                        "median": self._clean_val(round(float(valid.median()), 4)),
                        "std": self._clean_val(round(float(valid.std()), 4)) if len(valid) > 1 else 0.0,
                        "q25": self._clean_val(round(float(valid.quantile(0.25)), 4)),
                        "q50": self._clean_val(round(float(valid.quantile(0.50)), 4)),
                        "q75": self._clean_val(round(float(valid.quantile(0.75)), 4)),
                        "unique_count": int(valid.nunique())
                    }

            # Categorical / Text / Boolean
            if semantic_type in ["categorical", "boolean", "text"]:
                valid = series.dropna()
                val_counts = valid.value_counts().head(10)
                frequencies = {str(k): int(v) for k, v in val_counts.items()}
                categorical_stats[str(col)] = {
                    "unique_count": int(valid.nunique()),
                    "top_values": list(frequencies.keys())[:5],
                    "frequencies": frequencies
                }

            # Datetime
            if semantic_type == "datetime":
                try:
                    dt_series = pd.to_datetime(series.dropna(), errors='coerce').dropna()
                    if len(dt_series) > 0:
                        min_date = dt_series.min()
                        max_date = dt_series.max()
                        datetime_stats[str(col)] = {
                            "min_date": str(min_date),
                            "max_date": str(max_date),
                            "temporal_range_days": self._clean_val((max_date - min_date).days if hasattr(max_date - min_date, 'days') else None)
                        }
                except Exception:
                    pass

        # Data Quality Checks
        duplicated_rows = int(df.duplicated().sum())
        constant_columns = [str(c) for c in df.columns if df[c].nunique(dropna=False) <= 1]
        high_cardinality_columns = [
            str(c) for c, info in schema_info.items() 
            if info["semantic_type"] in ["categorical", "text"] and df[c].nunique() > 1000
        ]
        suspicious_null_columns = [
            str(c) for c, data in missing_data.items() if data["missing_percentage"] > 40.0
        ]
        potential_id_columns = [
            str(c) for c, info in schema_info.items() if info["semantic_type"] == "id"
        ]
        
        # Potential targets: low cardinality or specific names like target, label, churn, price, revenue
        potential_target_columns = []
        for c in df.columns:
            c_low = str(c).lower()
            if any(term in c_low for term in ["target", "label", "churn", "converted", "default", "status", "price", "revenue", "sales"]):
                potential_target_columns.append(str(c))

        data_quality = {
            "duplicated_rows": duplicated_rows,
            "constant_columns": constant_columns,
            "high_cardinality_columns": high_cardinality_columns,
            "suspicious_null_columns": suspicious_null_columns,
            "potential_id_columns": potential_id_columns,
            "potential_target_columns": list(set(potential_target_columns))
        }

        # Numeric correlations
        correlations: Dict[str, Dict[str, float]] = {}
        numeric_df = df.select_dtypes(include=[np.number])
        if not numeric_df.empty and numeric_df.shape[1] > 1:
            corr_matrix = numeric_df.corr().round(4)
            for c1 in corr_matrix.columns:
                correlations[str(c1)] = {}
                for c2 in corr_matrix.columns:
                    val = corr_matrix.loc[c1, c2]
                    correlations[str(c1)][str(c2)] = self._clean_val(val)

        return {
            "shape": {"rows": row_count, "columns": col_count},
            "schema_info": schema_info,
            "missing_data": missing_data,
            "numeric_stats": numeric_stats,
            "categorical_stats": categorical_stats,
            "datetime_stats": datetime_stats,
            "data_quality": data_quality,
            "correlations": correlations
        }

    def profile_file(self, file_path: str, file_type: str) -> Dict[str, Any]:
        df = self.load_dataset(file_path, file_type)
        return self.profile_dataframe(df)

profiling_service = ProfilingService()
