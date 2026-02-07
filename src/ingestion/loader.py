"""
ILI data loader for CSV files.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional
from pathlib import Path
import re
from datetime import datetime

from src.data_models.models import AnomalyRecord, ReferencePoint, ValidationResult


class ILIDataLoader:
    """
    Load and standardize ILI data from CSV files.
    
    Handles:
    - CSV parsing with pandas
    - Unit standardization (miles→feet, mm→inches, depth→percentage)
    - Clock position standardization (text→numeric 1-12)
    - Reference point extraction
    """

    def __init__(self):
        self.column_mappings = {
            # Common column name variations (2007/2015 format)
            "log dist.": "distance",
            "log dist. [ft]": "distance",
            "to u/s w. [ft]": "distance_to_upstream_weld",
            "to d/s w. [ft]": "distance_to_downstream_weld",
            "depth [%]": "depth_pct",
            "length [in]": "length",
            "width [in]": "width",
            "o'clock": "clock_position",
            "event": "feature_type",
            "event description": "feature_type",
            "comment": "description",
            "comments": "description",
            # 2022 format variations
            "ili wheel count \n[ft.]": "distance",
            "metal loss depth \n[%]": "depth_pct",
            "o'clock\n[hh:mm]": "clock_position",
        }

    def load_csv(
        self, file_path: str, run_id: str, inspection_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Load ILI data from CSV file.
        
        Args:
            file_path: Path to CSV file
            run_id: Unique identifier for this inspection run
            inspection_date: Date of inspection (extracted from filename if not provided)
            
        Returns:
            DataFrame with loaded data
        """
        # Extract year from filename if inspection_date not provided
        if inspection_date is None:
            year_match = re.search(r"(\d{4})", Path(file_path).name)
            if year_match:
                year = int(year_match.group(1))
                inspection_date = datetime(year, 1, 1)
            else:
                inspection_date = datetime.now()

        # Load CSV
        df = pd.read_csv(file_path, low_memory=False)

        # Normalize column names (lowercase, strip whitespace)
        df.columns = df.columns.str.lower().str.strip()

        # Apply column mappings
        df = df.rename(columns=self.column_mappings)

        # Add metadata
        df["run_id"] = run_id
        df["inspection_date"] = inspection_date

        # Generate IDs for each record
        df["id"] = df.apply(
            lambda row: f"{run_id}_{row.name}", axis=1
        )

        return df

    def standardize_units(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize units to: feet (distance), inches (dimensions), percentage (depth).
        
        Args:
            df: DataFrame with raw data
            
        Returns:
            DataFrame with standardized units
        """
        df = df.copy()

        # Distance: already in feet in these files
        # If you had miles, would convert: df['distance'] = df['distance'] * 5280

        # Depth: already in percentage
        # Ensure it's numeric
        if "depth_pct" in df.columns:
            df["depth_pct"] = pd.to_numeric(df["depth_pct"], errors="coerce")

        # Length: already in inches
        if "length" in df.columns:
            df["length"] = pd.to_numeric(df["length"], errors="coerce")

        # Width: already in inches
        if "width" in df.columns:
            df["width"] = pd.to_numeric(df["width"], errors="coerce")

        return df

    def standardize_clock_position(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize clock positions to numeric 1-12 format.
        
        Handles formats like:
        - "3 o'clock" → 3.0
        - "03:00:00" → 3.0
        - "3:30" → 3.5
        - "3" → 3.0
        
        Args:
            df: DataFrame with clock_position column
            
        Returns:
            DataFrame with standardized clock positions
        """
        df = df.copy()

        if "clock_position" not in df.columns:
            return df

        def parse_clock(value):
            if pd.isna(value):
                return np.nan

            # Convert to string
            value_str = str(value).strip().lower()

            # Handle time format (HH:MM:SS or HH:MM)
            if ":" in value_str:
                parts = value_str.split(":")
                try:
                    hour = int(parts[0])
                    minute = int(parts[1]) if len(parts) > 1 else 0
                    # Convert to decimal (e.g., 3:30 → 3.5)
                    return hour + (minute / 60.0)
                except (ValueError, IndexError):
                    return np.nan

            # Handle "X o'clock" format
            if "o'clock" in value_str or "oclock" in value_str:
                match = re.search(r"(\d+)", value_str)
                if match:
                    return float(match.group(1))

            # Handle plain number
            try:
                return float(value_str)
            except ValueError:
                return np.nan

        df["clock_position"] = df["clock_position"].apply(parse_clock)

        # Ensure values are in 1-12 range
        df.loc[df["clock_position"] < 1, "clock_position"] = np.nan
        df.loc[df["clock_position"] > 12, "clock_position"] = np.nan

        return df

    def standardize_feature_type(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize feature types to consistent categories.
        
        Maps various descriptions to standard types:
        - external_corrosion, internal_corrosion, dent, crack, other
        
        Args:
            df: DataFrame with feature_type column
            
        Returns:
            DataFrame with standardized feature types
        """
        df = df.copy()

        if "feature_type" not in df.columns:
            return df

        def categorize_feature(value):
            if pd.isna(value):
                return "other"

            value_str = str(value).lower()

            # External corrosion
            if any(
                term in value_str
                for term in ["external", "ext", "metal loss", "corrosion"]
            ):
                if "internal" not in value_str:
                    return "external_corrosion"

            # Internal corrosion
            if "internal" in value_str or "int" in value_str:
                return "internal_corrosion"

            # Dent
            if "dent" in value_str:
                return "dent"

            # Crack
            if "crack" in value_str:
                return "crack"

            # Reference points (not anomalies)
            if any(
                term in value_str
                for term in [
                    "weld",
                    "girth",
                    "valve",
                    "tap",
                    "tee",
                    "support",
                    "launcher",
                    "receiver",
                ]
            ):
                return "reference_point"

            return "other"

        df["feature_type"] = df["feature_type"].apply(categorize_feature)

        return df

    def extract_reference_points(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract reference points (girth welds, valves, tees) from data.
        
        Args:
            df: DataFrame with all records
            
        Returns:
            DataFrame with only reference points
        """
        # Identify reference points
        ref_point_types = ["girth_weld", "valve", "tee"]

        # Check if we have a feature_type column
        if "feature_type" not in df.columns:
            # Try to identify from event/description columns
            df = self.standardize_feature_type(df)

        # Filter for reference points
        ref_df = df[df["feature_type"] == "reference_point"].copy()

        # Further categorize reference points
        def categorize_ref_point(value):
            if pd.isna(value):
                return "other"

            value_str = str(value).lower()

            if "weld" in value_str or "girth" in value_str:
                return "girth_weld"
            elif "valve" in value_str:
                return "valve"
            elif "tee" in value_str or "tap" in value_str:
                return "tee"
            else:
                return "other"

        # Look at original event/description for categorization
        if "event" in df.columns:
            ref_df["point_type"] = df.loc[ref_df.index, "event"].apply(
                categorize_ref_point
            )
        elif "event description" in df.columns:
            ref_df["point_type"] = df.loc[ref_df.index, "event description"].apply(
                categorize_ref_point
            )
        else:
            ref_df["point_type"] = "other"

        # Keep only relevant columns
        ref_columns = ["id", "run_id", "distance", "point_type", "description"]
        ref_df = ref_df[[col for col in ref_columns if col in ref_df.columns]]

        return ref_df

    def extract_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract anomalies (corrosion, dents, cracks) from data.
        
        Filters out reference points and keeps only actual anomalies.
        
        Args:
            df: DataFrame with all records
            
        Returns:
            DataFrame with only anomalies
        """
        # Filter out reference points
        anomaly_types = [
            "external_corrosion",
            "internal_corrosion",
            "dent",
            "crack",
            "other",
        ]

        anomalies_df = df[df["feature_type"].isin(anomaly_types)].copy()

        # Filter out rows with missing critical data
        anomalies_df = anomalies_df.dropna(subset=["distance", "depth_pct"])

        # Ensure we have required columns
        required_cols = [
            "id",
            "run_id",
            "distance",
            "clock_position",
            "depth_pct",
            "length",
            "width",
            "feature_type",
            "inspection_date",
        ]

        # Fill missing values for non-critical fields
        if "clock_position" in anomalies_df.columns:
            # Forward fill clock position (pandas 3.0 compatible)
            anomalies_df["clock_position"] = anomalies_df["clock_position"].ffill()

        if "length" in anomalies_df.columns:
            # Use median for length
            median_length = anomalies_df["length"].median()
            anomalies_df["length"] = anomalies_df["length"].fillna(median_length)

        if "width" in anomalies_df.columns:
            # Use median for width
            median_width = anomalies_df["width"].median()
            anomalies_df["width"] = anomalies_df["width"].fillna(median_width)

        return anomalies_df

    def load_and_process(
        self, file_path: str, run_id: str, inspection_date: Optional[datetime] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Complete pipeline: load, standardize, and split into anomalies and reference points.
        
        Args:
            file_path: Path to CSV file
            run_id: Unique identifier for this inspection run
            inspection_date: Date of inspection
            
        Returns:
            Tuple of (anomalies_df, reference_points_df)
        """
        # Load data
        df = self.load_csv(file_path, run_id, inspection_date)

        # Standardize
        df = self.standardize_units(df)
        df = self.standardize_clock_position(df)
        df = self.standardize_feature_type(df)

        # Extract anomalies and reference points
        anomalies_df = self.extract_anomalies(df)
        ref_points_df = self.extract_reference_points(df)

        return anomalies_df, ref_points_df

    def generate_summary_report(
        self, anomalies_df: pd.DataFrame, ref_points_df: pd.DataFrame
    ) -> dict:
        """
        Generate data quality summary report.
        
        Args:
            anomalies_df: DataFrame with anomalies
            ref_points_df: DataFrame with reference points
            
        Returns:
            Dictionary with summary statistics
        """
        report = {
            "total_records": len(anomalies_df) + len(ref_points_df),
            "anomaly_count": len(anomalies_df),
            "reference_point_count": len(ref_points_df),
            "anomalies_by_type": anomalies_df["feature_type"].value_counts().to_dict()
            if "feature_type" in anomalies_df.columns
            else {},
            "reference_points_by_type": ref_points_df["point_type"]
            .value_counts()
            .to_dict()
            if "point_type" in ref_points_df.columns
            else {},
            "missing_clock_position": anomalies_df["clock_position"].isna().sum()
            if "clock_position" in anomalies_df.columns
            else 0,
            "missing_length": anomalies_df["length"].isna().sum()
            if "length" in anomalies_df.columns
            else 0,
            "missing_width": anomalies_df["width"].isna().sum()
            if "width" in anomalies_df.columns
            else 0,
            "depth_range": {
                "min": float(anomalies_df["depth_pct"].min())
                if "depth_pct" in anomalies_df.columns
                else None,
                "max": float(anomalies_df["depth_pct"].max())
                if "depth_pct" in anomalies_df.columns
                else None,
                "mean": float(anomalies_df["depth_pct"].mean())
                if "depth_pct" in anomalies_df.columns
                else None,
            },
        }

        return report
