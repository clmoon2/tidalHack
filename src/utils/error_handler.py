"""
Centralized error handling and user-friendly error messages.
"""

import logging
import traceback
from typing import Optional, Dict, Any
from enum import Enum


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    CRITICAL = "CRITICAL"  # System cannot continue
    ERROR = "ERROR"        # Operation failed but system can continue
    WARNING = "WARNING"    # Non-critical issue
    INFO = "INFO"          # Informational message


class ILISystemError(Exception):
    """Base exception for ILI system errors."""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        """
        Initialize system error.
        
        Args:
            message: Technical error message
            severity: Error severity level
            details: Additional error details
            user_message: User-friendly message
        """
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.details = details or {}
        self.user_message = user_message or self._generate_user_message()
    
    def _generate_user_message(self) -> str:
        """Generate user-friendly error message."""
        return f"An error occurred: {self.message}"


class DataValidationError(ILISystemError):
    """Data validation errors."""
    
    def _generate_user_message(self) -> str:
        return (
            f"Data validation failed: {self.message}\n"
            "Please check your input data and try again."
        )


class AlignmentError(ILISystemError):
    """Alignment errors."""
    
    def _generate_user_message(self) -> str:
        return (
            f"Alignment failed: {self.message}\n"
            "This may indicate significant odometer drift or missing reference points."
        )


class MatchingError(ILISystemError):
    """Matching errors."""
    
    def _generate_user_message(self) -> str:
        return (
            f"Anomaly matching failed: {self.message}\n"
            "This may indicate poor data quality or incompatible inspection runs."
        )


class PredictionError(ILISystemError):
    """ML prediction errors."""
    
    def _generate_user_message(self) -> str:
        return (
            f"Prediction failed: {self.message}\n"
            "This may indicate insufficient training data or model issues."
        )


class ErrorHandler:
    """
    Centralized error handler with logging and user-friendly messages.
    """
    
    def __init__(self, logger_name: str = "ili_system"):
        """
        Initialize error handler.
        
        Args:
            logger_name: Name for logger
        """
        self.logger = logging.getLogger(logger_name)
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[str] = None,
        raise_error: bool = True
    ) -> Dict[str, Any]:
        """
        Handle error with logging and user-friendly message.
        
        Args:
            error: Exception to handle
            context: Context where error occurred
            raise_error: Whether to re-raise the error
        
        Returns:
            Dictionary with error information
        """
        # Determine severity
        if isinstance(error, ILISystemError):
            severity = error.severity
            user_message = error.user_message
            details = error.details
        else:
            severity = ErrorSeverity.ERROR
            user_message = f"An unexpected error occurred: {str(error)}"
            details = {}
        
        # Log error
        log_message = f"{context}: {str(error)}" if context else str(error)
        
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, exc_info=True)
        elif severity == ErrorSeverity.ERROR:
            self.logger.error(log_message, exc_info=True)
        elif severity == ErrorSeverity.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # Create error info
        error_info = {
            'severity': severity.value,
            'message': str(error),
            'user_message': user_message,
            'context': context,
            'details': details,
            'traceback': traceback.format_exc() if severity in [ErrorSeverity.CRITICAL, ErrorSeverity.ERROR] else None
        }
        
        # Re-raise if requested
        if raise_error:
            raise error
        
        return error_info
    
    def log_warning(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log a warning message.
        
        Args:
            message: Warning message
            details: Additional details
        """
        self.logger.warning(message)
        if details:
            self.logger.warning(f"Details: {details}")
    
    def log_info(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log an info message.
        
        Args:
            message: Info message
            details: Additional details
        """
        self.logger.info(message)
        if details:
            self.logger.debug(f"Details: {details}")


class DataQualityWarning:
    """
    Data quality warnings for non-critical issues.
    """
    
    @staticmethod
    def low_match_rate(match_rate: float, threshold: float = 0.95) -> Optional[str]:
        """
        Warning for low match rate.
        
        Args:
            match_rate: Achieved match rate
            threshold: Expected threshold
        
        Returns:
            Warning message if applicable
        """
        if match_rate < threshold:
            return (
                f"⚠️ Match rate ({match_rate:.1%}) is below expected threshold ({threshold:.1%}).\n"
                "This may indicate:\n"
                "• Significant odometer drift between runs\n"
                "• Missing or misaligned reference points\n"
                "• Different inspection technologies or vendors\n"
                "• Actual changes in pipeline (repairs, replacements)\n\n"
                "Recommendation: Review alignment quality and reference point matching."
            )
        return None
    
    @staticmethod
    def high_rmse(rmse: float, threshold: float = 10.0) -> Optional[str]:
        """
        Warning for high RMSE.
        
        Args:
            rmse: Achieved RMSE
            threshold: Expected threshold
        
        Returns:
            Warning message if applicable
        """
        if rmse > threshold:
            return (
                f"⚠️ Alignment RMSE ({rmse:.1f} ft) exceeds threshold ({threshold:.1f} ft).\n"
                "This may indicate:\n"
                "• Poor odometer calibration\n"
                "• Significant pipeline changes\n"
                "• Inconsistent reference point identification\n\n"
                "Recommendation: Review distance correction function and reference points."
            )
        return None
    
    @staticmethod
    def low_confidence_matches(low_conf_count: int, total: int, threshold: float = 0.1) -> Optional[str]:
        """
        Warning for many low-confidence matches.
        
        Args:
            low_conf_count: Number of low-confidence matches
            total: Total matches
            threshold: Acceptable fraction
        
        Returns:
            Warning message if applicable
        """
        if total > 0 and (low_conf_count / total) > threshold:
            return (
                f"⚠️ {low_conf_count} of {total} matches ({low_conf_count/total:.1%}) have low confidence.\n"
                "This may indicate:\n"
                "• Anomalies have changed significantly\n"
                "• Poor data quality in one or both runs\n"
                "• Incorrect similarity thresholds\n\n"
                "Recommendation: Review low-confidence matches manually and adjust thresholds if needed."
            )
        return None
    
    @staticmethod
    def insufficient_training_data(sample_count: int, min_required: int = 100) -> Optional[str]:
        """
        Warning for insufficient ML training data.
        
        Args:
            sample_count: Number of training samples
            min_required: Minimum required samples
        
        Returns:
            Warning message if applicable
        """
        if sample_count < min_required:
            return (
                f"⚠️ Only {sample_count} training samples available (minimum {min_required} recommended).\n"
                "This may result in:\n"
                "• Poor prediction accuracy\n"
                "• Overfitting to limited data\n"
                "• Unreliable confidence intervals\n\n"
                "Recommendation: Collect more historical data or use rule-based growth analysis instead."
            )
        return None
    
    @staticmethod
    def alignment_failure_guidance() -> str:
        """
        Guidance for alignment failures.
        
        Returns:
            Actionable guidance
        """
        return (
            "🔧 Alignment Failure - Troubleshooting Steps:\n\n"
            "1. Check Reference Points:\n"
            "   • Ensure both runs have sufficient reference points (>10 recommended)\n"
            "   • Verify reference point types match (girth_weld, valve, etc.)\n"
            "   • Check for consistent naming/identification\n\n"
            "2. Review Data Quality:\n"
            "   • Check for missing or invalid distance values\n"
            "   • Verify distance units are consistent\n"
            "   • Look for gaps or discontinuities in data\n\n"
            "3. Adjust Parameters:\n"
            "   • Increase DTW drift constraint (default 10%)\n"
            "   • Adjust similarity thresholds\n"
            "   • Try different alignment algorithms\n\n"
            "4. Manual Review:\n"
            "   • Visually inspect pipeline schematics\n"
            "   • Identify known changes (repairs, replacements)\n"
            "   • Document any pipeline modifications"
        )
