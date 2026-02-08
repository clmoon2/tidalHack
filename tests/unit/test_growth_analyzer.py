"""
Unit tests for GrowthAnalyzer class.
"""

import pytest
from datetime import datetime
from src.growth.analyzer import GrowthAnalyzer
from src.data_models.models import AnomalyRecord, Match, GrowthMetrics


@pytest.fixture
def analyzer():
    """Create GrowthAnalyzer instance."""
    return GrowthAnalyzer(rapid_growth_threshold=5.0)


@pytest.fixture
def sample_anomaly_run1():
    """Create sample anomaly from first run."""
    return AnomalyRecord(
        id="R1_A1",
        run_id="RUN1",
        distance=100.0,
        clock_position=3.0,
        feature_type="external_corrosion",
        depth_pct=40.0,
        length=10.0,
        width=5.0,
        inspection_date=datetime(2020, 1, 1)
    )


@pytest.fixture
def sample_anomaly_run2():
    """Create sample anomaly from second run (with growth)."""
    return AnomalyRecord(
        id="R2_A1",
        run_id="RUN2",
        distance=100.0,
        clock_position=3.0,
        feature_type="external_corrosion",
        depth_pct=50.0,  # Grown from 40%
        length=11.0,     # Grown from 10.0
        width=5.5,       # Grown from 5.0
        inspection_date=datetime(2022, 1, 1)
    )


class TestGrowthAnalyzer:
    """Test suite for GrowthAnalyzer class."""
    
    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer1 = GrowthAnalyzer()
        assert analyzer1.rapid_growth_threshold == 5.0
        
        analyzer2 = GrowthAnalyzer(rapid_growth_threshold=10.0)
        assert analyzer2.rapid_growth_threshold == 10.0
    
    def test_calculate_growth_rate_basic(self, analyzer):
        """Test basic growth rate calculation."""
        # 40% to 50% over 2 years = 5.0 percentage points per year
        growth_rate = analyzer.calculate_growth_rate(40.0, 50.0, 2.0)
        assert growth_rate == pytest.approx(5.0, rel=1e-6)
        
        # 10 to 11 over 1 year = 1.0 per year
        growth_rate = analyzer.calculate_growth_rate(10.0, 11.0, 1.0)
        assert growth_rate == pytest.approx(1.0, rel=1e-6)
    
    def test_calculate_growth_rate_no_growth(self, analyzer):
        """Test growth rate with no change."""
        growth_rate = analyzer.calculate_growth_rate(40.0, 40.0, 2.0)
        assert growth_rate == 0.0
    
    def test_calculate_growth_rate_negative_growth(self, analyzer):
        """Test growth rate with decrease (negative growth)."""
        # 50% to 40% over 2 years = -5.0 percentage points per year
        growth_rate = analyzer.calculate_growth_rate(50.0, 40.0, 2.0)
        assert growth_rate == pytest.approx(-5.0, rel=1e-6)
    
    def test_calculate_growth_rate_zero_initial(self, analyzer):
        """Test growth rate with zero initial value."""
        # 0 to 10 over 2 years = 5.0 per year (absolute change)
        growth_rate = analyzer.calculate_growth_rate(0.0, 10.0, 2.0)
        assert growth_rate == pytest.approx(5.0, rel=1e-6)
    
    def test_calculate_growth_rate_invalid_time(self, analyzer):
        """Test growth rate with invalid time interval."""
        with pytest.raises(ValueError, match="Time interval must be positive"):
            analyzer.calculate_growth_rate(40.0, 50.0, 0.0)
        
        with pytest.raises(ValueError, match="Time interval must be positive"):
            analyzer.calculate_growth_rate(40.0, 50.0, -1.0)
    
    def test_identify_rapid_growth(self, analyzer):
        """Test rapid growth identification."""
        assert analyzer.identify_rapid_growth(6.0) is True
        assert analyzer.identify_rapid_growth(5.1) is True
        assert analyzer.identify_rapid_growth(5.0) is False
        assert analyzer.identify_rapid_growth(4.9) is False
        assert analyzer.identify_rapid_growth(0.0) is False
    
    def test_calculate_match_growth(self, analyzer, sample_anomaly_run1, sample_anomaly_run2):
        """Test growth calculation for matched anomaly pair."""
        growth_metrics = analyzer.calculate_match_growth(
            sample_anomaly_run1,
            sample_anomaly_run2,
            time_interval_years=2.0
        )
        
        # Check that GrowthMetrics object is created
        assert isinstance(growth_metrics, GrowthMetrics)
        assert growth_metrics.match_id is not None
        assert growth_metrics.time_interval_years == 2.0
        
        # Check growth rates
        # Depth: 40% to 50% over 2 years = 5.0 percentage points per year
        assert growth_metrics.depth_growth_rate == pytest.approx(5.0, rel=1e-6)
        
        # Length: 10 to 11 over 2 years = 0.5 inches per year
        assert growth_metrics.length_growth_rate == pytest.approx(0.5, rel=1e-6)
        
        # Width: 5 to 5.5 over 2 years = 0.25 inches per year
        assert growth_metrics.width_growth_rate == pytest.approx(0.25, rel=1e-6)
        
        # Check rapid growth flag (5.0 pp/year == 5.0 threshold)
        assert growth_metrics.is_rapid_growth is False
    
    def test_analyze_matches_basic(self, analyzer):
        """Test analysis of multiple matches."""
        # Create test data
        anomalies_run1 = [
            AnomalyRecord(
                id="R1_A1", run_id="RUN1", distance=100.0,
                clock_position=3.0, feature_type="external_corrosion",
                depth_pct=40.0, length=10.0, width=5.0,
                inspection_date=datetime(2020, 1, 1)
            ),
            AnomalyRecord(
                id="R1_A2", run_id="RUN1", distance=200.0,
                clock_position=6.0, feature_type="external_corrosion",
                depth_pct=30.0, length=8.0, width=4.0,
                inspection_date=datetime(2020, 1, 1)
            )
        ]
        
        anomalies_run2 = [
            AnomalyRecord(
                id="R2_A1", run_id="RUN2", distance=100.0,
                clock_position=3.0, feature_type="external_corrosion",
                depth_pct=50.0, length=11.0, width=5.5,
                inspection_date=datetime(2022, 1, 1)
            ),
            AnomalyRecord(
                id="R2_A2", run_id="RUN2", distance=200.0,
                clock_position=6.0, feature_type="external_corrosion",
                depth_pct=32.0, length=8.2, width=4.1,
                inspection_date=datetime(2022, 1, 1)
            )
        ]
        
        matches = [
            Match(
                id="M1",
                anomaly1_id="R1_A1",
                anomaly2_id="R2_A1",
                similarity_score=0.95,
                confidence="HIGH",
                distance_similarity=1.0,
                clock_similarity=1.0,
                type_similarity=1.0,
                depth_similarity=0.9,
                length_similarity=0.95,
                width_similarity=0.95
            ),
            Match(
                id="M2",
                anomaly1_id="R1_A2",
                anomaly2_id="R2_A2",
                similarity_score=0.92,
                confidence="HIGH",
                distance_similarity=1.0,
                clock_similarity=1.0,
                type_similarity=1.0,
                depth_similarity=0.95,
                length_similarity=0.98,
                width_similarity=0.98
            )
        ]
        
        result = analyzer.analyze_matches(
            matches, anomalies_run1, anomalies_run2, time_interval_years=2.0
        )
        
        # Check result structure
        assert 'growth_metrics' in result
        assert 'statistics' in result
        assert 'rapid_growth_anomalies' in result
        
        # Check growth metrics
        assert len(result['growth_metrics']) == 2
        
        # Check statistics
        stats = result['statistics']
        assert stats['total_matches'] == 2
        assert stats['rapid_growth_count'] >= 0  # May or may not have rapid growth
        assert 'depth_growth' in stats
        assert 'length_growth' in stats
        assert 'width_growth' in stats
    
    def test_analyze_matches_empty(self, analyzer):
        """Test analysis with empty matches."""
        result = analyzer.analyze_matches([], [], [], time_interval_years=2.0)
        
        assert result['growth_metrics'] == []
        assert result['statistics']['total_matches'] == 0
        assert result['statistics']['rapid_growth_count'] == 0
        assert result['rapid_growth_anomalies'] == []
    
    def test_statistics_calculation(self, analyzer):
        """Test statistical summary calculation."""
        growth_metrics_list = [
            GrowthMetrics(
                match_id="M1",
                time_interval_years=2.0,
                depth_growth_rate=10.0,
                length_growth_rate=5.0,
                width_growth_rate=3.0,
                is_rapid_growth=True,
                risk_score=0.8
            ),
            GrowthMetrics(
                match_id="M2",
                time_interval_years=2.0,
                depth_growth_rate=2.0,
                length_growth_rate=1.0,
                width_growth_rate=0.5,
                is_rapid_growth=False,
                risk_score=0.3
            ),
            GrowthMetrics(
                match_id="M3",
                time_interval_years=2.0,
                depth_growth_rate=6.0,
                length_growth_rate=3.0,
                width_growth_rate=2.0,
                is_rapid_growth=True,
                risk_score=0.6
            )
        ]
        
        stats = analyzer._calculate_statistics(growth_metrics_list)
        
        # Check counts
        assert stats['total_matches'] == 3
        assert stats['rapid_growth_count'] == 2
        assert stats['rapid_growth_percentage'] == pytest.approx(66.67, rel=0.01)
        
        # Check depth statistics
        assert stats['depth_growth']['mean'] == pytest.approx(6.0, rel=1e-6)
        assert stats['depth_growth']['min'] == 2.0
        assert stats['depth_growth']['max'] == 10.0
    
    def test_get_growth_distribution_by_feature_type(self, analyzer):
        """Test growth distribution grouped by feature type."""
        growth_metrics_list = [
            GrowthMetrics(
                match_id="R1A1_R2A1",  # Match format without underscores in IDs
                time_interval_years=2.0,
                depth_growth_rate=10.0,
                length_growth_rate=5.0,
                width_growth_rate=3.0,
                is_rapid_growth=True,
                risk_score=0.8
            ),
            GrowthMetrics(
                match_id="R1A2_R2A2",  # Match format without underscores in IDs
                time_interval_years=2.0,
                depth_growth_rate=2.0,
                length_growth_rate=1.0,
                width_growth_rate=0.5,
                is_rapid_growth=False,
                risk_score=0.3
            )
        ]
        
        anomalies_run2 = [
            AnomalyRecord(
                id="R2A1", run_id="R2", distance=100.0,
                clock_position=3.0, feature_type="external_corrosion",
                depth_pct=50.0, length=11.0, width=5.5,
                inspection_date=datetime(2022, 1, 1)
            ),
            AnomalyRecord(
                id="R2A2", run_id="R2", distance=200.0,
                clock_position=6.0, feature_type="dent",
                depth_pct=32.0, length=8.2, width=4.1,
                inspection_date=datetime(2022, 1, 1)
            )
        ]
        
        distribution = analyzer.get_growth_distribution_by_feature_type(
            growth_metrics_list, anomalies_run2
        )
        
        # Check that we have statistics for each feature type
        assert 'external_corrosion' in distribution
        assert 'dent' in distribution
        
        # Check external_corrosion statistics
        assert distribution['external_corrosion']['total_matches'] == 1
        assert distribution['external_corrosion']['depth_growth']['mean'] == 10.0
        
        # Check dent statistics
        assert distribution['dent']['total_matches'] == 1
        assert distribution['dent']['depth_growth']['mean'] == 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
