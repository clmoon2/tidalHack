"""
Unit tests for QualityReporter class.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import json
import tempfile
from pathlib import Path

from src.ingestion.quality_reporter import QualityReporter
from src.data_models.models import ValidationResult


class TestQualityReporter:
    """Tests for QualityReporter class."""

    @pytest.fixture
    def reporter(self):
        """Create a QualityReporter instance."""
        return QualityReporter()

    @pytest.fixture
    def sample_anomalies_df(self):
        """Create sample anomalies DataFrame."""
        return pd.DataFrame({
            "id": ["A1", "A2", "A3", "A4", "A5"],
            "run_id": ["RUN1"] * 5,
            "distance": [100.0, 200.0, 300.0, 400.0, 500.0],
            "clock_position": [3.0, 6.0, 9.0, 12.0, 3.0],
            "depth_pct": [25.0, 35.0, 55.0, 85.0, 45.0],
            "length": [4.5, 5.2, 3.8, 6.1, 4.0],
            "width": [2.3, 2.8, 2.1, 3.0, 2.5],
            "feature_type": ["external_corrosion", "external_corrosion", "internal_corrosion", "external_corrosion", "dent"],
            "coating_type": ["FBE", "FBE", None, "FBE", None],
            "inspection_date": [datetime(2020, 1, 1)] * 5
        })

    @pytest.fixture
    def sample_ref_points_df(self):
        """Create sample reference points DataFrame."""
        return pd.DataFrame({
            "id": ["R1", "R2", "R3", "R4", "R5"],
            "run_id": ["RUN1"] * 5,
            "distance": [50.0, 150.0, 250.0, 350.0, 450.0],
            "point_type": ["girth_weld", "girth_weld", "valve", "girth_weld", "tee"],
            "description": ["GW-001", "GW-002", "V-001", "GW-003", "T-001"]
        })

    @pytest.fixture
    def sample_validation_result(self):
        """Create sample validation result."""
        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            record_count=5,
            valid_count=5,
            invalid_count=0
        )

    @pytest.fixture
    def sample_validation_report(self):
        """Create sample validation report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "total_records": 5,
            "valid_records": 5,
            "invalid_records": 0,
            "validation_passed": True,
            "required_fields_present": True,
            "missing_fields": [],
            "validation_errors": [],
            "validation_warnings": [],
            "range_validation_errors": [],
            "imputation_log": [],
            "quality_metrics": {
                "depth_pct_min": 25.0,
                "depth_pct_max": 85.0,
                "depth_pct_mean": 49.0,
                "feature_type_distribution": {
                    "external_corrosion": 3,
                    "internal_corrosion": 1,
                    "dent": 1
                }
            }
        }

    @pytest.fixture
    def sample_imputation_log(self):
        """Create sample imputation log."""
        return [
            "Imputed 2 missing clock_position values using forward-fill",
            "Imputed 1 missing length values using median (4.50 inches)",
            "Imputed 1 missing width values using median (2.50 inches)"
        ]

    def test_generate_comprehensive_report(
        self,
        reporter,
        sample_anomalies_df,
        sample_ref_points_df,
        sample_validation_result,
        sample_validation_report,
        sample_imputation_log
    ):
        """Test generation of comprehensive quality report."""
        report = reporter.generate_comprehensive_report(
            anomalies_df=sample_anomalies_df,
            ref_points_df=sample_ref_points_df,
            validation_result=sample_validation_result,
            validation_report=sample_validation_report,
            imputation_log=sample_imputation_log,
            run_id="RUN1",
            file_path="data/test.csv"
        )
        
        # Check report structure
        assert "metadata" in report
        assert "summary" in report
        assert "validation" in report
        assert "data_quality" in report
        assert "imputation" in report
        assert "anomalies" in report
        assert "reference_points" in report
        assert "recommendations" in report
        
        # Check metadata
        assert report["metadata"]["run_id"] == "RUN1"
        assert report["metadata"]["file_path"] == "data/test.csv"
        assert "generated_at" in report["metadata"]
        
        # Check summary
        assert report["summary"]["total_records"] == 10  # 5 anomalies + 5 ref points
        assert report["summary"]["anomaly_count"] == 5
        assert report["summary"]["reference_point_count"] == 5
        assert report["summary"]["validation_status"] == "PASSED"
        assert "data_quality_score" in report["summary"]

    def test_summary_generation(
        self,
        reporter,
        sample_anomalies_df,
        sample_ref_points_df,
        sample_validation_result
    ):
        """Test summary statistics generation."""
        summary = reporter._generate_summary(
            sample_anomalies_df,
            sample_ref_points_df,
            sample_validation_result
        )
        
        assert summary["total_records"] == 10
        assert summary["anomaly_count"] == 5
        assert summary["reference_point_count"] == 5
        assert summary["validation_status"] == "PASSED"
        assert 0 <= summary["data_quality_score"] <= 100

    def test_quality_metrics_generation(
        self,
        reporter,
        sample_anomalies_df,
        sample_ref_points_df,
        sample_validation_report
    ):
        """Test quality metrics generation."""
        metrics = reporter._generate_quality_metrics(
            sample_anomalies_df,
            sample_ref_points_df,
            sample_validation_report
        )
        
        assert "completeness" in metrics
        assert "validity" in metrics
        assert "consistency" in metrics
        assert "anomaly_metrics" in metrics
        assert "missing_values" in metrics

    def test_anomaly_statistics(self, reporter, sample_anomalies_df):
        """Test anomaly statistics generation."""
        stats = reporter._generate_anomaly_statistics(sample_anomalies_df)
        
        assert stats["count"] == 5
        assert "by_type" in stats
        assert "depth_statistics" in stats
        assert "dimension_statistics" in stats
        assert "distance_coverage" in stats
        
        # Check depth statistics
        depth_stats = stats["depth_statistics"]
        assert depth_stats["min"] == 25.0
        assert depth_stats["max"] == 85.0
        assert depth_stats["critical_count"] == 1  # One anomaly > 80% (85%)
        assert depth_stats["high_count"] == 1  # One anomaly 50-80% (55%)
        assert depth_stats["moderate_count"] == 2  # Two anomalies 30-50% (35%, 45%)
        assert depth_stats["low_count"] == 1  # One anomaly < 30% (25%)

    def test_anomaly_statistics_empty_df(self, reporter):
        """Test anomaly statistics with empty DataFrame."""
        empty_df = pd.DataFrame()
        stats = reporter._generate_anomaly_statistics(empty_df)
        
        assert stats["count"] == 0
        assert stats["by_type"] == {}
        assert stats["depth_statistics"] == {}

    def test_reference_point_statistics(self, reporter, sample_ref_points_df):
        """Test reference point statistics generation."""
        stats = reporter._generate_reference_point_statistics(sample_ref_points_df)
        
        assert stats["count"] == 5
        assert "by_type" in stats
        assert "spacing" in stats
        
        # Check spacing statistics
        spacing = stats["spacing"]
        assert spacing["mean"] == 100.0  # Points are 100 feet apart
        assert spacing["min"] == 100.0
        assert spacing["max"] == 100.0

    def test_reference_point_statistics_empty_df(self, reporter):
        """Test reference point statistics with empty DataFrame."""
        empty_df = pd.DataFrame()
        stats = reporter._generate_reference_point_statistics(empty_df)
        
        assert stats["count"] == 0
        assert stats["by_type"] == {}
        assert stats["spacing"] == {}

    def test_imputation_summary(self, reporter, sample_imputation_log):
        """Test imputation log summarization."""
        summary = reporter._summarize_imputations(sample_imputation_log)
        
        assert summary["total_actions"] == 3
        assert "by_field" in summary
        assert "clock_position" in summary["by_field"]
        assert "length" in summary["by_field"]
        assert "width" in summary["by_field"]
        
        # Check counts
        assert summary["by_field"]["clock_position"]["count"] == 2
        assert summary["by_field"]["length"]["count"] == 1
        assert summary["by_field"]["width"]["count"] == 1

    def test_imputation_summary_empty_log(self, reporter):
        """Test imputation summary with empty log."""
        summary = reporter._summarize_imputations([])
        
        assert summary["total_actions"] == 0
        assert summary["by_field"] == {}

    def test_recommendations_validation_failed(self, reporter, sample_anomalies_df, sample_ref_points_df):
        """Test recommendations when validation fails."""
        validation_result = ValidationResult(
            is_valid=False,
            errors=["Error 1", "Error 2"],
            warnings=[],
            record_count=5,
            valid_count=3,
            invalid_count=2
        )
        
        recommendations = reporter._generate_recommendations(
            validation_result,
            [],
            sample_anomalies_df,
            sample_ref_points_df
        )
        
        # Should have critical recommendation about validation failure
        assert any("CRITICAL" in rec for rec in recommendations)
        assert any("2 records failed validation" in rec for rec in recommendations)

    def test_recommendations_imputation_performed(self, reporter, sample_anomalies_df, sample_ref_points_df, sample_validation_result):
        """Test recommendations when imputation was performed."""
        imputation_log = ["Imputed 5 values"]
        
        recommendations = reporter._generate_recommendations(
            sample_validation_result,
            imputation_log,
            sample_anomalies_df,
            sample_ref_points_df
        )
        
        # Should have info about imputation
        assert any("imputation" in rec.lower() for rec in recommendations)

    def test_recommendations_few_reference_points(self, reporter, sample_anomalies_df, sample_validation_result):
        """Test recommendations when few reference points exist."""
        few_ref_points = pd.DataFrame({
            "id": ["R1", "R2"],
            "run_id": ["RUN1"] * 2,
            "distance": [100.0, 200.0],
            "point_type": ["girth_weld", "valve"]
        })
        
        recommendations = reporter._generate_recommendations(
            sample_validation_result,
            [],
            sample_anomalies_df,
            few_ref_points
        )
        
        # Should warn about insufficient reference points
        assert any("reference points" in rec.lower() for rec in recommendations)

    def test_recommendations_critical_depth(self, reporter, sample_ref_points_df, sample_validation_result):
        """Test recommendations when critical depth anomalies exist."""
        critical_df = pd.DataFrame({
            "id": ["A1", "A2"],
            "run_id": ["RUN1"] * 2,
            "distance": [100.0, 200.0],
            "clock_position": [3.0, 6.0],
            "depth_pct": [85.0, 90.0],  # Both critical
            "length": [4.5, 5.2],
            "width": [2.3, 2.8],
            "feature_type": ["external_corrosion"] * 2,
            "inspection_date": [datetime(2020, 1, 1)] * 2
        })
        
        recommendations = reporter._generate_recommendations(
            sample_validation_result,
            [],
            critical_df,
            sample_ref_points_df
        )
        
        # Should alert about critical anomalies
        assert any("ALERT" in rec or "critical" in rec.lower() for rec in recommendations)
        assert any("49 CFR" in rec for rec in recommendations)

    def test_recommendations_excellent_quality(self, reporter, sample_anomalies_df, sample_ref_points_df):
        """Test recommendations when data quality is excellent."""
        validation_result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            record_count=5,
            valid_count=5,
            invalid_count=0
        )
        
        recommendations = reporter._generate_recommendations(
            validation_result,
            [],
            sample_anomalies_df,
            sample_ref_points_df
        )
        
        # Should have positive recommendation
        assert any("EXCELLENT" in rec or "ready" in rec.lower() for rec in recommendations)

    def test_quality_score_calculation_perfect(self, reporter, sample_validation_result, sample_anomalies_df):
        """Test quality score calculation with perfect data."""
        score = reporter._calculate_quality_score(sample_validation_result, sample_anomalies_df)
        
        # Should be close to 100 (perfect data)
        assert 95 <= score <= 100

    def test_quality_score_calculation_with_errors(self, reporter, sample_anomalies_df):
        """Test quality score calculation with validation errors."""
        validation_result = ValidationResult(
            is_valid=False,
            errors=["Error 1", "Error 2"],
            warnings=[],
            record_count=10,
            valid_count=8,
            invalid_count=2
        )
        
        score = reporter._calculate_quality_score(validation_result, sample_anomalies_df)
        
        # Should be reduced due to errors
        assert score < 100

    def test_quality_score_calculation_with_missing_data(self, reporter, sample_validation_result):
        """Test quality score calculation with missing data."""
        df_with_missing = pd.DataFrame({
            "id": ["A1", "A2", "A3"],
            "distance": [100.0, 200.0, 300.0],
            "depth_pct": [25.0, np.nan, 45.0],  # Missing depth
            "clock_position": [3.0, 6.0, np.nan]  # Missing clock
        })
        
        score = reporter._calculate_quality_score(sample_validation_result, df_with_missing)
        
        # Should be reduced due to missing critical data
        assert score < 100

    def test_completeness_calculation(self, reporter, sample_anomalies_df):
        """Test completeness calculation."""
        completeness = reporter._calculate_completeness(sample_anomalies_df)
        
        # All fields should be 100% complete in sample data
        for field, pct in completeness.items():
            if field != "coating_type":  # coating_type has nulls
                assert pct == 100.0

    def test_completeness_with_missing_values(self, reporter):
        """Test completeness with missing values."""
        df = pd.DataFrame({
            "field1": [1, 2, np.nan, 4, 5],
            "field2": [1, np.nan, np.nan, 4, 5]
        })
        
        completeness = reporter._calculate_completeness(df)
        
        assert completeness["field1"] == 80.0  # 4/5 = 80%
        assert completeness["field2"] == 60.0  # 3/5 = 60%

    def test_validity_calculation(self, reporter, sample_validation_report):
        """Test validity calculation."""
        validity = reporter._calculate_validity(sample_validation_report)
        
        assert validity["percentage"] == 100.0
        assert validity["valid_count"] == 5
        assert validity["invalid_count"] == 0

    def test_consistency_calculation(self, reporter, sample_anomalies_df):
        """Test consistency calculation."""
        consistency = reporter._calculate_consistency(sample_anomalies_df)
        
        # All values should be consistent in sample data
        assert consistency["clock_position_valid_pct"] == 100.0
        assert consistency["depth_pct_valid_pct"] == 100.0

    def test_consistency_with_invalid_values(self, reporter):
        """Test consistency with invalid values."""
        df = pd.DataFrame({
            "clock_position": [3.0, 15.0, 6.0, 0.5, 9.0],  # 2 invalid
            "depth_pct": [25.0, 150.0, 45.0, -10.0, 55.0]  # 2 invalid
        })
        
        consistency = reporter._calculate_consistency(df)
        
        assert consistency["clock_position_valid_pct"] == 60.0  # 3/5 = 60%
        assert consistency["depth_pct_valid_pct"] == 60.0  # 3/5 = 60%

    def test_format_report_text(
        self,
        reporter,
        sample_anomalies_df,
        sample_ref_points_df,
        sample_validation_result,
        sample_validation_report,
        sample_imputation_log
    ):
        """Test text report formatting."""
        report = reporter.generate_comprehensive_report(
            anomalies_df=sample_anomalies_df,
            ref_points_df=sample_ref_points_df,
            validation_result=sample_validation_result,
            validation_report=sample_validation_report,
            imputation_log=sample_imputation_log,
            run_id="RUN1",
            file_path="data/test.csv"
        )
        
        text_report = reporter.format_report_text(report)
        
        # Check that key sections are present
        assert "ILI DATA QUALITY REPORT" in text_report
        assert "SUMMARY" in text_report
        assert "VALIDATION RESULTS" in text_report
        assert "IMPUTATION LOG" in text_report
        assert "ANOMALY STATISTICS" in text_report
        assert "REFERENCE POINTS" in text_report
        assert "RECOMMENDATIONS" in text_report
        
        # Check that key values are present
        assert "RUN1" in text_report
        assert "data/test.csv" in text_report

    def test_save_report_json(
        self,
        reporter,
        sample_anomalies_df,
        sample_ref_points_df,
        sample_validation_result,
        sample_validation_report,
        sample_imputation_log
    ):
        """Test saving report as JSON."""
        report = reporter.generate_comprehensive_report(
            anomalies_df=sample_anomalies_df,
            ref_points_df=sample_ref_points_df,
            validation_result=sample_validation_result,
            validation_report=sample_validation_report,
            imputation_log=sample_imputation_log,
            run_id="RUN1"
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            reporter.save_report_json(report, str(output_path))
            
            # Check file was created
            assert output_path.exists()
            
            # Check file can be loaded
            with open(output_path) as f:
                loaded_report = json.load(f)
            
            assert loaded_report["metadata"]["run_id"] == "RUN1"
            assert loaded_report["summary"]["anomaly_count"] == 5

    def test_save_report_text(
        self,
        reporter,
        sample_anomalies_df,
        sample_ref_points_df,
        sample_validation_result,
        sample_validation_report,
        sample_imputation_log
    ):
        """Test saving report as text."""
        report = reporter.generate_comprehensive_report(
            anomalies_df=sample_anomalies_df,
            ref_points_df=sample_ref_points_df,
            validation_result=sample_validation_result,
            validation_report=sample_validation_report,
            imputation_log=sample_imputation_log,
            run_id="RUN1"
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.txt"
            reporter.save_report_text(report, str(output_path))
            
            # Check file was created
            assert output_path.exists()
            
            # Check file content
            with open(output_path, encoding='utf-8') as f:
                content = f.read()
            
            assert "ILI DATA QUALITY REPORT" in content
            assert "RUN1" in content

    def test_quality_score_bounds(self, reporter, sample_validation_result):
        """Test that quality score is always between 0 and 100."""
        # Test with extreme missing data
        df_extreme = pd.DataFrame({
            "distance": [np.nan] * 10,
            "depth_pct": [np.nan] * 10,
            "clock_position": [np.nan] * 10
        })
        
        score = reporter._calculate_quality_score(sample_validation_result, df_extreme)
        
        assert 0 <= score <= 100

    def test_empty_dataframes(
        self,
        reporter,
        sample_validation_result,
        sample_validation_report
    ):
        """Test report generation with empty DataFrames."""
        empty_df = pd.DataFrame()
        
        report = reporter.generate_comprehensive_report(
            anomalies_df=empty_df,
            ref_points_df=empty_df,
            validation_result=sample_validation_result,
            validation_report=sample_validation_report,
            imputation_log=[],
            run_id="RUN1"
        )
        
        # Should not crash and should have valid structure
        assert report["summary"]["anomaly_count"] == 0
        assert report["summary"]["reference_point_count"] == 0
        assert report["anomalies"]["count"] == 0
        assert report["reference_points"]["count"] == 0
