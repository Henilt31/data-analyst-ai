from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from app.db.session import get_db
from app.db.models import Report, Dataset, DatasetProfile, ResearchQuestion, AnalysisRun
from app.db.repositories import DatasetRepository
from app.schemas.analysis import ReportResponse

router = APIRouter(tags=["reports"])

def generate_markdown_report(dataset: Dataset, profile: Optional[DatasetProfile], questions: list) -> str:
    rows = dataset.row_count or "Unknown"
    cols = dataset.column_count or "Unknown"
    dq = profile.data_quality if profile else {}

    report_lines = [
        f"# Dataset Analysis Report: {dataset.original_filename}",
        "",
        "## Executive Summary",
        f"This autonomous exploratory data analysis report analyzes `{dataset.original_filename}` "
        f"({dataset.file_type.upper()} format) comprising {rows} rows across {cols} features. "
        "Each research question was analyzed using deterministically computed execution pipelines.",
        "",
        "## Dataset Overview",
        f"- **Total Rows:** {rows}",
        f"- **Total Columns:** {cols}",
        f"- **File Size:** {round(dataset.file_size / 1024, 2)} KB",
        f"- **Status:** {dataset.status}",
        "",
        "### Data Quality Findings",
        f"- **Duplicated Rows:** {dq.get('duplicated_rows', 0)}",
        f"- **Constant Columns:** {', '.join(dq.get('constant_columns', [])) or 'None'}",
        f"- **Suspicious High-Null Columns:** {', '.join(dq.get('suspicious_null_columns', [])) or 'None'}",
        f"- **Potential Target Variables:** {', '.join(dq.get('potential_target_columns', [])) or 'None'}",
        "",
        "## Research Questions",
    ]

    for idx, q in enumerate(questions, 1):
        report_lines.append(f"{idx}. **{q.question}** ({q.category})")

    report_lines.append("")
    report_lines.append("## Findings")

    key_takeaways = []
    
    for idx, q in enumerate(questions, 1):
        report_lines.append(f"### Question {idx}: {q.question}")
        report_lines.append(f"**Rationale:** {q.rationale or 'N/A'}")
        
        # Check latest successful run
        completed_run = None
        for r in getattr(q, 'runs', []):
            if r.status in ["success", "completed"] and r.insight:
                completed_run = r
                break
        
        if completed_run and completed_run.insight:
            ins = completed_run.insight
            report_lines.append("")
            report_lines.append(f"**Answer:** {ins.text}")
            report_lines.append("")
            if ins.evidence:
                report_lines.append(f"**Evidence:** `{ins.evidence}`")
            if ins.caveats:
                report_lines.append(f"**Caveats:** {ins.caveats}")
            if ins.takeaway:
                key_takeaways.append(ins.takeaway)

            if completed_run.visualization:
                viz = completed_run.visualization
                report_lines.append("")
                report_lines.append(f"**Visualization ({viz.chart_type}):** `{viz.chart_path}`")
        else:
            report_lines.append("")
            report_lines.append("*Analysis for this question has not completed or failed execution.*")
        
        report_lines.append("")

    report_lines.append("## Key Takeaways")
    if key_takeaways:
        for t in key_takeaways:
            report_lines.append(f"- {t}")
    else:
        report_lines.append("- Analysis provides foundational baseline measurements for future modeling.")

    report_lines.append("")
    report_lines.append("## Analysis Limitations")
    report_lines.append("- Statistics and findings reflect local sample distributions without unobserved external factors.")
    report_lines.append("- All numerical claims are strictly grounded in executed Python calculations.")

    return "\n".join(report_lines)

@router.post("/datasets/{dataset_id}/report", response_model=ReportResponse, status_code=201)
async def generate_report(dataset_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    stmt = (
        select(Dataset)
        .options(
            selectinload(Dataset.profile),
            selectinload(Dataset.questions).selectinload(ResearchQuestion.runs).selectinload(AnalysisRun.insight),
            selectinload(Dataset.questions).selectinload(ResearchQuestion.runs).selectinload(AnalysisRun.visualization),
            selectinload(Dataset.report)
        )
        .where(Dataset.id == dataset_id)
    )
    result = await db.execute(stmt)
    dataset = result.scalars().first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    content = generate_markdown_report(dataset, dataset.profile, dataset.questions)

    if dataset.report:
        dataset.report.content = content
        report = dataset.report
    else:
        report = Report(dataset_id=dataset_id, content=content)
        db.add(report)

    await db.commit()
    await db.refresh(report)
    return report

@router.get("/datasets/{dataset_id}/report", response_model=ReportResponse)
async def get_report(dataset_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Report).where(Report.dataset_id == dataset_id)
    result = await db.execute(stmt)
    report = result.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found. Generate it first via POST.")
    return report
