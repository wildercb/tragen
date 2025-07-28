"""
Training Feedback System
========================

Collects and processes feedback for training trading agents.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import json

logger = logging.getLogger(__name__)

class FeedbackType(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    CORRECTION = "correction"
    SUGGESTION = "suggestion"
    RATING = "rating"
    QUESTION = "question"

class FeedbackCategory(Enum):
    DECISION_MAKING = "decision_making"
    TIMING = "timing"
    RISK_MANAGEMENT = "risk_management"
    ANALYSIS_QUALITY = "analysis_quality"
    REASONING = "reasoning"
    EXECUTION = "execution"
    GENERAL = "general"

@dataclass
class TrainingFeedback:
    feedback_id: str
    agent_id: str
    user_id: str
    feedback_type: FeedbackType
    category: FeedbackCategory
    target_event_id: Optional[str]
    rating: Optional[int]  # 1-5 scale
    comment: str
    correction_data: Dict[str, Any]
    timestamp: datetime
    context: Dict[str, Any] = None
    processed: bool = False
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}

@dataclass
class FeedbackSummary:
    agent_id: str
    period_start: datetime
    period_end: datetime
    total_feedback: int
    by_type: Dict[str, int]
    by_category: Dict[str, int]
    average_rating: float
    positive_ratio: float
    improvement_areas: List[str]
    strengths: List[str]
    
class FeedbackCollector:
    """
    Collects and processes training feedback for agents.
    
    Provides:
    - Feedback collection and validation
    - Feedback analysis and insights
    - Performance tracking
    - Learning recommendations
    - Feedback aggregation
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.feedback_config = config.get('feedback', {})
        
        # Feedback storage
        self.feedback_data: Dict[str, List[TrainingFeedback]] = {}
        self.feedback_index: Dict[str, TrainingFeedback] = {}
        
        # Analysis cache
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        
        # Feedback processors
        self.feedback_processors: Dict[FeedbackType, callable] = {
            FeedbackType.POSITIVE: self._process_positive_feedback,
            FeedbackType.NEGATIVE: self._process_negative_feedback,
            FeedbackType.CORRECTION: self._process_correction_feedback,
            FeedbackType.SUGGESTION: self._process_suggestion_feedback,
            FeedbackType.RATING: self._process_rating_feedback,
            FeedbackType.QUESTION: self._process_question_feedback
        }
        
    async def collect_feedback(
        self,
        agent_id: str,
        user_id: str,
        feedback_data: Dict[str, Any]
    ) -> TrainingFeedback:
        """Collect feedback from a user."""
        
        # Validate feedback data
        validation_result = self._validate_feedback_data(feedback_data)
        if not validation_result['valid']:
            raise ValueError(f"Invalid feedback data: {validation_result['errors']}")
            
        # Create feedback object
        feedback = TrainingFeedback(
            feedback_id=feedback_data.get('feedback_id', self._generate_feedback_id()),
            agent_id=agent_id,
            user_id=user_id,
            feedback_type=FeedbackType(feedback_data['type']),
            category=FeedbackCategory(feedback_data.get('category', 'general')),
            target_event_id=feedback_data.get('target_event_id'),
            rating=feedback_data.get('rating'),
            comment=feedback_data.get('comment', ''),
            correction_data=feedback_data.get('correction', {}),
            timestamp=datetime.now(),
            context=feedback_data.get('context', {})
        )
        
        # Store feedback
        if agent_id not in self.feedback_data:
            self.feedback_data[agent_id] = []
            
        self.feedback_data[agent_id].append(feedback)
        self.feedback_index[feedback.feedback_id] = feedback
        
        # Process feedback
        await self._process_feedback(feedback)
        
        # Invalidate cache
        self._invalidate_cache(agent_id)
        
        logger.info(f"Collected {feedback.feedback_type.value} feedback for agent {agent_id}")
        
        return feedback
        
    async def collect_rating_feedback(
        self,
        agent_id: str,
        user_id: str,
        rating: int,
        category: Union[str, FeedbackCategory],
        comment: str = "",
        target_event_id: str = None
    ) -> TrainingFeedback:
        """Collect rating-based feedback."""
        
        if isinstance(category, str):
            category = FeedbackCategory(category)
            
        feedback_data = {
            'type': 'rating',
            'category': category.value,
            'rating': rating,
            'comment': comment,
            'target_event_id': target_event_id
        }
        
        return await self.collect_feedback(agent_id, user_id, feedback_data)
        
    async def collect_correction_feedback(
        self,
        agent_id: str,
        user_id: str,
        target_event_id: str,
        correction: Dict[str, Any],
        explanation: str = ""
    ) -> TrainingFeedback:
        """Collect correction feedback."""
        
        feedback_data = {
            'type': 'correction',
            'category': 'decision_making',
            'target_event_id': target_event_id,
            'correction': correction,
            'comment': explanation
        }
        
        return await self.collect_feedback(agent_id, user_id, feedback_data)
        
    async def collect_suggestion_feedback(
        self,
        agent_id: str,
        user_id: str,
        suggestion: str,
        category: Union[str, FeedbackCategory] = FeedbackCategory.GENERAL
    ) -> TrainingFeedback:
        """Collect suggestion feedback."""
        
        if isinstance(category, str):
            category = FeedbackCategory(category)
            
        feedback_data = {
            'type': 'suggestion',
            'category': category.value,
            'comment': suggestion
        }
        
        return await self.collect_feedback(agent_id, user_id, feedback_data)
        
    async def get_feedback_summary(
        self,
        agent_id: str,
        days: int = 7
    ) -> FeedbackSummary:
        """Get feedback summary for an agent."""
        
        # Check cache
        cache_key = f"{agent_id}_{days}d"
        if self._is_cache_valid(cache_key):
            return self.analysis_cache[cache_key]
            
        period_end = datetime.now()
        period_start = period_end - timedelta(days=days)
        
        # Get feedback for period
        agent_feedback = self.feedback_data.get(agent_id, [])
        period_feedback = [
            f for f in agent_feedback 
            if period_start <= f.timestamp <= period_end
        ]
        
        if not period_feedback:
            return FeedbackSummary(
                agent_id=agent_id,
                period_start=period_start,
                period_end=period_end,
                total_feedback=0,
                by_type={},
                by_category={},
                average_rating=0.0,
                positive_ratio=0.0,
                improvement_areas=[],
                strengths=[]
            )
            
        # Calculate statistics
        by_type = {}
        by_category = {}
        ratings = []
        
        for feedback in period_feedback:
            # Count by type
            feedback_type = feedback.feedback_type.value
            by_type[feedback_type] = by_type.get(feedback_type, 0) + 1
            
            # Count by category
            category = feedback.category.value
            by_category[category] = by_category.get(category, 0) + 1
            
            # Collect ratings
            if feedback.rating is not None:
                ratings.append(feedback.rating)
                
        # Calculate metrics
        average_rating = statistics.mean(ratings) if ratings else 0.0
        positive_feedback = len([f for f in period_feedback if self._is_positive_feedback(f)])
        positive_ratio = positive_feedback / len(period_feedback) if period_feedback else 0.0
        
        # Identify improvement areas and strengths
        improvement_areas = await self._identify_improvement_areas(period_feedback)
        strengths = await self._identify_strengths(period_feedback)
        
        summary = FeedbackSummary(
            agent_id=agent_id,
            period_start=period_start,
            period_end=period_end,
            total_feedback=len(period_feedback),
            by_type=by_type,
            by_category=by_category,
            average_rating=average_rating,
            positive_ratio=positive_ratio,
            improvement_areas=improvement_areas,
            strengths=strengths
        )
        
        # Cache result
        self.analysis_cache[cache_key] = summary
        self.cache_expiry[cache_key] = datetime.now() + timedelta(hours=1)
        
        return summary
        
    async def get_learning_insights(self, agent_id: str) -> Dict[str, Any]:
        """Get learning insights based on feedback patterns."""
        
        agent_feedback = self.feedback_data.get(agent_id, [])
        if not agent_feedback:
            return {'insights': [], 'recommendations': [], 'progress': 'insufficient_data'}
            
        insights = []
        recommendations = []
        
        # Analyze feedback trends
        recent_feedback = agent_feedback[-20:]  # Last 20 pieces of feedback
        older_feedback = agent_feedback[-40:-20] if len(agent_feedback) > 20 else []
        
        # Compare recent vs older performance
        if older_feedback:
            recent_avg = self._calculate_average_rating(recent_feedback)
            older_avg = self._calculate_average_rating(older_feedback)
            
            if recent_avg > older_avg + 0.3:
                insights.append("Agent performance is improving over time")
                progress = 'improving'
            elif recent_avg < older_avg - 0.3:
                insights.append("Agent performance may be declining")
                recommendations.append("Review recent training and feedback patterns")
                progress = 'declining'
            else:
                insights.append("Agent performance is stable")
                progress = 'stable'
        else:
            progress = 'insufficient_data'
            
        # Analyze feedback categories
        category_analysis = self._analyze_feedback_categories(recent_feedback)
        
        for category, analysis in category_analysis.items():
            if analysis['avg_rating'] < 3.0 and analysis['count'] > 2:
                insights.append(f"Needs improvement in {category}")
                recommendations.append(f"Focus training on {category} skills")
            elif analysis['avg_rating'] > 4.0:
                insights.append(f"Strong performance in {category}")
                
        # Common issues
        common_issues = self._identify_common_issues(recent_feedback)
        for issue in common_issues:
            insights.append(f"Common issue: {issue}")
            
        # User engagement
        unique_users = len(set(f.user_id for f in recent_feedback))
        if unique_users > 3:
            insights.append("High user engagement in training")
        elif unique_users == 1:
            recommendations.append("Get feedback from multiple users for diverse perspectives")
            
        return {
            'insights': insights,
            'recommendations': recommendations,
            'progress': progress,
            'recent_performance': self._calculate_average_rating(recent_feedback),
            'feedback_volume': len(recent_feedback),
            'category_breakdown': category_analysis
        }
        
    async def get_feedback_details(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed feedback information."""
        
        if feedback_id not in self.feedback_index:
            return None
            
        feedback = self.feedback_index[feedback_id]
        
        return {
            'feedback': asdict(feedback),
            'processing_status': 'processed' if feedback.processed else 'pending',
            'impact_analysis': await self._analyze_feedback_impact(feedback)
        }
        
    async def update_feedback_processing_status(self, feedback_id: str, processed: bool = True):
        """Update feedback processing status."""
        
        if feedback_id in self.feedback_index:
            self.feedback_index[feedback_id].processed = processed
            
    def get_agent_feedback_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive feedback statistics for an agent."""
        
        agent_feedback = self.feedback_data.get(agent_id, [])
        
        if not agent_feedback:
            return {
                'total_feedback': 0,
                'processed_feedback': 0,
                'average_rating': 0.0,
                'feedback_frequency': 0.0,
                'active_users': 0
            }
            
        processed_count = len([f for f in agent_feedback if f.processed])
        ratings = [f.rating for f in agent_feedback if f.rating is not None]
        
        # Calculate feedback frequency (feedback per day)
        if agent_feedback:
            first_feedback = min(agent_feedback, key=lambda x: x.timestamp).timestamp
            days_active = (datetime.now() - first_feedback).days + 1
            frequency = len(agent_feedback) / days_active
        else:
            frequency = 0.0
            
        return {
            'total_feedback': len(agent_feedback),
            'processed_feedback': processed_count,
            'average_rating': statistics.mean(ratings) if ratings else 0.0,
            'feedback_frequency': frequency,
            'active_users': len(set(f.user_id for f in agent_feedback)),
            'recent_feedback': len([
                f for f in agent_feedback 
                if f.timestamp > datetime.now() - timedelta(days=7)
            ])
        }
        
    def _validate_feedback_data(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate feedback data."""
        
        errors = []
        
        # Required fields
        if 'type' not in feedback_data:
            errors.append("Feedback type is required")
        elif feedback_data['type'] not in [t.value for t in FeedbackType]:
            errors.append(f"Invalid feedback type: {feedback_data['type']}")
            
        # Rating validation
        if feedback_data.get('rating') is not None:
            rating = feedback_data['rating']
            if not isinstance(rating, int) or rating < 1 or rating > 5:
                errors.append("Rating must be an integer between 1 and 5")
                
        # Category validation
        if 'category' in feedback_data:
            if feedback_data['category'] not in [c.value for c in FeedbackCategory]:
                errors.append(f"Invalid category: {feedback_data['category']}")
                
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
        
    async def _process_feedback(self, feedback: TrainingFeedback):
        """Process feedback using appropriate processor."""
        
        processor = self.feedback_processors.get(feedback.feedback_type)
        if processor:
            try:
                await processor(feedback)
                feedback.processed = True
            except Exception as e:
                logger.error(f"Error processing feedback {feedback.feedback_id}: {e}")
                
    async def _process_positive_feedback(self, feedback: TrainingFeedback):
        """Process positive feedback."""
        logger.info(f"Processing positive feedback for agent {feedback.agent_id}")
        
    async def _process_negative_feedback(self, feedback: TrainingFeedback):
        """Process negative feedback."""
        logger.info(f"Processing negative feedback for agent {feedback.agent_id}")
        
    async def _process_correction_feedback(self, feedback: TrainingFeedback):
        """Process correction feedback."""
        logger.info(f"Processing correction feedback for agent {feedback.agent_id}")
        
    async def _process_suggestion_feedback(self, feedback: TrainingFeedback):
        """Process suggestion feedback."""
        logger.info(f"Processing suggestion feedback for agent {feedback.agent_id}")
        
    async def _process_rating_feedback(self, feedback: TrainingFeedback):
        """Process rating feedback."""
        logger.info(f"Processing rating feedback for agent {feedback.agent_id}: {feedback.rating}/5")
        
    async def _process_question_feedback(self, feedback: TrainingFeedback):
        """Process question feedback."""
        logger.info(f"Processing question feedback for agent {feedback.agent_id}")
        
    def _is_positive_feedback(self, feedback: TrainingFeedback) -> bool:
        """Check if feedback is positive."""
        
        if feedback.feedback_type == FeedbackType.POSITIVE:
            return True
        elif feedback.feedback_type == FeedbackType.RATING:
            return feedback.rating is not None and feedback.rating >= 4
        elif feedback.feedback_type == FeedbackType.NEGATIVE:
            return False
            
        return True  # Neutral for other types
        
    def _calculate_average_rating(self, feedback_list: List[TrainingFeedback]) -> float:
        """Calculate average rating from feedback list."""
        
        ratings = [f.rating for f in feedback_list if f.rating is not None]
        return statistics.mean(ratings) if ratings else 0.0
        
    def _analyze_feedback_categories(self, feedback_list: List[TrainingFeedback]) -> Dict[str, Dict[str, Any]]:
        """Analyze feedback by category."""
        
        category_data = {}
        
        for feedback in feedback_list:
            category = feedback.category.value
            
            if category not in category_data:
                category_data[category] = {
                    'count': 0,
                    'ratings': [],
                    'positive_count': 0
                }
                
            category_data[category]['count'] += 1
            
            if feedback.rating is not None:
                category_data[category]['ratings'].append(feedback.rating)
                
            if self._is_positive_feedback(feedback):
                category_data[category]['positive_count'] += 1
                
        # Calculate averages
        for category, data in category_data.items():
            data['avg_rating'] = statistics.mean(data['ratings']) if data['ratings'] else 0.0
            data['positive_ratio'] = data['positive_count'] / data['count'] if data['count'] > 0 else 0.0
            
        return category_data
        
    async def _identify_improvement_areas(self, feedback_list: List[TrainingFeedback]) -> List[str]:
        """Identify areas needing improvement."""
        
        improvement_areas = []
        category_analysis = self._analyze_feedback_categories(feedback_list)
        
        for category, analysis in category_analysis.items():
            if analysis['avg_rating'] < 3.0 and analysis['count'] > 1:
                improvement_areas.append(category.replace('_', ' ').title())
                
        # Analyze correction feedback
        corrections = [f for f in feedback_list if f.feedback_type == FeedbackType.CORRECTION]
        correction_patterns = {}
        
        for correction in corrections:
            correction_type = correction.correction_data.get('type', 'general')
            correction_patterns[correction_type] = correction_patterns.get(correction_type, 0) + 1
            
        for pattern, count in correction_patterns.items():
            if count > 2:  # Multiple corrections of same type
                improvement_areas.append(f"Correction needed in {pattern}")
                
        return improvement_areas[:5]  # Top 5 areas
        
    async def _identify_strengths(self, feedback_list: List[TrainingFeedback]) -> List[str]:
        """Identify strengths based on feedback."""
        
        strengths = []
        category_analysis = self._analyze_feedback_categories(feedback_list)
        
        for category, analysis in category_analysis.items():
            if analysis['avg_rating'] > 4.0 and analysis['count'] > 1:
                strengths.append(category.replace('_', ' ').title())
                
        # Analyze positive feedback comments
        positive_feedback = [
            f for f in feedback_list 
            if f.feedback_type == FeedbackType.POSITIVE and f.comment
        ]
        
        # Simple keyword analysis for strengths
        strength_keywords = {
            'accurate': 'Accurate Analysis',
            'timely': 'Good Timing',
            'risk': 'Risk Management',
            'logical': 'Logical Reasoning',
            'clear': 'Clear Communication'
        }
        
        for feedback in positive_feedback:
            comment_lower = feedback.comment.lower()
            for keyword, strength in strength_keywords.items():
                if keyword in comment_lower and strength not in strengths:
                    strengths.append(strength)
                    
        return strengths[:5]  # Top 5 strengths
        
    def _identify_common_issues(self, feedback_list: List[TrainingFeedback]) -> List[str]:
        """Identify common issues from feedback."""
        
        issues = []
        
        # Analyze negative feedback comments
        negative_feedback = [
            f for f in feedback_list 
            if f.feedback_type == FeedbackType.NEGATIVE and f.comment
        ]
        
        issue_keywords = {
            'timing': 'Poor timing decisions',
            'risk': 'Risk management issues',
            'analysis': 'Analysis quality problems',
            'confidence': 'Overconfidence or underconfidence',
            'market': 'Market condition misreading'
        }
        
        keyword_counts = {}
        for feedback in negative_feedback:
            comment_lower = feedback.comment.lower()
            for keyword, issue in issue_keywords.items():
                if keyword in comment_lower:
                    keyword_counts[issue] = keyword_counts.get(issue, 0) + 1
                    
        # Add issues mentioned multiple times
        for issue, count in keyword_counts.items():
            if count > 1:
                issues.append(issue)
                
        return issues
        
    async def _analyze_feedback_impact(self, feedback: TrainingFeedback) -> Dict[str, Any]:
        """Analyze the potential impact of feedback on agent learning."""
        
        impact_analysis = {
            'priority': 'medium',
            'learning_value': 0.5,
            'action_required': False,
            'notes': []
        }
        
        # High priority for corrections
        if feedback.feedback_type == FeedbackType.CORRECTION:
            impact_analysis['priority'] = 'high'
            impact_analysis['learning_value'] = 0.9
            impact_analysis['action_required'] = True
            impact_analysis['notes'].append('Correction feedback requires immediate attention')
            
        # High priority for very low ratings
        elif feedback.rating is not None and feedback.rating <= 2:
            impact_analysis['priority'] = 'high'
            impact_analysis['learning_value'] = 0.8
            impact_analysis['action_required'] = True
            impact_analysis['notes'].append('Low rating indicates significant issues')
            
        # Medium priority for suggestions
        elif feedback.feedback_type == FeedbackType.SUGGESTION:
            impact_analysis['priority'] = 'medium'
            impact_analysis['learning_value'] = 0.6
            impact_analysis['notes'].append('Suggestion provides improvement opportunity')
            
        return impact_analysis
        
    def _generate_feedback_id(self) -> str:
        """Generate unique feedback ID."""
        import uuid
        return str(uuid.uuid4())
        
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is valid."""
        
        if cache_key not in self.cache_expiry:
            return False
            
        return datetime.now() < self.cache_expiry[cache_key]
        
    def _invalidate_cache(self, agent_id: str):
        """Invalidate cache entries for an agent."""
        
        keys_to_remove = [
            key for key in self.cache_expiry.keys() 
            if key.startswith(agent_id)
        ]
        
        for key in keys_to_remove:
            self.analysis_cache.pop(key, None)
            self.cache_expiry.pop(key, None)
            
    async def cleanup(self):
        """Cleanup feedback system resources."""
        
        # Clear caches
        self.analysis_cache.clear()
        self.cache_expiry.clear()
        
        logger.info("Feedback system cleanup complete")