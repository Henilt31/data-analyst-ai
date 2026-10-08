from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from app.db.models import (
    Dataset, DatasetProfile, ResearchQuestion, AnalysisRun, 
    AnalysisAttempt, Insight, Visualization, Report, TelemetryTrial
)

class DatasetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_dataset(
        self, id: str, original_filename: str, stored_path: str, file_type: str, file_size: int
    ) -> Dataset:
        dataset = Dataset(
            id=id,
            original_filename=original_filename,
            stored_path=stored_path,
            file_type=file_type,
            file_size=file_size,
            status="uploaded"
        )
        self.session.add(dataset)
        await self.session.commit()
        await self.session.refresh(dataset)
        return dataset

    async def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        result = await self.session.execute(select(Dataset).where(Dataset.id == dataset_id))
        return result.scalars().first()

    async def list_datasets(self) -> List[Dataset]:
        result = await self.session.execute(select(Dataset).order_by(Dataset.created_at.desc()))
        return list(result.scalars().all())

    async def update_dataset_status(
        self, dataset_id: str, status: str, row_count: Optional[int] = None, column_count: Optional[int] = None
    ) -> Optional[Dataset]:
        dataset = await self.get_dataset(dataset_id)
        if dataset:
            dataset.status = status
            if row_count is not None:
                dataset.row_count = row_count
            if column_count is not None:
                dataset.column_count = column_count
            await self.session.commit()
            await self.session.refresh(dataset)
        return dataset

    async def save_profile(self, dataset_id: str, profile_data: dict) -> DatasetProfile:
        result = await self.session.execute(
            select(DatasetProfile).where(DatasetProfile.dataset_id == dataset_id)
        )
        profile = result.scalars().first()
        if not profile:
            profile = DatasetProfile(dataset_id=dataset_id)
            self.session.add(profile)
            
        profile.schema_info = profile_data.get("schema_info")
        profile.missing_data = profile_data.get("missing_data")
        profile.numeric_stats = profile_data.get("numeric_stats")
        profile.categorical_stats = profile_data.get("categorical_stats")
        profile.datetime_stats = profile_data.get("datetime_stats")
        profile.data_quality = profile_data.get("data_quality")
        profile.correlations = profile_data.get("correlations")
        
        shape = profile_data.get("shape", {})
        dataset = await self.get_dataset(dataset_id)
        if dataset:
            dataset.row_count = shape.get("rows")
            dataset.column_count = shape.get("columns")
            dataset.status = "profiled"

        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def get_profile(self, dataset_id: str) -> Optional[DatasetProfile]:
        result = await self.session.execute(
            select(DatasetProfile).where(DatasetProfile.dataset_id == dataset_id)
        )
        return result.scalars().first()

    async def create_research_questions(self, dataset_id: str, questions: list) -> List[ResearchQuestion]:
        import uuid
        created = []
        for q in questions:
            q_id = str(uuid.uuid4())
            rq = ResearchQuestion(
                id=q_id,
                dataset_id=dataset_id,
                question=q.get("question"),
                rationale=q.get("rationale"),
                columns_involved=q.get("columns", []),
                category=q.get("category")
            )
            self.session.add(rq)
            created.append(rq)
        await self.session.commit()
        for rq in created:
            await self.session.refresh(rq)
        return created

    async def get_research_questions(self, dataset_id: str) -> List[ResearchQuestion]:
        result = await self.session.execute(
            select(ResearchQuestion).where(ResearchQuestion.dataset_id == dataset_id)
        )
        return list(result.scalars().all())

    async def get_research_question(self, question_id: str) -> Optional[ResearchQuestion]:
        result = await self.session.execute(
            select(ResearchQuestion).where(ResearchQuestion.id == question_id)
        )
        return result.scalars().first()

    async def create_analysis_run(self, run_id: str, question_id: str) -> AnalysisRun:
        run = AnalysisRun(id=run_id, question_id=question_id, status="running")
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def save_run_results(self, run_id: str, state: dict) -> AnalysisRun:
        from sqlalchemy.orm import selectinload
        result = await self.session.execute(
            select(AnalysisRun).where(AnalysisRun.id == run_id)
        )
        run = result.scalars().first()
        if not run:
            return None

        run.status = state.get("status", "completed")

        # Save attempts
        for att in state.get("execution_history", []):
            attempt = AnalysisAttempt(
                run_id=run_id,
                attempt_number=att.get("attempt_number", 1),
                generated_code=att.get("generated_code"),
                exit_code=att.get("exit_code"),
                stdout=att.get("stdout"),
                stderr=att.get("stderr"),
                duration_ms=att.get("duration_ms"),
                status=att.get("status", "unknown"),
                failure_type=att.get("failure_type")
            )
            self.session.add(attempt)

        # Save insight if present
        insight_data = state.get("insight")
        if insight_data:
            insight = Insight(
                run_id=run_id,
                text=insight_data.get("text", ""),
                evidence=insight_data.get("evidence"),
                important_numbers=insight_data.get("important_numbers"),
                caveats=insight_data.get("caveats"),
                takeaway=insight_data.get("takeaway")
            )
            self.session.add(insight)

        # Save visualization if present
        viz_data = state.get("visualization")
        if viz_data:
            viz = Visualization(
                run_id=run_id,
                chart_type=viz_data.get("chart_type", "chart"),
                chart_path=viz_data.get("chart_path", ""),
                title=viz_data.get("title"),
                data=viz_data.get("data")
            )
            self.session.add(viz)

        await self.session.commit()
        return await self.get_run(run_id)

    async def get_run(self, run_id: str) -> Optional[AnalysisRun]:
        from sqlalchemy.orm import selectinload
        result = await self.session.execute(
            select(AnalysisRun)
            .options(
                selectinload(AnalysisRun.attempts),
                selectinload(AnalysisRun.insight),
                selectinload(AnalysisRun.visualization)
            )
            .where(AnalysisRun.id == run_id)
        )
        return result.scalars().first()

    async def get_insight(self, run_id_or_insight_id: str) -> Optional[Insight]:
        try:
            iid = int(run_id_or_insight_id)
            stmt = select(Insight).where(Insight.id == iid)
        except ValueError:
            stmt = select(Insight).where(Insight.run_id == run_id_or_insight_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()


