"""
CRUD operations for ILI database.
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from src.database.schema import (
    InspectionRun,
    Anomaly,
    ReferencePoint,
    Match,
    GrowthMetric,
    Prediction,
    AlignmentResult,
    ComplianceReport,
)
from src.data_models.models import (
    AnomalyRecord,
    ReferencePoint as ReferencePointModel,
    Match as MatchModel,
    GrowthMetrics,
    Prediction as PredictionModel,
    AlignmentResult as AlignmentResultModel,
    ComplianceReport as ComplianceReportModel,
)


# Inspection Run CRUD
def create_inspection_run(
    session: Session,
    run_id: str,
    pipeline_segment: str,
    inspection_date: datetime,
    vendor: str = None,
    tool_type: str = None,
    file_path: str = None,
) -> InspectionRun:
    """Create a new inspection run"""
    run = InspectionRun(
        id=run_id,
        pipeline_segment=pipeline_segment,
        inspection_date=inspection_date,
        vendor=vendor,
        tool_type=tool_type,
        file_path=file_path,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def get_inspection_run(session: Session, run_id: str) -> Optional[InspectionRun]:
    """Get inspection run by ID"""
    return session.query(InspectionRun).filter(InspectionRun.id == run_id).first()


def get_all_inspection_runs(session: Session) -> List[InspectionRun]:
    """Get all inspection runs"""
    return session.query(InspectionRun).all()


# Anomaly CRUD
def create_anomaly(session: Session, anomaly: AnomalyRecord) -> Anomaly:
    """Create a new anomaly"""
    db_anomaly = Anomaly(
        id=anomaly.id,
        run_id=anomaly.run_id,
        distance=anomaly.distance,
        clock_position=anomaly.clock_position,
        depth_pct=anomaly.depth_pct,
        length=anomaly.length,
        width=anomaly.width,
        feature_type=anomaly.feature_type,
        coating_type=anomaly.coating_type,
        inspection_date=anomaly.inspection_date,
    )
    session.add(db_anomaly)
    session.commit()
    session.refresh(db_anomaly)
    return db_anomaly


def bulk_create_anomalies(session: Session, anomalies: List[AnomalyRecord]) -> List[Anomaly]:
    """Bulk create anomalies"""
    db_anomalies = [
        Anomaly(
            id=a.id,
            run_id=a.run_id,
            distance=a.distance,
            clock_position=a.clock_position,
            depth_pct=a.depth_pct,
            length=a.length,
            width=a.width,
            feature_type=a.feature_type,
            coating_type=a.coating_type,
            inspection_date=a.inspection_date,
        )
        for a in anomalies
    ]
    session.bulk_save_objects(db_anomalies)
    session.commit()
    return db_anomalies


def get_anomaly(session: Session, anomaly_id: str) -> Optional[Anomaly]:
    """Get anomaly by ID"""
    return session.query(Anomaly).filter(Anomaly.id == anomaly_id).first()


def get_anomalies_by_run(session: Session, run_id: str) -> List[Anomaly]:
    """Get all anomalies for a run"""
    return session.query(Anomaly).filter(Anomaly.run_id == run_id).all()


def update_anomaly_corrected_distance(
    session: Session, anomaly_id: str, corrected_distance: float
) -> Anomaly:
    """Update anomaly corrected distance"""
    anomaly = get_anomaly(session, anomaly_id)
    if anomaly:
        anomaly.corrected_distance = corrected_distance
        session.commit()
        session.refresh(anomaly)
    return anomaly


def update_anomaly_regulatory_fields(
    session: Session,
    anomaly_id: str,
    risk_score: int = None,
    risk_level: str = None,
    cfr_classification: str = None,
    asme_classification: str = None,
    action_required: str = None,
    inspection_interval_years: float = None,
    next_inspection_date: datetime = None,
    **kwargs,
) -> Anomaly:
    """Update anomaly regulatory fields"""
    anomaly = get_anomaly(session, anomaly_id)
    if anomaly:
        if risk_score is not None:
            anomaly.risk_score = risk_score
        if risk_level is not None:
            anomaly.risk_level = risk_level
        if cfr_classification is not None:
            anomaly.cfr_classification = cfr_classification
        if asme_classification is not None:
            anomaly.asme_classification = asme_classification
        if action_required is not None:
            anomaly.action_required = action_required
        if inspection_interval_years is not None:
            anomaly.inspection_interval_years = inspection_interval_years
        if next_inspection_date is not None:
            anomaly.next_inspection_date = next_inspection_date

        # Update any additional fields
        for key, value in kwargs.items():
            if hasattr(anomaly, key):
                setattr(anomaly, key, value)

        session.commit()
        session.refresh(anomaly)
    return anomaly


# Reference Point CRUD
def create_reference_point(
    session: Session, ref_point: ReferencePointModel
) -> ReferencePoint:
    """Create a new reference point"""
    db_ref_point = ReferencePoint(
        id=ref_point.id,
        run_id=ref_point.run_id,
        distance=ref_point.distance,
        point_type=ref_point.point_type,
        description=ref_point.description,
    )
    session.add(db_ref_point)
    session.commit()
    session.refresh(db_ref_point)
    return db_ref_point


def get_reference_points_by_run(session: Session, run_id: str) -> List[ReferencePoint]:
    """Get all reference points for a run"""
    return session.query(ReferencePoint).filter(ReferencePoint.run_id == run_id).all()


# Match CRUD
def create_match(session: Session, match: MatchModel) -> Match:
    """Create a new match"""
    db_match = Match(
        id=match.id,
        anomaly1_id=match.anomaly1_id,
        anomaly2_id=match.anomaly2_id,
        similarity_score=match.similarity_score,
        confidence=match.confidence,
        distance_similarity=match.distance_similarity,
        clock_similarity=match.clock_similarity,
        type_similarity=match.type_similarity,
        depth_similarity=match.depth_similarity,
        length_similarity=match.length_similarity,
        width_similarity=match.width_similarity,
    )
    session.add(db_match)
    session.commit()
    session.refresh(db_match)
    return db_match


def get_matches_by_run_pair(
    session: Session, run1_id: str, run2_id: str
) -> List[Match]:
    """Get all matches between two runs"""
    return (
        session.query(Match)
        .join(Anomaly, Match.anomaly1_id == Anomaly.id)
        .filter(Anomaly.run_id == run1_id)
        .all()
    )


# Growth Metric CRUD
def create_growth_metric(session: Session, growth: GrowthMetrics) -> GrowthMetric:
    """Create a new growth metric"""
    db_growth = GrowthMetric(
        id=str(uuid.uuid4()),
        match_id=growth.match_id,
        time_interval_years=growth.time_interval_years,
        depth_growth_rate=growth.depth_growth_rate,
        length_growth_rate=growth.length_growth_rate,
        width_growth_rate=growth.width_growth_rate,
        is_rapid_growth=growth.is_rapid_growth,
        risk_score=growth.risk_score,
    )
    session.add(db_growth)
    session.commit()
    session.refresh(db_growth)
    return db_growth


# Prediction CRUD
def create_prediction(session: Session, prediction: PredictionModel) -> Prediction:
    """Create a new prediction"""
    db_prediction = Prediction(
        id=str(uuid.uuid4()),
        anomaly_id=prediction.anomaly_id,
        predicted_depth_pct=prediction.predicted_depth_pct,
        years_ahead=prediction.years_ahead,
        confidence_interval_lower=prediction.confidence_interval_lower,
        confidence_interval_upper=prediction.confidence_interval_upper,
        model_confidence=prediction.model_confidence,
    )
    session.add(db_prediction)
    session.commit()
    session.refresh(db_prediction)
    return db_prediction


# Alignment Result CRUD
def create_alignment_result(
    session: Session, alignment: AlignmentResultModel
) -> AlignmentResult:
    """Create a new alignment result"""
    import json

    db_alignment = AlignmentResult(
        id=str(uuid.uuid4()),
        run1_id=alignment.run1_id,
        run2_id=alignment.run2_id,
        match_rate=alignment.match_rate,
        rmse=alignment.rmse,
        correction_function_params=json.dumps(alignment.correction_function_params),
    )
    session.add(db_alignment)
    session.commit()
    session.refresh(db_alignment)
    return db_alignment


# Compliance Report CRUD
def create_compliance_report(
    session: Session, report: ComplianceReportModel, report_file_path: str = None
) -> ComplianceReport:
    """Create a new compliance report"""
    db_report = ComplianceReport(
        id=report.report_id,
        pipeline_segment=report.pipeline_segment,
        assessment_period_start=report.assessment_period_start,
        assessment_period_end=report.assessment_period_end,
        generated_at=report.generated_at,
        total_anomalies=report.total_anomalies,
        immediate_action_count=report.immediate_action_count,
        scheduled_action_count=report.scheduled_action_count,
        critical_count=report.critical_count,
        high_count=report.high_count,
        moderate_count=report.moderate_count,
        low_count=report.low_count,
        acceptable_count=report.acceptable_count,
        highest_risk_score=report.highest_risk_score,
        average_growth_rate=report.average_growth_rate,
        compliance_status=report.compliance_status,
        report_file_path=report_file_path,
    )
    session.add(db_report)
    session.commit()
    session.refresh(db_report)
    return db_report


def get_compliance_reports_by_segment(
    session: Session, pipeline_segment: str
) -> List[ComplianceReport]:
    """Get all compliance reports for a pipeline segment"""
    return (
        session.query(ComplianceReport)
        .filter(ComplianceReport.pipeline_segment == pipeline_segment)
        .order_by(ComplianceReport.generated_at.desc())
        .all()
    )
