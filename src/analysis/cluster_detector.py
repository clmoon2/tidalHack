"""
Cluster Detector
================

Identifies groups of spatially proximate anomalies within a single inspection
run that form ASME B31G interaction zones.  Uses scikit-learn DBSCAN on
(distance, clock_position) features with configurable proximity thresholds.

DBSCAN is the right fit because:
  (a) no need to pre-specify cluster count,
  (b) naturally classifies isolated anomalies as noise (not clustered),
  (c) works well with physical proximity thresholds.

Author: ILI Data Alignment System
Date: 2026
"""

from __future__ import annotations

import math
import uuid
from typing import List, Tuple, Optional

import numpy as np
from sklearn.cluster import DBSCAN

from src.data_models.models import AnomalyRecord, InteractionZone


class ClusterDetector:
    """
    Detect interaction zones (clusters) of spatially-close anomalies
    within a single inspection run.

    Uses DBSCAN with normalised axial / circumferential features so
    that the two proximity thresholds contribute equally.
    """

    def __init__(
        self,
        axial_threshold_ft: float = 1.0,
        clock_threshold: float = 1.5,
        min_cluster_size: int = 2,
        wall_thickness_in: float = 0.25,
    ):
        """
        Args:
            axial_threshold_ft: Maximum axial separation in feet for two
                anomalies to be considered neighbours (default 1.0 ft ≈
                6 × typical wall thickness converted to feet).
            clock_threshold: Maximum circumferential separation in clock
                hours for two anomalies to be neighbours.
            min_cluster_size: Minimum number of anomalies to form a
                cluster (DBSCAN ``min_samples``).
            wall_thickness_in: Nominal wall thickness in inches
                (informational / future use).
        """
        if axial_threshold_ft <= 0:
            raise ValueError("axial_threshold_ft must be positive")
        if clock_threshold <= 0:
            raise ValueError("clock_threshold must be positive")
        if min_cluster_size < 2:
            raise ValueError("min_cluster_size must be >= 2")

        self.axial_threshold_ft = axial_threshold_ft
        self.clock_threshold = clock_threshold
        self.min_cluster_size = min_cluster_size
        self.wall_thickness_in = wall_thickness_in

    # ------------------------------------------------------------------ #
    #  Public API                                                         #
    # ------------------------------------------------------------------ #

    def detect_clusters(
        self,
        anomalies: List[AnomalyRecord],
        run_id: str,
    ) -> Tuple[List[AnomalyRecord], List[InteractionZone]]:
        """
        Run DBSCAN clustering on a list of anomalies.

        Args:
            anomalies: Anomaly records from a single inspection run.
            run_id: Inspection run identifier (stamped on each zone).

        Returns:
            Tuple of:
                - Updated anomaly list (each anomaly that belongs to a
                  cluster has its ``cluster_id`` field set).
                - List of ``InteractionZone`` objects describing each
                  detected cluster.
        """
        if len(anomalies) < self.min_cluster_size:
            return anomalies, []

        # ── 1. Build feature matrix (distance, clock_position) ────────
        distances = np.array([a.distance for a in anomalies], dtype=np.float64)
        clocks = np.array([a.clock_position for a in anomalies], dtype=np.float64)

        # ── 2. Handle clock-position circularity (12 wraps to 1) ──────
        # Convert clock hours to a linear angle (radians) and use the
        # chord-length metric so that 12 and 1 are close.
        clock_angles = (clocks - 1.0) / 11.0 * 2.0 * math.pi  # 0..2π
        clock_x = np.cos(clock_angles)
        clock_y = np.sin(clock_angles)

        # ── 3. Scale features so eps=1 respects both thresholds ───────
        # Axial: divide by threshold so that threshold distance → 1.0
        scaled_dist = distances / self.axial_threshold_ft

        # Circumferential: the max chord length for *clock_threshold*
        # hours is 2·sin(π·clock_threshold/11).  We scale x,y by the
        # inverse so that the threshold maps to unit distance.
        clock_thresh_angle = self.clock_threshold / 11.0 * math.pi
        chord_at_thresh = 2.0 * math.sin(clock_thresh_angle) if clock_thresh_angle < math.pi else 2.0
        if chord_at_thresh < 1e-9:
            chord_at_thresh = 1e-9  # safety
        scaled_cx = clock_x / chord_at_thresh
        scaled_cy = clock_y / chord_at_thresh

        # Stack into (n, 3) feature matrix
        X = np.column_stack([scaled_dist, scaled_cx, scaled_cy])

        # ── 4. DBSCAN ────────────────────────────────────────────────
        db = DBSCAN(eps=1.0, min_samples=self.min_cluster_size, metric="euclidean")
        labels = db.fit_predict(X)

        # ── 5. Build InteractionZone objects ──────────────────────────
        zones = self._build_interaction_zones(anomalies, labels, run_id)

        # ── 6. Stamp cluster_id on each anomaly ─────────────────────
        label_to_zone_id = {}
        for zone in zones:
            for aid in zone.anomaly_ids:
                label_to_zone_id[aid] = zone.zone_id

        updated_anomalies: List[AnomalyRecord] = []
        for a in anomalies:
            zid = label_to_zone_id.get(a.id)
            if zid is not None:
                updated_anomalies.append(a.model_copy(update={"cluster_id": zid}))
            else:
                updated_anomalies.append(a)

        return updated_anomalies, zones

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                   #
    # ------------------------------------------------------------------ #

    def _build_interaction_zones(
        self,
        anomalies: List[AnomalyRecord],
        labels: np.ndarray,
        run_id: str,
    ) -> List[InteractionZone]:
        """
        Build ``InteractionZone`` objects from DBSCAN labels.

        A label of ``-1`` means noise (unclustered); all other labels
        represent clusters.
        """
        # Group anomaly indices by cluster label
        cluster_map: dict[int, List[int]] = {}
        for idx, label in enumerate(labels):
            if label == -1:
                continue  # noise
            cluster_map.setdefault(label, []).append(idx)

        zones: List[InteractionZone] = []
        for label, indices in sorted(cluster_map.items()):
            members = [anomalies[i] for i in indices]
            zone_id = f"ZONE_{run_id}_{label:04d}"

            dists = [m.distance for m in members]
            clks = [m.clock_position for m in members]

            # Circular mean for clock position
            mean_clock = self._circular_mean_clock(clks)

            zone = InteractionZone(
                zone_id=zone_id,
                run_id=run_id,
                anomaly_ids=[m.id for m in members],
                anomaly_count=len(members),
                centroid_distance=float(np.mean(dists)),
                centroid_clock=round(mean_clock, 2),
                span_distance_ft=max(dists) - min(dists),
                span_clock=self._circular_span_clock(clks),
                max_depth_pct=max(m.depth_pct for m in members),
                combined_length_in=sum(m.length for m in members),
            )
            zones.append(zone)

        return zones

    @staticmethod
    def _circular_mean_clock(clocks: List[float]) -> float:
        """Compute the circular mean of clock positions (1-12 scale)."""
        angles = [(c - 1.0) / 11.0 * 2.0 * math.pi for c in clocks]
        mean_sin = sum(math.sin(a) for a in angles) / len(angles)
        mean_cos = sum(math.cos(a) for a in angles) / len(angles)
        mean_angle = math.atan2(mean_sin, mean_cos)
        if mean_angle < 0:
            mean_angle += 2.0 * math.pi
        mean_clock = mean_angle / (2.0 * math.pi) * 11.0 + 1.0
        return mean_clock

    @staticmethod
    def _circular_span_clock(clocks: List[float]) -> float:
        """
        Compute the smallest arc that contains all clock positions.

        Returns the span in clock hours.
        """
        if len(clocks) <= 1:
            return 0.0
        sorted_c = sorted(clocks)
        # Compute gaps, including the wrap-around gap
        gaps = [sorted_c[i + 1] - sorted_c[i] for i in range(len(sorted_c) - 1)]
        wrap_gap = (12.0 - sorted_c[-1]) + (sorted_c[0] - 1.0) + 1.0  # accounts for 12→1 wrap
        gaps.append(wrap_gap)
        # The span is 11 (full circle in clock hours) minus the largest gap
        max_gap = max(gaps)
        span = 11.0 - max_gap
        return max(span, 0.0)

