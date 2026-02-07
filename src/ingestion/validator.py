"""
Data validator for ILI anomaly records.

Validates anomaly records against Pydantic schemas and generates validation reports.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from datetime import datetime
from pydantic import ValidationError

from src.data_models.models import AnomalyRecord, ReferencePoint, ValidationResult


class DataValidator:
    """
    Validates ILI data against Pydantic schemas.
    
    Handles:
    - Schema validation using Pydantic models
    - Required field checking
    - Range validation
    - Missing value imputation
    - Validation report generation
    """

    def __init__(self):
        """Initialize the validator."""
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
        self.imputation_log: List[str] = []

    def validate_schema(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validate DataFrame against AnomalyRecord schema.
        
        Args:
            df: DataFrame with anomaly records
            
        Returns:
            ValidationResult with validation status and error details
        """
        self.validation_errors = []
        self.validation_warnings = []
        
        valid_count = 0
        invalid_count = 0
        
        for idx, row in df.iterrows():
            try:
                # Attempt to create AnomalyRecord from row
                self._validate_record(row)
                valid_count += 1
            except ValidationError as e:
                invalid_count += 1
                error_msg = f"Row {idx}: {self._format_validation_error(e)}"
                self.validation_errors.append(error_msg)
            except Exception as e:
                invalid_count += 1
                error_msg = f"Row {idx}: Unexpected error - {str(e)}"
                self.validation_errors.append(error_msg)
        
        is_valid = invalid_count == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=self.validation_errors,
            warnings=self.validation_warnings,
            record_count=len(df),
            valid_count=valid_count,
            invalid_count=invalid_count
        )

    def _validate_record(self, row: pd.Series) -> AnomalyRecord:
        """
        Validate a single record against AnomalyRecord schema.
        
        Args:
            row: Pandas Series representing one record
            
        Returns:
            Validated AnomalyRecord
            
        Raises:
            ValidationError: If validation fails
        """
        # Convert row to dict
        record_dict = row.to_dict()
        
        # Create AnomalyRecord (will raise ValidationError if invalid)
        record = AnomalyRecord(**record_dict)
        
        return record

    def _format_validation_error(self, error: ValidationError) -> str:
        """
        Format Pydantic validation error into readable message.
        
        Args:
            error: Pydantic ValidationError
            
        Returns:
            Formatted error message
        """
        error_messages = []
        for err in error.errors():
            field = ".".join(str(loc) for loc in err["loc"])
            msg = err["msg"]
            error_messages.append(f"{field}: {msg}")
        
        return "; ".join(error_messages)

    def check_required_fields(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Check if all required fields are present in DataFrame.
        
        Args:
            df: DataFrame to check
            
        Returns:
            Tuple of (all_present, missing_fields)
        """
        required_fields = [
            "id",
            "run_id",
            "distance",
            "clock_position",
            "depth_pct",
            "length",
            "width",
            "feature_type",
            "inspection_date"
        ]
        
        missing_fields = [field for field in required_fields if field not in df.columns]
        
        all_present = len(missing_fields) == 0
        
        return all_present, missing_fields

    def validate_ranges(self, df: pd.DataFrame) -> List[str]:
        """
        Validate that numeric fields are within acceptable ranges.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Check distance (must be >= 0)
        if "distance" in df.columns:
            invalid_distance = df[df["distance"] < 0]
            if len(invalid_distance) > 0:
                errors.append(
                    f"Found {len(invalid_distance)} records with negative distance"
                )
        
        # Check clock_position (must be 1-12)
        if "clock_position" in df.columns:
            invalid_clock = df[
                (df["clock_position"] < 1) | (df["clock_position"] > 12)
            ]
            if len(invalid_clock) > 0:
                errors.append(
                    f"Found {len(invalid_clock)} records with clock_position outside 1-12 range"
                )
        
        # Check depth_pct (must be 0-100)
        if "depth_pct" in df.columns:
            invalid_depth = df[(df["depth_pct"] < 0) | (df["depth_pct"] > 100)]
            if len(invalid_depth) > 0:
                errors.append(
                    f"Found {len(invalid_depth)} records with depth_pct outside 0-100 range"
                )
        
        # Check length (must be > 0)
        if "length" in df.columns:
            invalid_length = df[df["length"] <= 0]
            if len(invalid_length) > 0:
                errors.append(
                    f"Found {len(invalid_length)} records with length <= 0"
                )
        
        # Check width (must be > 0)
        if "width" in df.columns:
            invalid_width = df[df["width"] <= 0]
            if len(invalid_width) > 0:
                errors.append(
                    f"Found {len(invalid_width)} records with width <= 0"
                )
        
        return errors

    def impute_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Impute missing values using appropriate strategies.
        
        Strategy:
        - clock_position: forward-fill
        - length: median
        - width: median
        - depth_pct: no imputation (critical field)
        - distance: no imputation (critical field)
        
        Args:
            df: DataFrame with potential missing values
            
        Returns:
            DataFrame with imputed values
        """
        df = df.copy()
        self.imputation_log = []
        
        # Forward-fill clock_position
        if "clock_position" in df.columns:
            missing_clock_before = df["clock_position"].isna().sum()
            if missing_clock_before > 0:
                df["clock_position"] = df["clock_position"].ffill()
                missing_clock_after = df["clock_position"].isna().sum()
                imputed_count = missing_clock_before - missing_clock_after
                if imputed_count > 0:
                    self.imputation_log.append(
                        f"Imputed {imputed_count} missing clock_position values using forward-fill"
                    )
        
        # Median imputation for length
        if "length" in df.columns:
            missing_length = df["length"].isna().sum()
            if missing_length > 0:
                median_length = df["length"].median()
                df["length"] = df["length"].fillna(median_length)
                self.imputation_log.append(
                    f"Imputed {missing_length} missing length values using median ({median_length:.2f} inches)"
                )
        
        # Median imputation for width
        if "width" in df.columns:
            missing_width = df["width"].isna().sum()
            if missing_width > 0:
                median_width = df["width"].median()
                df["width"] = df["width"].fillna(median_width)
                self.imputation_log.append(
                    f"Imputed {missing_width} missing width values using median ({median_width:.2f} inches)"
                )
        
        return df

    def generate_validation_report(
        self,
        df: pd.DataFrame,
        validation_result: ValidationResult
    ) -> Dict[str, Any]:
        """
        Generate comprehensive validation report.
        
        Args:
            df: DataFrame that was validated
            validation_result: Result from validate_schema()
            
        Returns:
            Dictionary with validation report details
        """
        # Check required fields
        all_fields_present, missing_fields = self.check_required_fields(df)
        
        # Check ranges
        range_errors = self.validate_ranges(df)
        
        # Calculate data quality metrics
        quality_metrics = self._calculate_quality_metrics(df)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_records": validation_result.record_count,
            "valid_records": validation_result.valid_count,
            "invalid_records": validation_result.invalid_count,
            "validation_passed": validation_result.is_valid,
            "required_fields_present": all_fields_present,
            "missing_fields": missing_fields,
            "validation_errors": validation_result.errors,
            "validation_warnings": validation_result.warnings,
            "range_validation_errors": range_errors,
            "imputation_log": self.imputation_log,
            "quality_metrics": quality_metrics
        }
        
        return report

    def _calculate_quality_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate data quality metrics.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with quality metrics
        """
        metrics = {}
        
        # Missing value percentages
        if len(df) > 0:
            for col in df.columns:
                missing_pct = (df[col].isna().sum() / len(df)) * 100
                if missing_pct > 0:
                    metrics[f"missing_{col}_pct"] = round(missing_pct, 2)
        
        # Numeric field statistics
        numeric_fields = ["distance", "clock_position", "depth_pct", "length", "width"]
        for field in numeric_fields:
            if field in df.columns and pd.api.types.is_numeric_dtype(df[field]):
                metrics[f"{field}_min"] = float(df[field].min()) if not df[field].isna().all() else None
                metrics[f"{field}_max"] = float(df[field].max()) if not df[field].isna().all() else None
                metrics[f"{field}_mean"] = float(df[field].mean()) if not df[field].isna().all() else None
                metrics[f"{field}_std"] = float(df[field].std()) if not df[field].isna().all() else None
        
        # Categorical field distributions
        if "feature_type" in df.columns:
            metrics["feature_type_distribution"] = df["feature_type"].value_counts().to_dict()
        
        return metrics

    def validate_and_report(self, df: pd.DataFrame) -> Tuple[ValidationResult, Dict[str, Any]]:
        """
        Convenience method to validate and generate report in one call.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (ValidationResult, report_dict)
        """
        validation_result = self.validate_schema(df)
        report = self.generate_validation_report(df, validation_result)
        
        return validation_result, report

    def validate_reference_points(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validate reference points against ReferencePoint schema.
        
        Args:
            df: DataFrame with reference point records
            
        Returns:
            ValidationResult with validation status
        """
        self.validation_errors = []
        self.validation_warnings = []
        
        valid_count = 0
        invalid_count = 0
        
        for idx, row in df.iterrows():
            try:
                # Attempt to create ReferencePoint from row
                record_dict = row.to_dict()
                ReferencePoint(**record_dict)
                valid_count += 1
            except ValidationError as e:
                invalid_count += 1
                error_msg = f"Row {idx}: {self._format_validation_error(e)}"
                self.validation_errors.append(error_msg)
            except Exception as e:
                invalid_count += 1
                error_msg = f"Row {idx}: Unexpected error - {str(e)}"
                self.validation_errors.append(error_msg)
        
        is_valid = invalid_count == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=self.validation_errors,
            warnings=self.validation_warnings,
            record_count=len(df),
            valid_count=valid_count,
            invalid_count=invalid_count
        )
