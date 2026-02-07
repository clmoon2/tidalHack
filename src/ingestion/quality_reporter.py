"""
Data quality reporting for ILI ingestion pipeline.

Provides comprehensive quality reports combining validation results,
summary statistics, and imputation logs.
"""

import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pathlib import Path

from src.data_models.models import ValidationResult


class QualityReporter:
    """
    Generate comprehensive data quality reports for ILI ingestion.
    
    Combines:
    - Validation results (errors, warnings)
    - Summary statistics (record counts, distributions)
    - Data quality metrics (missing values, outliers)
    - Imputation logs (all data transformations)
    """

    def __init__(self):
        """Initialize the quality reporter."""
        pass

    def generate_comprehensive_report(
        self,
        anomalies_df: pd.DataFrame,
        ref_points_df: pd.DataFrame,
        validation_result: ValidationResult,
        validation_report: Dict[str, Any],
        imputation_log: List[str],
        run_id: str,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive quality report combining all data quality information.
        
        Args:
            anomalies_df: DataFrame with anomalies
            ref_points_df: DataFrame with reference points
            validation_result: Validation result from DataValidator
            validation_report: Detailed validation report from DataValidator
            imputation_log: List of imputation actions performed
            run_id: Inspection run identifier
            file_path: Optional path to source file
            
        Returns:
            Dictionary with comprehensive quality report
        """
        report = {
            "metadata": {
                "run_id": run_id,
                "file_path": file_path,
                "generated_at": datetime.now().isoformat(),
                "report_version": "1.0"
            },
            "summary": self._generate_summary(
                anomalies_df, ref_points_df, validation_result
            ),
            "validation": {
                "passed": validation_result.is_valid,
                "total_records": validation_result.record_count,
                "valid_records": validation_result.valid_count,
                "invalid_records": validation_result.invalid_count,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
                "required_fields_present": validation_report.get("required_fields_present", True),
                "missing_fields": validation_report.get("missing_fields", []),
                "range_validation_errors": validation_report.get("range_validation_errors", [])
            },
            "data_quality": self._generate_quality_metrics(
                anomalies_df, ref_points_df, validation_report
            ),
            "imputation": {
                "actions_performed": len(imputation_log),
                "log": imputation_log,
                "summary": self._summarize_imputations(imputation_log)
            },
            "anomalies": self._generate_anomaly_statistics(anomalies_df),
            "reference_points": self._generate_reference_point_statistics(ref_points_df),
            "recommendations": self._generate_recommendations(
                validation_result, imputation_log, anomalies_df, ref_points_df
            )
        }
        
        return report

    def _generate_summary(
        self,
        anomalies_df: pd.DataFrame,
        ref_points_df: pd.DataFrame,
        validation_result: ValidationResult
    ) -> Dict[str, Any]:
        """
        Generate high-level summary statistics.
        
        Args:
            anomalies_df: DataFrame with anomalies
            ref_points_df: DataFrame with reference points
            validation_result: Validation result
            
        Returns:
            Dictionary with summary statistics
        """
        return {
            "total_records": len(anomalies_df) + len(ref_points_df),
            "anomaly_count": len(anomalies_df),
            "reference_point_count": len(ref_points_df),
            "validation_status": "PASSED" if validation_result.is_valid else "FAILED",
            "data_quality_score": self._calculate_quality_score(
                validation_result, anomalies_df
            )
        }

    def _generate_quality_metrics(
        self,
        anomalies_df: pd.DataFrame,
        ref_points_df: pd.DataFrame,
        validation_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate detailed data quality metrics.
        
        Args:
            anomalies_df: DataFrame with anomalies
            ref_points_df: DataFrame with reference points
            validation_report: Validation report from DataValidator
            
        Returns:
            Dictionary with quality metrics
        """
        metrics = {
            "completeness": self._calculate_completeness(anomalies_df),
            "validity": self._calculate_validity(validation_report),
            "consistency": self._calculate_consistency(anomalies_df),
            "anomaly_metrics": validation_report.get("quality_metrics", {}),
        }
        
        # Add missing value analysis
        if len(anomalies_df) > 0:
            metrics["missing_values"] = {
                col: {
                    "count": int(anomalies_df[col].isna().sum()),
                    "percentage": round((anomalies_df[col].isna().sum() / len(anomalies_df)) * 100, 2)
                }
                for col in anomalies_df.columns
                if anomalies_df[col].isna().sum() > 0
            }
        else:
            metrics["missing_values"] = {}
        
        return metrics

    def _generate_anomaly_statistics(self, anomalies_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate detailed anomaly statistics.
        
        Args:
            anomalies_df: DataFrame with anomalies
            
        Returns:
            Dictionary with anomaly statistics
        """
        if len(anomalies_df) == 0:
            return {
                "count": 0,
                "by_type": {},
                "depth_statistics": {},
                "dimension_statistics": {}
            }
        
        stats = {
            "count": len(anomalies_df),
            "by_type": anomalies_df["feature_type"].value_counts().to_dict()
            if "feature_type" in anomalies_df.columns else {},
        }
        
        # Depth statistics
        if "depth_pct" in anomalies_df.columns:
            stats["depth_statistics"] = {
                "min": float(anomalies_df["depth_pct"].min()),
                "max": float(anomalies_df["depth_pct"].max()),
                "mean": float(anomalies_df["depth_pct"].mean()),
                "median": float(anomalies_df["depth_pct"].median()),
                "std": float(anomalies_df["depth_pct"].std()),
                "critical_count": int((anomalies_df["depth_pct"] > 80).sum()),
                "high_count": int(((anomalies_df["depth_pct"] >= 50) & (anomalies_df["depth_pct"] <= 80)).sum()),
                "moderate_count": int(((anomalies_df["depth_pct"] >= 30) & (anomalies_df["depth_pct"] < 50)).sum()),
                "low_count": int((anomalies_df["depth_pct"] < 30).sum())
            }
        
        # Dimension statistics
        stats["dimension_statistics"] = {}
        for dim in ["length", "width"]:
            if dim in anomalies_df.columns:
                stats["dimension_statistics"][dim] = {
                    "min": float(anomalies_df[dim].min()),
                    "max": float(anomalies_df[dim].max()),
                    "mean": float(anomalies_df[dim].mean()),
                    "median": float(anomalies_df[dim].median()),
                    "std": float(anomalies_df[dim].std())
                }
        
        # Distance coverage
        if "distance" in anomalies_df.columns:
            stats["distance_coverage"] = {
                "min": float(anomalies_df["distance"].min()),
                "max": float(anomalies_df["distance"].max()),
                "range": float(anomalies_df["distance"].max() - anomalies_df["distance"].min())
            }
        
        return stats

    def _generate_reference_point_statistics(
        self, ref_points_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Generate reference point statistics.
        
        Args:
            ref_points_df: DataFrame with reference points
            
        Returns:
            Dictionary with reference point statistics
        """
        if len(ref_points_df) == 0:
            return {
                "count": 0,
                "by_type": {},
                "spacing": {}
            }
        
        stats = {
            "count": len(ref_points_df),
            "by_type": ref_points_df["point_type"].value_counts().to_dict()
            if "point_type" in ref_points_df.columns else {}
        }
        
        # Calculate spacing between reference points
        if "distance" in ref_points_df.columns and len(ref_points_df) > 1:
            sorted_df = ref_points_df.sort_values("distance")
            spacings = sorted_df["distance"].diff().dropna()
            
            stats["spacing"] = {
                "min": float(spacings.min()),
                "max": float(spacings.max()),
                "mean": float(spacings.mean()),
                "median": float(spacings.median()),
                "std": float(spacings.std())
            }
        
        return stats

    def _summarize_imputations(self, imputation_log: List[str]) -> Dict[str, Any]:
        """
        Summarize imputation actions.
        
        Args:
            imputation_log: List of imputation log messages
            
        Returns:
            Dictionary with imputation summary
        """
        summary = {
            "total_actions": len(imputation_log),
            "by_field": {}
        }
        
        # Parse log messages to extract field names and counts
        for log_entry in imputation_log:
            # Extract field name and count from log message
            # Format: "Imputed X missing field_name values using method"
            if "clock_position" in log_entry:
                field = "clock_position"
            elif "length" in log_entry:
                field = "length"
            elif "width" in log_entry:
                field = "width"
            else:
                field = "unknown"
            
            # Extract count
            import re
            match = re.search(r"Imputed (\d+)", log_entry)
            if match:
                count = int(match.group(1))
                summary["by_field"][field] = {
                    "count": count,
                    "message": log_entry
                }
        
        return summary

    def _generate_recommendations(
        self,
        validation_result: ValidationResult,
        imputation_log: List[str],
        anomalies_df: pd.DataFrame,
        ref_points_df: pd.DataFrame
    ) -> List[str]:
        """
        Generate actionable recommendations based on data quality analysis.
        
        Args:
            validation_result: Validation result
            imputation_log: List of imputation actions
            anomalies_df: DataFrame with anomalies
            ref_points_df: DataFrame with reference points
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Validation recommendations
        if not validation_result.is_valid:
            recommendations.append(
                f"⚠️  CRITICAL: {validation_result.invalid_count} records failed validation. "
                "Review validation errors and correct source data."
            )
        
        # Imputation recommendations
        if len(imputation_log) > 0:
            recommendations.append(
                f"ℹ️  INFO: {len(imputation_log)} imputation actions were performed. "
                "Review imputation log to understand data transformations."
            )
        
        # Reference point recommendations
        if len(ref_points_df) < 10:
            recommendations.append(
                f"⚠️  WARNING: Only {len(ref_points_df)} reference points found. "
                "Alignment quality may be affected. Minimum 10 reference points recommended."
            )
        
        # Missing data recommendations
        if len(anomalies_df) > 0:
            critical_fields = ["distance", "depth_pct"]
            for field in critical_fields:
                if field in anomalies_df.columns:
                    missing_pct = (anomalies_df[field].isna().sum() / len(anomalies_df)) * 100
                    if missing_pct > 5:
                        recommendations.append(
                            f"⚠️  WARNING: {missing_pct:.1f}% of {field} values are missing. "
                            "This may affect analysis quality."
                        )
        
        # Depth distribution recommendations
        if "depth_pct" in anomalies_df.columns and len(anomalies_df) > 0:
            critical_count = (anomalies_df["depth_pct"] > 80).sum()
            if critical_count > 0:
                recommendations.append(
                    f"🚨 ALERT: {critical_count} anomalies have depth > 80% (critical threshold). "
                    "Immediate action may be required per 49 CFR 192.933."
                )
        
        # Data quality score recommendation
        quality_score = self._calculate_quality_score(validation_result, anomalies_df)
        if quality_score < 70:
            recommendations.append(
                f"⚠️  WARNING: Data quality score is {quality_score:.1f}/100. "
                "Consider improving source data quality before proceeding with analysis."
            )
        elif quality_score >= 90:
            recommendations.append(
                f"✅ EXCELLENT: Data quality score is {quality_score:.1f}/100. "
                "Data is ready for alignment and matching."
            )
        
        if len(recommendations) == 0:
            recommendations.append(
                "✅ No issues detected. Data quality is acceptable for analysis."
            )
        
        return recommendations

    def _calculate_quality_score(
        self, validation_result: ValidationResult, anomalies_df: pd.DataFrame
    ) -> float:
        """
        Calculate overall data quality score (0-100).
        
        Args:
            validation_result: Validation result
            anomalies_df: DataFrame with anomalies
            
        Returns:
            Quality score (0-100)
        """
        score = 100.0
        
        # Deduct for validation failures
        if validation_result.record_count > 0:
            invalid_pct = (validation_result.invalid_count / validation_result.record_count) * 100
            score -= invalid_pct * 0.5  # Each 1% invalid reduces score by 0.5
        
        # Deduct for missing critical fields
        if len(anomalies_df) > 0:
            critical_fields = ["distance", "depth_pct", "clock_position"]
            for field in critical_fields:
                if field in anomalies_df.columns:
                    missing_pct = (anomalies_df[field].isna().sum() / len(anomalies_df)) * 100
                    score -= missing_pct * 0.3  # Each 1% missing reduces score by 0.3
        
        return max(0.0, min(100.0, score))

    def _calculate_completeness(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate completeness metrics (percentage of non-null values).
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with completeness percentages by field
        """
        if len(df) == 0:
            return {}
        
        completeness = {}
        for col in df.columns:
            non_null_count = df[col].notna().sum()
            completeness[col] = round((non_null_count / len(df)) * 100, 2)
        
        return completeness

    def _calculate_validity(self, validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate validity metrics (percentage of valid values).
        
        Args:
            validation_report: Validation report from DataValidator
            
        Returns:
            Dictionary with validity metrics
        """
        total = validation_report.get("total_records", 0)
        valid = validation_report.get("valid_records", 0)
        
        if total == 0:
            return {"percentage": 0.0, "valid_count": 0, "invalid_count": 0}
        
        return {
            "percentage": round((valid / total) * 100, 2),
            "valid_count": valid,
            "invalid_count": validation_report.get("invalid_records", 0)
        }

    def _calculate_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate consistency metrics (data uniformity and patterns).
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with consistency metrics
        """
        consistency = {}
        
        # Check clock position consistency (should be 1-12)
        if "clock_position" in df.columns and len(df) > 0:
            valid_clock = df["clock_position"].between(1, 12, inclusive="both").sum()
            consistency["clock_position_valid_pct"] = round(
                (valid_clock / len(df)) * 100, 2
            )
        
        # Check depth consistency (should be 0-100)
        if "depth_pct" in df.columns and len(df) > 0:
            valid_depth = df["depth_pct"].between(0, 100, inclusive="both").sum()
            consistency["depth_pct_valid_pct"] = round(
                (valid_depth / len(df)) * 100, 2
            )
        
        return consistency

    def format_report_text(self, report: Dict[str, Any]) -> str:
        """
        Format report as human-readable text.
        
        Args:
            report: Comprehensive quality report
            
        Returns:
            Formatted text report
        """
        lines = []
        
        # Header
        lines.append("=" * 80)
        lines.append("ILI DATA QUALITY REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Metadata
        metadata = report["metadata"]
        lines.append(f"Run ID: {metadata['run_id']}")
        if metadata.get("file_path"):
            lines.append(f"Source File: {metadata['file_path']}")
        lines.append(f"Generated: {metadata['generated_at']}")
        lines.append("")
        
        # Summary
        lines.append("-" * 80)
        lines.append("SUMMARY")
        lines.append("-" * 80)
        summary = report["summary"]
        lines.append(f"Total Records: {summary['total_records']}")
        lines.append(f"Anomalies: {summary['anomaly_count']}")
        lines.append(f"Reference Points: {summary['reference_point_count']}")
        lines.append(f"Validation Status: {summary['validation_status']}")
        lines.append(f"Data Quality Score: {summary['data_quality_score']:.1f}/100")
        lines.append("")
        
        # Validation
        lines.append("-" * 80)
        lines.append("VALIDATION RESULTS")
        lines.append("-" * 80)
        validation = report["validation"]
        lines.append(f"Valid Records: {validation['valid_records']}/{validation['total_records']}")
        lines.append(f"Invalid Records: {validation['invalid_records']}")
        
        if validation["errors"]:
            lines.append(f"\nValidation Errors ({len(validation['errors'])}):")
            for error in validation["errors"][:10]:  # Show first 10
                lines.append(f"  • {error}")
            if len(validation["errors"]) > 10:
                lines.append(f"  ... and {len(validation['errors']) - 10} more")
        
        if validation["warnings"]:
            lines.append(f"\nValidation Warnings ({len(validation['warnings'])}):")
            for warning in validation["warnings"][:10]:
                lines.append(f"  • {warning}")
        
        lines.append("")
        
        # Imputation
        lines.append("-" * 80)
        lines.append("IMPUTATION LOG")
        lines.append("-" * 80)
        imputation = report["imputation"]
        lines.append(f"Actions Performed: {imputation['actions_performed']}")
        
        if imputation["log"]:
            lines.append("\nImputation Actions:")
            for action in imputation["log"]:
                lines.append(f"  • {action}")
        else:
            lines.append("No imputation actions were required.")
        
        lines.append("")
        
        # Anomaly Statistics
        lines.append("-" * 80)
        lines.append("ANOMALY STATISTICS")
        lines.append("-" * 80)
        anomalies = report["anomalies"]
        lines.append(f"Total Anomalies: {anomalies['count']}")
        
        if anomalies["by_type"]:
            lines.append("\nBy Type:")
            for anom_type, count in anomalies["by_type"].items():
                lines.append(f"  {anom_type}: {count}")
        
        if "depth_statistics" in anomalies and anomalies["depth_statistics"]:
            lines.append("\nDepth Statistics:")
            depth = anomalies["depth_statistics"]
            lines.append(f"  Min: {depth['min']:.2f}%")
            lines.append(f"  Max: {depth['max']:.2f}%")
            lines.append(f"  Mean: {depth['mean']:.2f}%")
            lines.append(f"  Median: {depth['median']:.2f}%")
            lines.append(f"  Critical (>80%): {depth['critical_count']}")
            lines.append(f"  High (50-80%): {depth['high_count']}")
            lines.append(f"  Moderate (30-50%): {depth['moderate_count']}")
            lines.append(f"  Low (<30%): {depth['low_count']}")
        
        lines.append("")
        
        # Reference Points
        lines.append("-" * 80)
        lines.append("REFERENCE POINTS")
        lines.append("-" * 80)
        ref_points = report["reference_points"]
        lines.append(f"Total Reference Points: {ref_points['count']}")
        
        if ref_points["by_type"]:
            lines.append("\nBy Type:")
            for ref_type, count in ref_points["by_type"].items():
                lines.append(f"  {ref_type}: {count}")
        
        lines.append("")
        
        # Recommendations
        lines.append("-" * 80)
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 80)
        for rec in report["recommendations"]:
            lines.append(f"{rec}")
            lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)

    def save_report_json(self, report: Dict[str, Any], output_path: str) -> None:
        """
        Save report as JSON file.
        
        Args:
            report: Comprehensive quality report
            output_path: Path to save JSON file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

    def save_report_text(self, report: Dict[str, Any], output_path: str) -> None:
        """
        Save report as text file.
        
        Args:
            report: Comprehensive quality report
            output_path: Path to save text file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        text_report = self.format_report_text(report)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text_report)
