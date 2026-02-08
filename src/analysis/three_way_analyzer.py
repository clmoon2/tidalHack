"""
Three-Way Analyzer
==================

Performs full three-way analysis across 2007 → 2015 → 2022 inspection runs.

Workflow:
1.  Load all 3 datasets
2.  Cluster detection (ASME B31G interaction zones) per run
3.  Extract reference points (girth welds) from each run
4.  DTW-align 2007→2015 reference points, build distance correction function
5.  DTW-align 2015→2022 reference points, build distance correction function
6.  Match drift-corrected 2007 → 2015 (Hungarian algorithm)
7.  Match drift-corrected 2015 → 2022
8.  Build chains (link same anomaly across all 3 runs)
9.  Calculate growth for BOTH intervals + acceleration
10. Risk scoring
11. AI storytelling for top N chains

Author: ILI Data Alignment System
Date: 2026
"""

import uuid
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd

from src.data_models.models import (
    AnomalyRecord,
    AnomalyChain,
    ChainExplanation,
    ThreeWayAnalysisResult,
    InteractionZone,
    Match,
    ReferencePoint,
)
from src.ingestion.loader import ILIDataLoader
from src.alignment.dtw_aligner import DTWAligner
from src.alignment.correction import DistanceCorrectionFunction
from src.matching.matcher import HungarianMatcher
from src.matching.similarity import SimilarityCalculator
from src.growth.analyzer import GrowthAnalyzer
from src.growth.risk_scorer import RiskScorer
from src.analysis.cluster_detector import ClusterDetector
from src.agents.chain_storyteller import ChainStorytellerSystem, TrendAgent, ProjectionAgent


class ThreeWayAnalyzer:
    """
    Orchestrates full three-way analysis across 3 inspection runs.

    Takes data from 2007, 2015, and 2022 ILI inspections, matches anomalies
    across runs, builds chains, computes growth/acceleration, and generates
    AI-powered explanations.
    """

    def __init__(
        self,
        distance_sigma: float = 5.0,
        clock_sigma: float = 1.0,
        confidence_threshold: float = 0.6,
        rapid_growth_threshold: float = 5.0,
        use_agents: bool = True,
        api_key: Optional[str] = None,
        drift_constraint: float = 0.10,
        cluster_axial_ft: float = 1.0,
        cluster_clock: float = 1.5,
        cluster_min_size: int = 2,
    ):
        """
        Initialize the three-way analyzer.

        Args:
            distance_sigma: Sigma for distance similarity
            clock_sigma: Sigma for clock similarity
            confidence_threshold: Minimum match confidence
            rapid_growth_threshold: Threshold for rapid growth (pp/yr)
            use_agents: Whether to use AI agents for explanations
            api_key: Google API key for agents
            drift_constraint: Maximum allowed odometer drift fraction for DTW (default 10%)
            cluster_axial_ft: Axial proximity threshold for clustering (ft)
            cluster_clock: Clock proximity threshold for clustering (hours)
            cluster_min_size: Minimum anomalies to form a cluster
        """
        self.similarity_calc = SimilarityCalculator(
            distance_sigma=distance_sigma, clock_sigma=clock_sigma
        )
        self.matcher = HungarianMatcher(
            similarity_calculator=self.similarity_calc,
            confidence_threshold=confidence_threshold,
        )
        self.growth_analyzer = GrowthAnalyzer(
            rapid_growth_threshold=rapid_growth_threshold
        )
        self.risk_scorer = RiskScorer(
            depth_weight=0.6, growth_weight=0.3, location_weight=0.1
        )
        self.cluster_detector = ClusterDetector(
            axial_threshold_ft=cluster_axial_ft,
            clock_threshold=cluster_clock,
            min_cluster_size=cluster_min_size,
        )
        self.use_agents = use_agents
        self.api_key = api_key
        self.drift_constraint = drift_constraint

    def load_dataset(
        self,
        file_path: str,
        run_id: str,
        inspection_date: datetime,
    ) -> Tuple[List[AnomalyRecord], pd.DataFrame]:
        """
        Load an ILI dataset and convert to AnomalyRecord objects.

        Args:
            file_path: Path to CSV file
            run_id: Run identifier
            inspection_date: Date of the inspection

        Returns:
            Tuple of (list of AnomalyRecords, DataFrame of reference points)
        """
        loader = ILIDataLoader()
        anomalies_df, ref_points_df = loader.load_and_process(
            file_path, run_id, inspection_date
        )

        anomalies = []
        for idx, row in anomalies_df.iterrows():
            try:
                anomaly = AnomalyRecord(
                    id=f"{run_id}_{idx}",
                    run_id=run_id,
                    distance=float(row["distance"]),
                    clock_position=float(row["clock_position"]),
                    depth_pct=float(row["depth_pct"]),
                    length=float(row["length"]),
                    width=float(row["width"]),
                    feature_type=row["feature_type"],
                    inspection_date=inspection_date,
                )
                anomalies.append(anomaly)
            except Exception:
                pass

        return anomalies, ref_points_df

    def _convert_ref_df_to_models(
        self, ref_df: pd.DataFrame, run_id: str
    ) -> List[ReferencePoint]:
        """
        Convert a reference-points DataFrame into a list of ReferencePoint
        Pydantic models suitable for DTWAligner.

        Filters to rows that have a valid distance and a recognised point_type.

        Args:
            ref_df: DataFrame returned by ILIDataLoader.extract_reference_points()
            run_id: Run identifier to stamp on each model

        Returns:
            Sorted (by distance) list of ReferencePoint models
        """
        valid_types = {"girth_weld", "valve", "tee", "other"}
        ref_points: List[ReferencePoint] = []

        for _, row in ref_df.iterrows():
            try:
                pt = row.get("point_type", "other")
                if pt not in valid_types:
                    pt = "other"
                rp = ReferencePoint(
                    id=row.get("id", f"{run_id}_ref_{_}"),
                    run_id=run_id,
                    distance=float(row["distance"]),
                    point_type=pt,
                    description=row.get("description"),
                )
                ref_points.append(rp)
            except Exception:
                # Skip rows that can't be converted (missing distance, etc.)
                pass

        # DTW expects the sequences sorted by odometer distance
        ref_points.sort(key=lambda rp: rp.distance)
        return ref_points

    def _align_and_correct(
        self,
        anomalies_source: List[AnomalyRecord],
        ref_source: List[ReferencePoint],
        ref_target: List[ReferencePoint],
        source_run_id: str,
        target_run_id: str,
    ) -> Tuple[List[AnomalyRecord], bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Run DTW alignment between two sets of reference points and apply the
        resulting distance-correction function to every anomaly in the source
        run so that matching uses drift-corrected distances.

        The method prefers girth-weld reference points for alignment because
        they are the most reliable physical features.  If fewer than 3 girth
        welds are available it falls back to all reference point types.

        Args:
            anomalies_source: Anomalies from the earlier (source) run
            ref_source: Reference points from the source run
            ref_target: Reference points from the target (later) run
            source_run_id: Run ID of the source run
            target_run_id: Run ID of the target run

        Returns:
            Tuple containing:
                - List[AnomalyRecord]: Corrected anomalies (or original if correction failed)
                - bool: True if DTW correction was applied, False if fallback to raw
                - Optional[str]: Reason for fallback (None if correction succeeded)
                - Optional[Dict[str, Any]]: Alignment statistics (None if correction failed)
        """
        # ── 1. Prefer girth welds for alignment ────────────────────────
        gw_source = [rp for rp in ref_source if rp.point_type == "girth_weld"]
        gw_target = [rp for rp in ref_target if rp.point_type == "girth_weld"]

        if len(gw_source) < 3 or len(gw_target) < 3:
            # Fall back to all reference points
            gw_source = ref_source
            gw_target = ref_target

        if len(gw_source) < 2 or len(gw_target) < 2:
            print(
                f"  [WARN] Too few reference points for alignment "
                f"({len(gw_source)} source, {len(gw_target)} target). "
                f"Skipping distance correction for {source_run_id} -> {target_run_id}."
            )
            reason = (
                f"Insufficient reference points: {len(gw_source)} in {source_run_id}, "
                f"{len(gw_target)} in {target_run_id} (minimum: 2 each)"
            )
            return anomalies_source, False, reason, None

        # ── 2. DTW alignment ───────────────────────────────────────────
        try:
            aligner = DTWAligner(drift_constraint=self.drift_constraint)
            alignment = aligner.align_sequences(
                gw_source, gw_target, source_run_id, target_run_id
            )

            print(
                f"  Alignment quality: {alignment.match_rate:.1f}% match rate, "
                f"RMSE {alignment.rmse:.2f} ft "
                f"({len(alignment.matched_points)} pairs)"
            )

            # ── 3. Build correction function ───────────────────────────
            corrector = DistanceCorrectionFunction(
                alignment.correction_function_params
            )
            info = corrector.get_correction_info()
            print(
                f"  Correction applied: {info['num_reference_points']} ref pts, "
                f"max shift {info['max_correction']:.2f} ft, "
                f"mean shift {info['mean_correction']:.2f} ft"
            )

            # ── 4. Correct every source anomaly distance ───────────────
            corrected: List[AnomalyRecord] = []
            for anom in anomalies_source:
                new_dist = corrector.correct_distance(anom.distance)
                corrected.append(anom.model_copy(update={"distance": new_dist}))

            alignment_info = {
                "match_rate": alignment.match_rate,
                "rmse": alignment.rmse,
                "matched_pairs": len(alignment.matched_points),
                **info,
            }
            return corrected, True, None, alignment_info

        except Exception as e:
            # Alignment quality below threshold, insufficient data, etc.
            print(
                f"  [WARN] DTW alignment failed for {source_run_id} -> {target_run_id}: {e}"
            )
            print("  Proceeding with raw odometer distances.")
            reason = f"DTW alignment failed: {str(e)}"
            return anomalies_source, False, reason, None

    def run_full_analysis(
        self,
        data_2007_path: str,
        data_2015_path: str,
        data_2022_path: str,
        date_2007: Optional[datetime] = None,
        date_2015: Optional[datetime] = None,
        date_2022: Optional[datetime] = None,
        top_n_explain: int = 10,
        output_dir: Optional[str] = None,
    ) -> ThreeWayAnalysisResult:
        """
        Run the complete three-way analysis pipeline.

        Args:
            data_2007_path: Path to 2007 CSV data
            data_2015_path: Path to 2015 CSV data
            data_2022_path: Path to 2022 CSV data
            date_2007: Inspection date for 2007 (defaults to 2007-01-01)
            date_2015: Inspection date for 2015 (defaults to 2015-01-01)
            date_2022: Inspection date for 2022 (defaults to 2022-01-01)
            top_n_explain: Number of top chains to explain with AI
            output_dir: Optional directory to save output files

        Returns:
            ThreeWayAnalysisResult with all analysis data
        """
        analysis_id = str(uuid.uuid4())[:8]
        date_2007 = date_2007 or datetime(2007, 1, 1)
        date_2015 = date_2015 or datetime(2015, 1, 1)
        date_2022 = date_2022 or datetime(2022, 1, 1)

        print("=" * 80)
        print("THREE-WAY ANALYSIS: 2007 -> 2015 -> 2022  (with DTW drift correction + clustering)")
        print("=" * 80)

        # ─── Step 1: Load all 3 datasets ────────────────────────────────
        print("\n[1/11] Loading datasets...")
        anomalies_2007, ref_df_2007 = self.load_dataset(
            data_2007_path, "RUN_2007", date_2007
        )
        anomalies_2015, ref_df_2015 = self.load_dataset(
            data_2015_path, "RUN_2015", date_2015
        )
        anomalies_2022, ref_df_2022 = self.load_dataset(
            data_2022_path, "RUN_2022", date_2022
        )
        print(
            f"  Loaded: {len(anomalies_2007)} (2007) + "
            f"{len(anomalies_2015)} (2015) + {len(anomalies_2022)} (2022) = "
            f"{len(anomalies_2007) + len(anomalies_2015) + len(anomalies_2022)} total"
        )

        # ─── Step 2: Cluster detection (ASME B31G interaction zones) ───
        print("\n[2/11] Detecting ASME B31G interaction zones (DBSCAN clustering)...")
        anomalies_2007, zones_2007 = self.cluster_detector.detect_clusters(
            anomalies_2007, "RUN_2007"
        )
        anomalies_2015, zones_2015 = self.cluster_detector.detect_clusters(
            anomalies_2015, "RUN_2015"
        )
        anomalies_2022, zones_2022 = self.cluster_detector.detect_clusters(
            anomalies_2022, "RUN_2022"
        )
        total_clusters = len(zones_2007) + len(zones_2015) + len(zones_2022)
        total_anomalies_all = len(anomalies_2007) + len(anomalies_2015) + len(anomalies_2022)
        clustered_count = sum(1 for a in anomalies_2007 if a.cluster_id) + \
                          sum(1 for a in anomalies_2015 if a.cluster_id) + \
                          sum(1 for a in anomalies_2022 if a.cluster_id)
        clustered_pct = (clustered_count / total_anomalies_all * 100) if total_anomalies_all else 0.0
        print(
            f"  Clusters found: {len(zones_2007)} (2007) | "
            f"{len(zones_2015)} (2015) | {len(zones_2022)} (2022) = "
            f"{total_clusters} total"
        )
        print(
            f"  Clustered anomalies: {clustered_count}/{total_anomalies_all} "
            f"({clustered_pct:.1f}%)"
        )
        if zones_2007 or zones_2015 or zones_2022:
            all_zones = zones_2007 + zones_2015 + zones_2022
            largest = max(z.anomaly_count for z in all_zones)
            print(f"  Largest cluster size: {largest} anomalies")

        # ─── Step 3: Extract reference points for alignment ────────────
        print("\n[3/11] Extracting reference points (girth welds) for DTW alignment...")
        ref_pts_2007 = self._convert_ref_df_to_models(ref_df_2007, "RUN_2007")
        ref_pts_2015 = self._convert_ref_df_to_models(ref_df_2015, "RUN_2015")
        ref_pts_2022 = self._convert_ref_df_to_models(ref_df_2022, "RUN_2022")
        gw_07 = sum(1 for r in ref_pts_2007 if r.point_type == "girth_weld")
        gw_15 = sum(1 for r in ref_pts_2015 if r.point_type == "girth_weld")
        gw_22 = sum(1 for r in ref_pts_2022 if r.point_type == "girth_weld")
        print(
            f"  Reference points: {len(ref_pts_2007)} (2007, {gw_07} welds) | "
            f"{len(ref_pts_2015)} (2015, {gw_15} welds) | "
            f"{len(ref_pts_2022)} (2022, {gw_22} welds)"
        )

        # ─── Step 4: DTW align 2007→2015, correct 2007 distances ──────
        print("\n[4/11] DTW alignment: 2007 -> 2015 (correcting 2007 odometer drift)...")
        (
            anomalies_2007_corrected,
            dtw_applied_07_15,
            dtw_fallback_reason_07_15,
            align_info_07_15,
        ) = self._align_and_correct(
            anomalies_2007, ref_pts_2007, ref_pts_2015, "RUN_2007", "RUN_2015"
        )

        # ─── Step 5: DTW align 2015→2022, correct 2015 distances ──────
        print("\n[5/11] DTW alignment: 2015 -> 2022 (correcting 2015 odometer drift)...")
        (
            anomalies_2015_corrected,
            dtw_applied_15_22,
            dtw_fallback_reason_15_22,
            align_info_15_22,
        ) = self._align_and_correct(
            anomalies_2015, ref_pts_2015, ref_pts_2022, "RUN_2015", "RUN_2022"
        )

        # ─── Step 6: Match corrected-2007 → 2015 ──────────────────────
        print("\n[6/11] Matching corrected-2007 -> 2015 (8-year interval)...")
        start = time.time()
        result_07_15 = self.matcher.match_anomalies(
            anomalies_2007_corrected, anomalies_2015, "RUN_2007", "RUN_2015"
        )
        stats_07_15 = result_07_15["statistics"]
        print(
            f"  Matched {stats_07_15['matched']} pairs in {time.time()-start:.1f}s "
            f"({stats_07_15['match_rate']:.1%} rate)"
        )

        # ─── Step 7: Match corrected-2015 → 2022 ──────────────────────
        print("\n[7/11] Matching corrected-2015 -> 2022 (7-year interval)...")
        start = time.time()
        result_15_22 = self.matcher.match_anomalies(
            anomalies_2015_corrected, anomalies_2022, "RUN_2015", "RUN_2022"
        )
        stats_15_22 = result_15_22["statistics"]
        print(
            f"  Matched {stats_15_22['matched']} pairs in {time.time()-start:.1f}s "
            f"({stats_15_22['match_rate']:.1%} rate)"
        )

        # ─── Step 8: Build chains ──────────────────────────────────────
        # NOTE: _build_chains uses anomaly IDs to look up objects.  We pass
        # the *corrected* source anomalies so that any downstream distance-
        # based logic (e.g. chain metadata) reflects drift-corrected values,
        # while the target run anomalies remain in their native coordinate
        # system (the correction maps source→target, so target is already
        # in the "true" frame of reference).
        print("\n[8/11] Building 3-way chains...")
        chains = self._build_chains(
            anomalies_2007_corrected,
            anomalies_2015,
            anomalies_2022,
            result_07_15,
            result_15_22,
        )
        print(f"  Found {len(chains)} complete 3-way chains")

        # ─── Step 9: Calculate growth and acceleration ─────────────────
        print("\n[9/11] Computing growth rates and acceleration...")
        chain_models = self._compute_growth_and_risk(chains)
        accelerating = sum(1 for c in chain_models if c.is_accelerating)
        decelerating = sum(
            1 for c in chain_models if c.acceleration < -0.1
        )
        stable = len(chain_models) - accelerating - decelerating
        print(
            f"  Accelerating: {accelerating} | Stable: {stable} | Decelerating: {decelerating}"
        )

        # ─── Step 10: Risk scoring ────────────────────────────────────
        print("\n[10/11] Risk scoring...")
        # Sort chains by risk score
        chain_models.sort(key=lambda c: c.risk_score, reverse=True)
        high_risk = sum(1 for c in chain_models if c.risk_score >= 0.7)
        print(f"  High-risk chains (>= 0.7): {high_risk}")

        # ─── Step 11: AI storytelling ─────────────────────────────────
        explanations = []
        if self.use_agents and len(chain_models) > 0:
            print(f"\n[11/11] AI storytelling for top {min(top_n_explain, len(chain_models))} chains...")
            try:
                storyteller = ChainStorytellerSystem(api_key=self.api_key)
                chain_dicts = [
                    {
                        "chain_id": c.chain_id,
                        "anomaly_2007_id": c.anomaly_2007_id,
                        "anomaly_2015_id": c.anomaly_2015_id,
                        "anomaly_2022_id": c.anomaly_2022_id,
                        "depth_2007": c.depth_2007,
                        "depth_2015": c.depth_2015,
                        "depth_2022": c.depth_2022,
                        "growth_rate_07_15": c.growth_rate_07_15,
                        "growth_rate_15_22": c.growth_rate_15_22,
                        "acceleration": c.acceleration,
                        "match_confidence_07_15": c.match_confidence_07_15,
                        "match_confidence_15_22": c.match_confidence_15_22,
                        "risk_score": c.risk_score,
                    }
                    for c in chain_models
                ]
                explanation_dicts = storyteller.explain_chains_batch(
                    chain_dicts, top_n=top_n_explain
                )
                for exp_dict in explanation_dicts:
                    try:
                        explanations.append(
                            ChainExplanation(
                                chain_id=exp_dict["chain_id"],
                                trend_classification=exp_dict["trend_classification"],
                                urgency_level=exp_dict["urgency_level"],
                                lifecycle_narrative=exp_dict["lifecycle_narrative"],
                                trend_analysis=exp_dict["trend_analysis"],
                                projection_analysis=exp_dict["projection_analysis"],
                                recommendation=exp_dict["recommendation"],
                                concerns=exp_dict.get("concerns", []),
                            )
                        )
                    except Exception:
                        pass
                print(f"  Generated {len(explanations)} chain explanations")
            except Exception as e:
                print(f"  [WARN] AI storytelling failed: {e}")
        else:
            print("\n[11/11] AI storytelling skipped (agents disabled or no chains)")

        # ─── Build result ─────────────────────────────────────────────
        print("\nBuilding final result...")

        # Calculate average growth rates
        avg_gr_07_15 = 0.0
        avg_gr_15_22 = 0.0
        if chain_models:
            avg_gr_07_15 = sum(c.growth_rate_07_15 for c in chain_models) / len(chain_models)
            avg_gr_15_22 = sum(c.growth_rate_15_22 for c in chain_models) / len(chain_models)

        immediate_count = sum(
            1
            for c in chain_models
            if c.depth_2022 >= 70 or (c.years_to_80pct is not None and c.years_to_80pct <= 3)
        )

        result = ThreeWayAnalysisResult(
            analysis_id=analysis_id,
            timestamp=datetime.now(),
            total_anomalies_2007=len(anomalies_2007),
            total_anomalies_2015=len(anomalies_2015),
            total_anomalies_2022=len(anomalies_2022),
            matched_07_15=stats_07_15["matched"],
            matched_15_22=stats_15_22["matched"],
            total_chains=len(chain_models),
            chains=chain_models,
            explanations=explanations,
            accelerating_count=accelerating,
            stable_count=stable,
            decelerating_count=decelerating,
            immediate_action_count=immediate_count,
            avg_growth_rate_07_15=avg_gr_07_15,
            avg_growth_rate_15_22=avg_gr_15_22,
            interaction_zones_2007=zones_2007,
            interaction_zones_2015=zones_2015,
            interaction_zones_2022=zones_2022,
            total_clusters=total_clusters,
            clustered_anomaly_pct=clustered_pct,
            dtw_applied_07_15=dtw_applied_07_15,
            dtw_applied_15_22=dtw_applied_15_22,
            dtw_fallback_reason_07_15=dtw_fallback_reason_07_15,
            dtw_fallback_reason_15_22=dtw_fallback_reason_15_22,
            status="COMPLETE",
        )

        # ─── DTW Status Summary ─────────────────────────────────────────
        print("\n=== DTW Correction Status ===")
        print(f"  2007->2015: {'[OK] Applied' if dtw_applied_07_15 else '[X] Fallback'}")
        if dtw_fallback_reason_07_15:
            print(f"    Reason: {dtw_fallback_reason_07_15}")
        print(f"  2015->2022: {'[OK] Applied' if dtw_applied_15_22 else '[X] Fallback'}")
        if dtw_fallback_reason_15_22:
            print(f"    Reason: {dtw_fallback_reason_15_22}")
        print()

        # Save output files if requested
        if output_dir:
            self._save_outputs(result, output_dir)

        print("=" * 80)
        print(f"ANALYSIS COMPLETE: {len(chain_models)} chains, {len(explanations)} explained")
        print("=" * 80)

        return result

    def _build_chains(
        self,
        anomalies_2007: List[AnomalyRecord],
        anomalies_2015: List[AnomalyRecord],
        anomalies_2022: List[AnomalyRecord],
        result_07_15: Dict[str, Any],
        result_15_22: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Build 3-way chains by linking matches across both intervals.

        A chain exists when:
        - Anomaly A in 2007 matched to anomaly B in 2015
        - Anomaly B in 2015 also matched to anomaly C in 2022

        Returns list of chain dictionaries with all anomaly data.
        """
        # Create lookup dictionaries
        # matches_07_15: 2015 anomaly ID -> Match object
        match_lookup_07_15 = {}
        for m in result_07_15["matches"]:
            match_lookup_07_15[m.anomaly2_id] = m

        # matches_15_22: 2015 anomaly ID -> Match object
        match_lookup_15_22 = {}
        for m in result_15_22["matches"]:
            match_lookup_15_22[m.anomaly1_id] = m

        # Create anomaly lookup dictionaries
        lookup_2007 = {a.id: a for a in anomalies_2007}
        lookup_2015 = {a.id: a for a in anomalies_2015}
        lookup_2022 = {a.id: a for a in anomalies_2022}

        chains = []
        chain_idx = 0

        for anom_2015_id in match_lookup_07_15:
            if anom_2015_id in match_lookup_15_22:
                match_07_15 = match_lookup_07_15[anom_2015_id]
                match_15_22 = match_lookup_15_22[anom_2015_id]

                anom_2007 = lookup_2007.get(match_07_15.anomaly1_id)
                anom_2015 = lookup_2015.get(anom_2015_id)
                anom_2022 = lookup_2022.get(match_15_22.anomaly2_id)

                if anom_2007 and anom_2015 and anom_2022:
                    chains.append(
                        {
                            "chain_idx": chain_idx,
                            "anomaly_2007_id": anom_2007.id,
                            "anomaly_2015_id": anom_2015.id,
                            "anomaly_2022_id": anom_2022.id,
                            "depth_2007": anom_2007.depth_pct,
                            "depth_2015": anom_2015.depth_pct,
                            "depth_2022": anom_2022.depth_pct,
                            "distance_2007": anom_2007.distance,
                            "distance_2015": anom_2015.distance,
                            "distance_2022": anom_2022.distance,
                            "clock_2007": anom_2007.clock_position,
                            "clock_2015": anom_2015.clock_position,
                            "clock_2022": anom_2022.clock_position,
                            "match_confidence_07_15": match_07_15.similarity_score,
                            "match_confidence_15_22": match_15_22.similarity_score,
                            "feature_type": anom_2022.feature_type,
                        }
                    )
                    chain_idx += 1

        return chains

    def _compute_growth_and_risk(
        self, chains: List[Dict[str, Any]]
    ) -> List[AnomalyChain]:
        """
        Calculate growth rates, acceleration, and risk scores for all chains.

        Returns list of AnomalyChain model objects.
        """
        chain_models = []

        for chain in chains:
            depth_07 = chain["depth_2007"]
            depth_15 = chain["depth_2015"]
            depth_22 = chain["depth_2022"]

            # Growth rates (pp/year)
            gr_07_15 = (depth_15 - depth_07) / 8.0  # 8 years
            gr_15_22 = (depth_22 - depth_15) / 7.0  # 7 years

            # Acceleration (change in growth rate)
            acceleration = gr_15_22 - gr_07_15

            # Risk score: composite of current depth, growth rate, acceleration
            depth_risk = min(depth_22 / 100.0, 1.0) * 0.5
            growth_risk = min(max(gr_15_22, 0) / 10.0, 1.0) * 0.3
            accel_risk = min(max(acceleration, 0) / 5.0, 1.0) * 0.2
            risk_score = depth_risk + growth_risk + accel_risk

            # Years to 80% critical threshold
            years_to_80 = ProjectionAgent.project_years_to_critical(
                depth_22, gr_15_22, acceleration
            )

            chain_model = AnomalyChain(
                chain_id=f"CHAIN_{chain['chain_idx']:04d}",
                anomaly_2007_id=chain["anomaly_2007_id"],
                anomaly_2015_id=chain["anomaly_2015_id"],
                anomaly_2022_id=chain["anomaly_2022_id"],
                match_confidence_07_15=chain["match_confidence_07_15"],
                match_confidence_15_22=chain["match_confidence_15_22"],
                depth_2007=depth_07,
                depth_2015=depth_15,
                depth_2022=depth_22,
                growth_rate_07_15=gr_07_15,
                growth_rate_15_22=gr_15_22,
                acceleration=acceleration,
                is_accelerating=acceleration > 0.1,
                risk_score=risk_score,
                years_to_80pct=years_to_80,
            )
            chain_models.append(chain_model)

        return chain_models

    def _save_outputs(
        self, result: ThreeWayAnalysisResult, output_dir: str
    ) -> None:
        """Save analysis outputs to files."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        # 1. Save chains CSV
        if result.chains:
            chains_data = []
            for c in result.chains:
                chains_data.append(
                    {
                        "chain_id": c.chain_id,
                        "anomaly_2007_id": c.anomaly_2007_id,
                        "anomaly_2015_id": c.anomaly_2015_id,
                        "anomaly_2022_id": c.anomaly_2022_id,
                        "depth_2007": c.depth_2007,
                        "depth_2015": c.depth_2015,
                        "depth_2022": c.depth_2022,
                        "growth_rate_07_15": c.growth_rate_07_15,
                        "growth_rate_15_22": c.growth_rate_15_22,
                        "acceleration": c.acceleration,
                        "is_accelerating": c.is_accelerating,
                        "risk_score": c.risk_score,
                        "years_to_80pct": c.years_to_80pct,
                        "match_confidence_07_15": c.match_confidence_07_15,
                        "match_confidence_15_22": c.match_confidence_15_22,
                    }
                )
            pd.DataFrame(chains_data).to_csv(
                out_path / "three_way_chains.csv", index=False
            )
            print(f"  Saved: {out_path / 'three_way_chains.csv'}")

        # 2. Save AI explanations CSV
        if result.explanations:
            exp_data = []
            for e in result.explanations:
                exp_data.append(
                    {
                        "chain_id": e.chain_id,
                        "trend": e.trend_classification,
                        "urgency": e.urgency_level,
                        "narrative": e.lifecycle_narrative,
                        "recommendation": e.recommendation,
                        "concerns": "; ".join(e.concerns),
                    }
                )
            pd.DataFrame(exp_data).to_csv(
                out_path / "ai_explanations.csv", index=False
            )
            print(f"  Saved: {out_path / 'ai_explanations.csv'}")

        # 3. Save executive summary JSON
        summary = {
            "analysis_id": result.analysis_id,
            "timestamp": result.timestamp.isoformat(),
            "total_anomalies": {
                "2007": result.total_anomalies_2007,
                "2015": result.total_anomalies_2015,
                "2022": result.total_anomalies_2022,
            },
            "matching": {
                "matched_07_15": result.matched_07_15,
                "matched_15_22": result.matched_15_22,
                "total_chains": result.total_chains,
            },
            "dtw_correction": {
                "dtw_applied_07_15": result.dtw_applied_07_15,
                "dtw_applied_15_22": result.dtw_applied_15_22,
                "dtw_fallback_reason_07_15": result.dtw_fallback_reason_07_15,
                "dtw_fallback_reason_15_22": result.dtw_fallback_reason_15_22,
            },
            "clustering": {
                "total_clusters": result.total_clusters,
                "clustered_anomaly_pct": result.clustered_anomaly_pct,
                "interaction_zones_2007": len(result.interaction_zones_2007),
                "interaction_zones_2015": len(result.interaction_zones_2015),
                "interaction_zones_2022": len(result.interaction_zones_2022),
            },
            "trends": {
                "accelerating": result.accelerating_count,
                "stable": result.stable_count,
                "decelerating": result.decelerating_count,
            },
            "risk": {
                "immediate_action_count": result.immediate_action_count,
                "avg_growth_07_15": result.avg_growth_rate_07_15,
                "avg_growth_15_22": result.avg_growth_rate_15_22,
            },
            "status": result.status,
        }
        with open(out_path / "executive_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        print(f"  Saved: {out_path / 'executive_summary.json'}")

