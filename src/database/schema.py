"""
SQLite database schema for ILI system.
"""

from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Index,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class InspectionRun(Base):
    """Inspection run metadata"""

    __tablename__ = "inspection_runs"

    id = Column(String, primary_key=True)
    pipeline_segment = Column(String, nullable=False)
    inspection_date = Column(DateTime, nullable=False)
    vendor = Column(String)
    tool_type = Column(String)
    file_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    anomalies = relationship("Anomaly", back_populates="run", cascade="all, delete-orphan")
    reference_points = relationship(
        "ReferencePoint", back_populates="run", cascade="all, delete-orphan"
    )


class Anomaly(Base):
    """Anomaly record"""

    __tablename__ = "anomalies"

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("inspection_runs.id"), nullable=False)
    distance = Column(Float, nullable=False)
    corrected_distance = Column(Float)
    clock_position = Column(Float, nullable=False)
    depth_pct = Column(Float, nullable=False)
    length = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    feature_type = Column(String, nullable=False)
    coating_type = Column(String)
    inspection_date = Column(DateTime, nullable=False)

    # Regulatory fields
    is_hca = Column(Boolean, default=False)
    distance_to_nearest_weld_ft = Column(Float)
    is_cluster = Column(Boolean, default=False)
    coating_condition = Column(String)
    maop_ratio = Column(Float)
    wall_thickness_in = Column(Float)

    # Risk scoring fields
    risk_score = Column(Integer)
    risk_level = Column(String)
    cfr_classification = Column(String)
    asme_classification = Column(String)
    action_required = Column(String)
    inspection_interval_years = Column(Float)
    next_inspection_date = Column(DateTime)

    # Growth fields
    growth_rate_pct_per_year = Column(Float)
    growth_rate_mils_per_year = Column(Float)

    # Compliance flags
    exceeds_cfr_192_933 = Column(Boolean, default=False)
    exceeds_cfr_195_452 = Column(Boolean, default=False)
    exceeds_asme_growth = Column(Boolean, default=False)
    high_growth_flag = Column(Boolean, default=False)

    # Relationships
    run = relationship("InspectionRun", back_populates="anomalies")
    matches_as_anomaly1 = relationship(
        "Match", foreign_keys="Match.anomaly1_id", back_populates="anomaly1"
    )
    matches_as_anomaly2 = relationship(
        "Match", foreign_keys="Match.anomaly2_id", back_populates="anomaly2"
    )

    # Indexes
    __table_args__ = (
        Index("idx_anomalies_run", "run_id"),
        Index("idx_anomalies_corrected_distance", "corrected_distance"),
        Index("idx_anomalies_risk_score", "risk_score"),
        Index("idx_anomalies_cfr_classification", "cfr_classification"),
    )


class ReferencePoint(Base):
    """Reference point for alignment"""

    __tablename__ = "reference_points"

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("inspection_runs.id"), nullable=False)
    distance = Column(Float, nullable=False)
    point_type = Column(String, nullable=False)
    description = Column(Text)

    # Relationships
    run = relationship("InspectionRun", back_populates="reference_points")

    # Indexes
    __table_args__ = (Index("idx_reference_points_run", "run_id"),)


class Match(Base):
    """Matched anomaly pair"""

    __tablename__ = "matches"

    id = Column(String, primary_key=True)
    anomaly1_id = Column(String, ForeignKey("anomalies.id"), nullable=False)
    anomaly2_id = Column(String, ForeignKey("anomalies.id"), nullable=False)
    similarity_score = Column(Float, nullable=False)
    confidence = Column(String, nullable=False)
    distance_similarity = Column(Float)
    clock_similarity = Column(Float)
    type_similarity = Column(Float)
    depth_similarity = Column(Float)
    length_similarity = Column(Float)
    width_similarity = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    anomaly1 = relationship("Anomaly", foreign_keys=[anomaly1_id], back_populates="matches_as_anomaly1")
    anomaly2 = relationship("Anomaly", foreign_keys=[anomaly2_id], back_populates="matches_as_anomaly2")
    growth_metrics = relationship("GrowthMetric", back_populates="match", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_matches_anomaly1", "anomaly1_id"),
        Index("idx_matches_anomaly2", "anomaly2_id"),
    )


class GrowthMetric(Base):
    """Growth metrics for matched pair"""

    __tablename__ = "growth_metrics"

    id = Column(String, primary_key=True)
    match_id = Column(String, ForeignKey("matches.id"), nullable=False)
    time_interval_years = Column(Float, nullable=False)
    depth_growth_rate = Column(Float, nullable=False)
    length_growth_rate = Column(Float, nullable=False)
    width_growth_rate = Column(Float, nullable=False)
    is_rapid_growth = Column(Boolean, nullable=False)
    risk_score = Column(Float, nullable=False)

    # Relationships
    match = relationship("Match", back_populates="growth_metrics")

    # Indexes
    __table_args__ = (
        Index("idx_growth_metrics_match", "match_id"),
        Index("idx_growth_metrics_rapid_growth", "is_rapid_growth"),
    )


class Prediction(Base):
    """ML prediction for future depth"""

    __tablename__ = "predictions"

    id = Column(String, primary_key=True)
    anomaly_id = Column(String, ForeignKey("anomalies.id"), nullable=False)
    predicted_depth_pct = Column(Float, nullable=False)
    years_ahead = Column(Float, nullable=False)
    confidence_interval_lower = Column(Float)
    confidence_interval_upper = Column(Float)
    model_version = Column(String)
    model_confidence = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes
    __table_args__ = (Index("idx_predictions_anomaly", "anomaly_id"),)


class AlignmentResult(Base):
    """DTW alignment result"""

    __tablename__ = "alignment_results"

    id = Column(String, primary_key=True)
    run1_id = Column(String, ForeignKey("inspection_runs.id"), nullable=False)
    run2_id = Column(String, ForeignKey("inspection_runs.id"), nullable=False)
    match_rate = Column(Float, nullable=False)
    rmse = Column(Float, nullable=False)
    correction_function_params = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_alignment_run1", "run1_id"),
        Index("idx_alignment_run2", "run2_id"),
    )


class ComplianceReport(Base):
    """Compliance report metadata"""

    __tablename__ = "compliance_reports"

    id = Column(String, primary_key=True)
    pipeline_segment = Column(String, nullable=False)
    assessment_period_start = Column(DateTime, nullable=False)
    assessment_period_end = Column(DateTime, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    total_anomalies = Column(Integer, nullable=False)
    immediate_action_count = Column(Integer, nullable=False)
    scheduled_action_count = Column(Integer, nullable=False)
    critical_count = Column(Integer, nullable=False)
    high_count = Column(Integer, nullable=False)
    moderate_count = Column(Integer, nullable=False)
    low_count = Column(Integer, nullable=False)
    acceptable_count = Column(Integer, nullable=False)
    highest_risk_score = Column(Integer, nullable=False)
    average_growth_rate = Column(Float, nullable=False)
    compliance_status = Column(String, nullable=False)
    report_file_path = Column(String)

    # Indexes
    __table_args__ = (
        Index("idx_compliance_reports_segment", "pipeline_segment"),
        Index("idx_compliance_reports_generated", "generated_at"),
    )


def create_database(db_url: str = "sqlite:///ili_system.db") -> None:
    """Create all database tables"""
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    return engine


def drop_database(db_url: str = "sqlite:///ili_system.db") -> None:
    """Drop all database tables"""
    engine = create_engine(db_url, echo=False)
    Base.metadata.drop_all(engine)
