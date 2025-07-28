"""
Data Quality Manager
===================

Real-time data validation and quality assurance for production trading.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import numpy as np
from decimal import Decimal

logger = logging.getLogger(__name__)

class QualityIssueType(Enum):
    PRICE_SPIKE = "price_spike"
    PRICE_GAP = "price_gap"
    VOLUME_ANOMALY = "volume_anomaly"
    TIMESTAMP_ERROR = "timestamp_error"
    OHLC_INCONSISTENCY = "ohlc_inconsistency"
    STALE_DATA = "stale_data"
    MISSING_DATA = "missing_data"
    DUPLICATE_DATA = "duplicate_data"

@dataclass
class QualityIssue:
    issue_type: QualityIssueType
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    field: Optional[str] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class QualityReport:
    symbol: str
    timestamp: datetime
    overall_score: float  # 0.0 to 1.0
    issues: List[QualityIssue]
    recommendation: str  # 'ACCEPT', 'CAUTION', 'REJECT'
    metrics: Dict[str, float]
    
class DataQualityManager:
    """
    Production-grade data quality management with real-time validation.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.quality_config = config.get('data_quality', {})
        
        # Quality thresholds
        self.thresholds = {
            'price_spike_threshold': self.quality_config.get('price_spike_threshold', 0.05),  # 5%
            'volume_spike_threshold': self.quality_config.get('volume_spike_threshold', 5.0),  # 5x
            'stale_data_threshold': self.quality_config.get('stale_data_threshold', 300),  # 5 minutes
            'gap_threshold': self.quality_config.get('gap_threshold', 0.02),  # 2%
            'min_quality_score': self.quality_config.get('min_quality_score', 0.7)
        }
        
        # Historical data for validation
        self.price_history: Dict[str, List[Tuple[datetime, Decimal]]] = {}
        self.volume_history: Dict[str, List[Tuple[datetime, int]]] = {}
        self.history_length = 100  # Keep last 100 data points
        
        # Statistics for anomaly detection
        self.price_stats: Dict[str, Dict[str, float]] = {}
        self.volume_stats: Dict[str, Dict[str, float]] = {}
        
    async def validate_market_data(self, data: Dict[str, Any]) -> QualityReport:
        """
        Validate market data and generate quality report.
        
        Args:
            data: Market data dictionary with OHLCV data
            
        Returns:
            QualityReport with validation results
        """
        symbol = data.get('symbol', 'UNKNOWN')
        timestamp = data.get('timestamp', datetime.now())
        
        if isinstance(timestamp, (str, int, float)):
            timestamp = self._parse_timestamp(timestamp)
            
        issues = []
        metrics = {}
        
        # Basic data validation
        basic_issues = self._validate_basic_data(data)
        issues.extend(basic_issues)
        
        # OHLC consistency validation
        ohlc_issues = self._validate_ohlc_consistency(data)
        issues.extend(ohlc_issues)
        
        # Price spike detection
        price_issues = await self._detect_price_anomalies(symbol, data)
        issues.extend(price_issues)
        
        # Volume anomaly detection
        volume_issues = await self._detect_volume_anomalies(symbol, data)
        issues.extend(volume_issues)
        
        # Timestamp validation
        timestamp_issues = self._validate_timestamp(data)
        issues.extend(timestamp_issues)
        
        # Data freshness check
        freshness_issues = self._validate_data_freshness(data)
        issues.extend(freshness_issues)
        
        # Calculate overall quality score
        overall_score = self._calculate_quality_score(issues)
        
        # Determine recommendation
        recommendation = self._determine_recommendation(overall_score, issues)
        
        # Update historical data
        self._update_history(symbol, data)
        
        # Calculate metrics
        metrics = self._calculate_quality_metrics(data, issues)
        
        report = QualityReport(
            symbol=symbol,
            timestamp=timestamp,
            overall_score=overall_score,
            issues=issues,
            recommendation=recommendation,
            metrics=metrics
        )
        
        # Log significant quality issues
        if overall_score < 0.8 or any(issue.severity in ['high', 'critical'] for issue in issues):
            logger.warning(
                f"Data quality issues for {symbol}: "
                f"score={overall_score:.2f}, issues={len(issues)}, "
                f"recommendation={recommendation}"
            )
            
        return report
        
    def _validate_basic_data(self, data: Dict[str, Any]) -> List[QualityIssue]:
        """Validate basic data structure and values."""
        issues = []
        
        required_fields = ['symbol', 'open', 'high', 'low', 'close', 'volume']
        
        for field in required_fields:
            if field not in data or data[field] is None:
                issues.append(QualityIssue(
                    issue_type=QualityIssueType.MISSING_DATA,
                    severity='critical',
                    message=f"Missing required field: {field}",
                    field=field
                ))
                continue
                
            # Validate numeric fields
            if field in ['open', 'high', 'low', 'close']:
                try:
                    value = float(data[field])
                    if value <= 0:
                        issues.append(QualityIssue(
                            issue_type=QualityIssueType.OHLC_INCONSISTENCY,
                            severity='critical',
                            message=f"Invalid {field} value: {value} (must be > 0)",
                            field=field,
                            actual_value=value
                        ))
                    elif value > 1000000:  # Sanity check for extremely high prices
                        issues.append(QualityIssue(
                            issue_type=QualityIssueType.PRICE_SPIKE,
                            severity='high',
                            message=f"Suspiciously high {field} value: {value}",
                            field=field,
                            actual_value=value
                        ))
                except (ValueError, TypeError):
                    issues.append(QualityIssue(
                        issue_type=QualityIssueType.OHLC_INCONSISTENCY,
                        severity='critical',
                        message=f"Invalid {field} value type: {type(data[field])}",
                        field=field,
                        actual_value=data[field]
                    ))
                    
            elif field == 'volume':
                try:
                    value = int(data[field])
                    if value < 0:
                        issues.append(QualityIssue(
                            issue_type=QualityIssueType.VOLUME_ANOMALY,
                            severity='high',
                            message=f"Negative volume: {value}",
                            field=field,
                            actual_value=value
                        ))
                except (ValueError, TypeError):
                    issues.append(QualityIssue(
                        issue_type=QualityIssueType.VOLUME_ANOMALY,
                        severity='high',
                        message=f"Invalid volume value type: {type(data[field])}",
                        field=field,
                        actual_value=data[field]
                    ))
                    
        return issues
        
    def _validate_ohlc_consistency(self, data: Dict[str, Any]) -> List[QualityIssue]:
        """Validate OHLC consistency."""
        issues = []
        
        try:
            open_price = float(data.get('open', 0))
            high_price = float(data.get('high', 0))
            low_price = float(data.get('low', 0))
            close_price = float(data.get('close', 0))
            
            # High should be >= max(open, close)
            if high_price < max(open_price, close_price):
                issues.append(QualityIssue(
                    issue_type=QualityIssueType.OHLC_INCONSISTENCY,
                    severity='critical',
                    message=f"High ({high_price}) < max(open, close) ({max(open_price, close_price)})",
                    field='high',
                    actual_value=high_price,
                    expected_value=max(open_price, close_price)
                ))
                
            # Low should be <= min(open, close)
            if low_price > min(open_price, close_price):
                issues.append(QualityIssue(
                    issue_type=QualityIssueType.OHLC_INCONSISTENCY,
                    severity='critical',
                    message=f"Low ({low_price}) > min(open, close) ({min(open_price, close_price)})",
                    field='low',
                    actual_value=low_price,
                    expected_value=min(open_price, close_price)
                ))
                
            # High should be >= low
            if high_price < low_price:
                issues.append(QualityIssue(
                    issue_type=QualityIssueType.OHLC_INCONSISTENCY,
                    severity='critical',
                    message=f"High ({high_price}) < Low ({low_price})",
                    field='high',
                    actual_value=high_price,
                    expected_value=low_price
                ))
                
        except (ValueError, TypeError) as e:
            issues.append(QualityIssue(
                issue_type=QualityIssueType.OHLC_INCONSISTENCY,
                severity='critical',
                message=f"Error validating OHLC consistency: {e}"
            ))
            
        return issues
        
    async def _detect_price_anomalies(self, symbol: str, data: Dict[str, Any]) -> List[QualityIssue]:
        """Detect price spikes and anomalies."""
        issues = []
        
        if symbol not in self.price_history or len(self.price_history[symbol]) < 5:
            # Not enough history for anomaly detection
            return issues
            
        try:
            current_price = float(data.get('close', 0))
            if current_price <= 0:
                return issues
                
            # Get recent prices
            recent_prices = [float(price) for _, price in self.price_history[symbol][-10:]]
            
            if len(recent_prices) < 3:
                return issues
                
            # Calculate moving average and standard deviation
            avg_price = np.mean(recent_prices)
            std_price = np.std(recent_prices)
            
            # Detect price spikes using z-score
            if std_price > 0:
                z_score = abs(current_price - avg_price) / std_price
                
                if z_score > 3.0:  # 3 standard deviations
                    severity = 'critical' if z_score > 5.0 else 'high'
                    issues.append(QualityIssue(
                        issue_type=QualityIssueType.PRICE_SPIKE,
                        severity=severity,
                        message=f"Price spike detected: {current_price} (z-score: {z_score:.2f})",
                        field='close',
                        actual_value=current_price,
                        expected_value=avg_price
                    ))
                    
            # Detect percentage-based price gaps
            last_price = recent_prices[-1]
            price_change_pct = abs(current_price - last_price) / last_price
            
            if price_change_pct > self.thresholds['price_spike_threshold']:
                severity = 'critical' if price_change_pct > 0.1 else 'high'
                issues.append(QualityIssue(
                    issue_type=QualityIssueType.PRICE_GAP,
                    severity=severity,
                    message=f"Large price gap: {price_change_pct:.2%} change",
                    field='close',
                    actual_value=current_price,
                    expected_value=last_price
                ))
                
        except Exception as e:
            logger.error(f"Error detecting price anomalies for {symbol}: {e}")
            
        return issues
        
    async def _detect_volume_anomalies(self, symbol: str, data: Dict[str, Any]) -> List[QualityIssue]:
        """Detect volume anomalies."""
        issues = []
        
        if symbol not in self.volume_history or len(self.volume_history[symbol]) < 5:
            return issues
            
        try:
            current_volume = int(data.get('volume', 0))
            if current_volume < 0:
                return issues
                
            # Get recent volumes
            recent_volumes = [volume for _, volume in self.volume_history[symbol][-10:]]
            
            if len(recent_volumes) < 3:
                return issues
                
            # Calculate average volume
            avg_volume = np.mean(recent_volumes)
            
            if avg_volume > 0:
                volume_ratio = current_volume / avg_volume
                
                # Detect volume spikes
                if volume_ratio > self.thresholds['volume_spike_threshold']:
                    severity = 'high' if volume_ratio < 10 else 'medium'
                    issues.append(QualityIssue(
                        issue_type=QualityIssueType.VOLUME_ANOMALY,
                        severity=severity,
                        message=f"Volume spike: {volume_ratio:.1f}x normal volume",
                        field='volume',
                        actual_value=current_volume,
                        expected_value=int(avg_volume)
                    ))
                    
            # Detect zero volume (suspicious for active markets)
            if current_volume == 0 and avg_volume > 0:
                issues.append(QualityIssue(
                    issue_type=QualityIssueType.VOLUME_ANOMALY,
                    severity='medium',
                    message="Zero volume in active market",
                    field='volume',
                    actual_value=0,
                    expected_value=int(avg_volume)
                ))
                
        except Exception as e:
            logger.error(f"Error detecting volume anomalies for {symbol}: {e}")
            
        return issues
        
    def _validate_timestamp(self, data: Dict[str, Any]) -> List[QualityIssue]:
        """Validate timestamp."""
        issues = []
        
        timestamp = data.get('timestamp')
        if not timestamp:
            issues.append(QualityIssue(
                issue_type=QualityIssueType.TIMESTAMP_ERROR,
                severity='high',
                message="Missing timestamp",
                field='timestamp'
            ))
            return issues
            
        try:
            if isinstance(timestamp, (str, int, float)):
                parsed_timestamp = self._parse_timestamp(timestamp)
            else:
                parsed_timestamp = timestamp
                
            now = datetime.now()
            
            # Check if timestamp is in the future
            if parsed_timestamp > now + timedelta(minutes=5):
                issues.append(QualityIssue(
                    issue_type=QualityIssueType.TIMESTAMP_ERROR,
                    severity='high',
                    message=f"Future timestamp: {parsed_timestamp}",
                    field='timestamp',
                    actual_value=parsed_timestamp,
                    expected_value=now
                ))
                
            # Check if timestamp is too old
            if now - parsed_timestamp > timedelta(hours=24):
                issues.append(QualityIssue(
                    issue_type=QualityIssueType.STALE_DATA,
                    severity='medium',
                    message=f"Very old timestamp: {parsed_timestamp}",
                    field='timestamp',
                    actual_value=parsed_timestamp,
                    expected_value=now
                ))
                
        except Exception as e:
            issues.append(QualityIssue(
                issue_type=QualityIssueType.TIMESTAMP_ERROR,
                severity='high',
                message=f"Invalid timestamp format: {e}",
                field='timestamp',
                actual_value=timestamp
            ))
            
        return issues
        
    def _validate_data_freshness(self, data: Dict[str, Any]) -> List[QualityIssue]:
        """Validate data freshness."""
        issues = []
        
        timestamp = data.get('timestamp')
        if not timestamp:
            return issues
            
        try:
            if isinstance(timestamp, (str, int, float)):
                parsed_timestamp = self._parse_timestamp(timestamp)
            else:
                parsed_timestamp = timestamp
                
            now = datetime.now()
            age_seconds = (now - parsed_timestamp).total_seconds()
            
            if age_seconds > self.thresholds['stale_data_threshold']:
                severity = 'high' if age_seconds > 3600 else 'medium'  # 1 hour threshold
                issues.append(QualityIssue(
                    issue_type=QualityIssueType.STALE_DATA,
                    severity=severity,
                    message=f"Stale data: {age_seconds:.0f} seconds old",
                    field='timestamp',
                    actual_value=parsed_timestamp,
                    expected_value=now
                ))
                
        except Exception as e:
            logger.error(f"Error validating data freshness: {e}")
            
        return issues
        
    def _calculate_quality_score(self, issues: List[QualityIssue]) -> float:
        """Calculate overall quality score based on issues."""
        if not issues:
            return 1.0
            
        # Penalty weights for different severity levels
        penalty_weights = {
            'low': 0.05,
            'medium': 0.15,
            'high': 0.30,
            'critical': 0.50
        }
        
        total_penalty = sum(penalty_weights.get(issue.severity, 0.10) for issue in issues)
        
        # Cap total penalty at 0.95 (minimum score of 0.05)
        total_penalty = min(0.95, total_penalty)
        
        return max(0.0, 1.0 - total_penalty)
        
    def _determine_recommendation(self, score: float, issues: List[QualityIssue]) -> str:
        """Determine recommendation based on quality score and issues."""
        # Check for critical issues
        critical_issues = [issue for issue in issues if issue.severity == 'critical']
        if critical_issues:
            return 'REJECT'
            
        # Check overall score
        if score >= 0.9:
            return 'ACCEPT'
        elif score >= 0.7:
            return 'CAUTION'
        else:
            return 'REJECT'
            
    def _update_history(self, symbol: str, data: Dict[str, Any]):
        """Update historical data for future validation."""
        try:
            timestamp = data.get('timestamp', datetime.now())
            if isinstance(timestamp, (str, int, float)):
                timestamp = self._parse_timestamp(timestamp)
                
            # Update price history
            close_price = Decimal(str(data.get('close', 0)))
            if symbol not in self.price_history:
                self.price_history[symbol] = []
                
            self.price_history[symbol].append((timestamp, close_price))
            
            # Keep only recent history
            if len(self.price_history[symbol]) > self.history_length:
                self.price_history[symbol] = self.price_history[symbol][-self.history_length:]
                
            # Update volume history
            volume = int(data.get('volume', 0))
            if symbol not in self.volume_history:
                self.volume_history[symbol] = []
                
            self.volume_history[symbol].append((timestamp, volume))
            
            # Keep only recent history
            if len(self.volume_history[symbol]) > self.history_length:
                self.volume_history[symbol] = self.volume_history[symbol][-self.history_length:]
                
        except Exception as e:
            logger.error(f"Error updating history for {symbol}: {e}")
            
    def _calculate_quality_metrics(self, data: Dict[str, Any], issues: List[QualityIssue]) -> Dict[str, float]:
        """Calculate quality metrics."""
        symbol = data.get('symbol', 'UNKNOWN')
        metrics = {}
        
        # Issue counts by severity
        metrics['critical_issues'] = len([i for i in issues if i.severity == 'critical'])
        metrics['high_issues'] = len([i for i in issues if i.severity == 'high'])
        metrics['medium_issues'] = len([i for i in issues if i.severity == 'medium'])
        metrics['low_issues'] = len([i for i in issues if i.severity == 'low'])
        
        # Data completeness
        required_fields = ['symbol', 'open', 'high', 'low', 'close', 'volume', 'timestamp']
        complete_fields = sum(1 for field in required_fields if data.get(field) is not None)
        metrics['completeness'] = complete_fields / len(required_fields)
        
        # Historical availability
        price_history_length = len(self.price_history.get(symbol, []))
        metrics['history_availability'] = min(1.0, price_history_length / 50)  # Normalize to 50 points
        
        # Data freshness
        timestamp = data.get('timestamp')
        if timestamp:
            try:
                if isinstance(timestamp, (str, int, float)):
                    timestamp = self._parse_timestamp(timestamp)
                age_seconds = (datetime.now() - timestamp).total_seconds()
                metrics['freshness'] = max(0.0, 1.0 - (age_seconds / 3600))  # 1 hour max age
            except:
                metrics['freshness'] = 0.0
        else:
            metrics['freshness'] = 0.0
            
        return metrics
        
    def _parse_timestamp(self, timestamp) -> datetime:
        """Parse various timestamp formats."""
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, (int, float)):
            # Unix timestamp
            if timestamp > 1e10:  # Milliseconds
                return datetime.fromtimestamp(timestamp / 1000)
            else:  # Seconds
                return datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, str):
            # Try to parse ISO format
            try:
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                # Try other common formats
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d %H:%M:%S.%f',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S.%f'
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(timestamp, fmt)
                    except:
                        continue
                        
                raise ValueError(f"Unable to parse timestamp: {timestamp}")
        else:
            raise ValueError(f"Invalid timestamp type: {type(timestamp)}")
            
    def get_quality_summary(self) -> Dict[str, Any]:
        """Get quality summary for all symbols."""
        summary = {
            'symbols_tracked': len(self.price_history),
            'total_price_points': sum(len(history) for history in self.price_history.values()),
            'total_volume_points': sum(len(history) for history in self.volume_history.values()),
            'thresholds': self.thresholds.copy()
        }
        
        return summary
        
    def clear_history(self, symbol: Optional[str] = None):
        """Clear historical data for a symbol or all symbols."""
        if symbol:
            self.price_history.pop(symbol, None)
            self.volume_history.pop(symbol, None)
            self.price_stats.pop(symbol, None)
            self.volume_stats.pop(symbol, None)
            logger.info(f"Cleared quality history for {symbol}")
        else:
            self.price_history.clear()
            self.volume_history.clear()
            self.price_stats.clear()
            self.volume_stats.clear()
            logger.info("Cleared all quality history")