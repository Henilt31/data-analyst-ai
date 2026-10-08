import pytest
from app.api.reports import generate_markdown_report
from app.db.models import Dataset, DatasetProfile, ResearchQuestion, AnalysisRun, Insight

def test_generate_markdown_report_structure():
    dataset = Dataset(
        id="ds_rep_1",
        original_filename="customer_churn.csv",
        file_type="csv",
        file_size=20480,
        status="profiled",
        row_count=5000,
        column_count=12
    )

    profile = DatasetProfile(
        dataset_id="ds_rep_1",
        data_quality={
            "duplicated_rows": 0,
            "constant_columns": ["country"],
            "suspicious_null_columns": [],
            "potential_target_columns": ["churn"]
        }
    )

    question = ResearchQuestion(
        id="q_rep_1",
        dataset_id="ds_rep_1",
        question="What factors drive customer churn?",
        rationale="Identify churn prevention opportunities.",
        category="segmentation"
    )

    run = AnalysisRun(
        id="run_rep_1",
        question_id="q_rep_1",
        status="success"
    )

    insight = Insight(
        id=1,
        run_id="run_rep_1",
        text="High monthly fee is the leading driver of customer churn.",
        important_numbers={"churn_rate_high_fee": 0.38, "churn_rate_low_fee": 0.12},
        takeaway="Focus retention discounts on customers with monthly fees above $80.",
        caveats="Sample limited to postpaid customers."
    )
    run.insight = insight
    question.runs = [run]

    report_md = generate_markdown_report(dataset, profile, [question])

    assert "# Dataset Analysis Report: customer_churn.csv" in report_md
    assert "## Executive Summary" in report_md
    assert "5000 rows across 12 features" in report_md
    assert "## Dataset Overview" in report_md
    assert "**Duplicated Rows:** 0" in report_md
    assert "High monthly fee is the leading driver" in report_md
    assert "Focus retention discounts" in report_md
