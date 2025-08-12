"""
Context Analyzer Module
Provides context analysis and proactive insights for conversations
"""

import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from models.conversation_models import UserProfile


class ContextAnalyzer:
    """
    Analyzes conversation context and generates proactive insights
    """
    
    def __init__(self):
        self.urgency_keywords = [
            'urgent', 'asap', 'emergency', 'critical', 'immediate', 
            'right now', 'help', 'broken', 'down', 'not working',
            'issue', 'problem', 'error', 'failed', 'failure'
        ]
        
        self.escalation_keywords = [
            'manager', 'supervisor', 'escalate', 'speak to someone',
            'human', 'person', 'representative', 'agent', 'support'
        ]
        
        self.sentiment_positive = [
            'thank', 'thanks', 'great', 'excellent', 'perfect',
            'good', 'helpful', 'awesome', 'amazing'
        ]
        
        self.sentiment_negative = [
            'frustrated', 'angry', 'upset', 'disappointed', 'terrible',
            'awful', 'horrible', 'worst', 'hate', 'stupid'
        ]

    async def analyze_conversation_context(
        self, 
        user_id: str, 
        message: str, 
        user_profile: Optional[UserProfile] = None
    ) -> Dict[str, Any]:
        """
        Analyze the context of a conversation message
        
        Args:
            user_id: User identifier
            message: The message to analyze
            user_profile: User profile information
            
        Returns:
            Dict containing context analysis results
        """
        analysis = {
            'urgency_level': self._assess_urgency(message),
            'sentiment': self._analyze_sentiment(message),
            'intent': self._detect_intent(message),
            'escalation_required': self._check_escalation_needs(message),
            'technical_complexity': self._assess_technical_complexity(message),
            'user_context': self._analyze_user_context(user_profile),
            'keywords': self._extract_keywords(message),
            'timestamp': datetime.now().isoformat()
        }
        
        return analysis

    async def generate_proactive_insights(
        self, 
        user_profile: Optional[UserProfile], 
        recent_conversations: List[Dict], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate proactive insights based on user patterns and context
        
        Args:
            user_profile: User profile information
            recent_conversations: Recent conversation history
            context: Additional context information
            
        Returns:
            Dict containing proactive insights
        """
        insights = {
            'patterns': self._analyze_conversation_patterns(recent_conversations),
            'recommendations': self._generate_recommendations(user_profile, recent_conversations),
            'next_actions': self._suggest_next_actions(recent_conversations, context),
            'user_satisfaction_trend': self._analyze_satisfaction_trend(recent_conversations),
            'common_issues': self._identify_common_issues(recent_conversations),
            'optimization_opportunities': self._identify_optimizations(recent_conversations)
        }
        
        return insights

    def _assess_urgency(self, message: str) -> str:
        """Assess the urgency level of a message"""
        message_lower = message.lower()
        urgency_score = sum(1 for keyword in self.urgency_keywords if keyword in message_lower)
        
        if urgency_score >= 3:
            return 'high'
        elif urgency_score >= 1:
            return 'medium'
        else:
            return 'low'

    def _analyze_sentiment(self, message: str) -> Dict[str, Any]:
        """Analyze sentiment of the message"""
        message_lower = message.lower()
        
        positive_score = sum(1 for word in self.sentiment_positive if word in message_lower)
        negative_score = sum(1 for word in self.sentiment_negative if word in message_lower)
        
        if positive_score > negative_score:
            sentiment = 'positive'
            confidence = min(0.9, 0.5 + (positive_score - negative_score) * 0.1)
        elif negative_score > positive_score:
            sentiment = 'negative'
            confidence = min(0.9, 0.5 + (negative_score - positive_score) * 0.1)
        else:
            sentiment = 'neutral'
            confidence = 0.5
            
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'positive_indicators': positive_score,
            'negative_indicators': negative_score
        }

    def _detect_intent(self, message: str) -> str:
        """Detect the intent of the message"""
        message_lower = message.lower()
        
        question_words = ['what', 'how', 'when', 'where', 'why', 'which', 'who']
        if any(word in message_lower for word in question_words) or '?' in message:
            return 'question'
        
        request_words = ['please', 'can you', 'could you', 'would you', 'help me']
        if any(phrase in message_lower for phrase in request_words):
            return 'request'
        
        complaint_words = ['problem', 'issue', 'error', 'broken', 'not working']
        if any(word in message_lower for word in complaint_words):
            return 'complaint'
        
        if any(word in message_lower for word in self.sentiment_positive):
            return 'feedback_positive'
        
        return 'general'

    def _check_escalation_needs(self, message: str) -> bool:
        """Check if the message indicates need for escalation"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.escalation_keywords)

    def _assess_technical_complexity(self, message: str) -> str:
        """Assess the technical complexity of the request"""
        technical_terms = [
            'api', 'database', 'server', 'network', 'configuration',
            'integration', 'authentication', 'ssl', 'firewall',
            'deployment', 'kubernetes', 'docker', 'cloud'
        ]
        
        message_lower = message.lower()
        complexity_score = sum(1 for term in technical_terms if term in message_lower)
        
        if complexity_score >= 3:
            return 'high'
        elif complexity_score >= 1:
            return 'medium'
        else:
            return 'low'

    def _analyze_user_context(self, user_profile: Optional[UserProfile]) -> Dict[str, Any]:
        """Analyze user context from profile"""
        if not user_profile:
            return {'profile_available': False}
        
        context = {
            'profile_available': True,
            'user_id': user_profile.get('user_id'),
            'preferences_set': bool(user_profile.get('preferences')),
            'interaction_count': len(user_profile.get('conversation_history', [])) if user_profile.get('conversation_history') else 0
        }
        
        if user_profile.get('preferences'):
            context['communication_style'] = user_profile['preferences'].get('communication_style', 'standard')
            context['technical_level'] = user_profile['preferences'].get('technical_level', 'intermediate')
        
        return context

    def _extract_keywords(self, message: str) -> List[str]:
        """Extract important keywords from the message"""
        # Simple keyword extraction - could be enhanced with NLP
        words = re.findall(r'\b\w+\b', message.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can'
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return list(set(keywords))[:10]  # Return unique keywords, limit to 10

    def _analyze_conversation_patterns(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in conversation history"""
        if not conversations:
            return {}
        
        patterns = {
            'total_conversations': len(conversations),
            'average_response_time': self._calculate_avg_response_time(conversations),
            'common_topics': self._identify_common_topics(conversations),
            'resolution_rate': self._calculate_resolution_rate(conversations),
            'escalation_frequency': self._calculate_escalation_frequency(conversations)
        }
        
        return patterns

    def _generate_recommendations(self, user_profile: Optional[UserProfile], conversations: List[Dict]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if conversations:
            # Analyze recent conversation trends
            recent_issues = [conv.get('category', 'general') for conv in conversations[-5:]]
            if len(set(recent_issues)) == 1:
                recommendations.append(f"Consider creating a knowledge base article for {recent_issues[0]} issues")
        
        if user_profile and user_profile.get('preferences'):
            tech_level = user_profile['preferences'].get('technical_level', 'intermediate')
            if tech_level == 'beginner':
                recommendations.append("Provide more detailed explanations with step-by-step guidance")
            elif tech_level == 'expert':
                recommendations.append("Focus on advanced solutions and technical details")
        
        # Default recommendations
        if not recommendations:
            recommendations = [
                "Monitor user satisfaction trends",
                "Consider proactive outreach for unresolved issues",
                "Provide relevant documentation links"
            ]
        
        return recommendations

    def _suggest_next_actions(self, conversations: List[Dict], context: Dict[str, Any]) -> List[str]:
        """Suggest next best actions"""
        actions = []
        
        if conversations:
            unresolved = [conv for conv in conversations if not conv.get('resolved', False)]
            if unresolved:
                actions.append("Follow up on unresolved issues")
        
        if context.get('urgency_level') == 'high':
            actions.append("Prioritize immediate response")
        
        if context.get('escalation_required'):
            actions.append("Prepare for human handoff")
        
        # Default actions
        if not actions:
            actions = [
                "Provide comprehensive response",
                "Ask for feedback on resolution",
                "Offer additional assistance"
            ]
        
        return actions

    def _analyze_satisfaction_trend(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Analyze user satisfaction trends"""
        if not conversations:
            return {'trend': 'unknown', 'confidence': 0.0}
        
        # Simple satisfaction analysis based on conversation data
        recent_convs = conversations[-5:] if len(conversations) >= 5 else conversations
        satisfaction_scores = []
        
        for conv in recent_convs:
            # Estimate satisfaction based on resolution and feedback
            score = 0.5  # neutral baseline
            if conv.get('resolved', False):
                score += 0.3
            if conv.get('feedback_positive', False):
                score += 0.2
            if conv.get('escalated', False):
                score -= 0.3
                
            satisfaction_scores.append(min(1.0, max(0.0, score)))
        
        avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0.5
        
        if avg_satisfaction > 0.7:
            trend = 'improving'
        elif avg_satisfaction < 0.4:
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'confidence': avg_satisfaction,
            'recent_score': avg_satisfaction
        }

    def _identify_common_issues(self, conversations: List[Dict]) -> List[str]:
        """Identify common issues from conversation history"""
        if not conversations:
            return []
        
        categories = {}
        for conv in conversations:
            category = conv.get('category', 'general')
            categories[category] = categories.get(category, 0) + 1
        
        # Return categories sorted by frequency
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        return [cat[0] for cat in sorted_categories[:5]]

    def _identify_optimizations(self, conversations: List[Dict]) -> List[str]:
        """Identify optimization opportunities"""
        optimizations = []
        
        if not conversations:
            return ["Establish baseline metrics for conversation analysis"]
        
        # Check for patterns that suggest optimization opportunities
        avg_resolution_time = self._calculate_avg_response_time(conversations)
        if avg_resolution_time and avg_resolution_time > 24:  # hours
            optimizations.append("Reduce average resolution time")
        
        escalation_rate = self._calculate_escalation_frequency(conversations)
        if escalation_rate > 0.2:  # 20% escalation rate
            optimizations.append("Improve first-contact resolution")
        
        unresolved_count = sum(1 for conv in conversations if not conv.get('resolved', False))
        if unresolved_count > len(conversations) * 0.1:  # 10% unresolved
            optimizations.append("Focus on closing open issues")
        
        return optimizations or ["Continue monitoring conversation patterns"]

    def _calculate_avg_response_time(self, conversations: List[Dict]) -> Optional[float]:
        """Calculate average response time in hours"""
        response_times = []
        
        for conv in conversations:
            if 'created_at' in conv and 'resolved_at' in conv and conv.get('resolved_at'):
                try:
                    created = datetime.fromisoformat(conv['created_at'])
                    resolved = datetime.fromisoformat(conv['resolved_at'])
                    response_time = (resolved - created).total_seconds() / 3600  # hours
                    response_times.append(response_time)
                except (ValueError, TypeError):
                    continue
        
        return sum(response_times) / len(response_times) if response_times else None

    def _identify_common_topics(self, conversations: List[Dict]) -> List[str]:
        """Identify common topics from conversations"""
        topics = {}
        
        for conv in conversations:
            message = conv.get('message', '').lower()
            keywords = self._extract_keywords(message)
            
            for keyword in keywords:
                topics[keyword] = topics.get(keyword, 0) + 1
        
        # Return top topics
        sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
        return [topic[0] for topic in sorted_topics[:10]]

    def _calculate_resolution_rate(self, conversations: List[Dict]) -> float:
        """Calculate the rate of resolved conversations"""
        if not conversations:
            return 0.0
        
        resolved_count = sum(1 for conv in conversations if conv.get('resolved', False))
        return resolved_count / len(conversations)

    def _calculate_escalation_frequency(self, conversations: List[Dict]) -> float:
        """Calculate how frequently conversations are escalated"""
        if not conversations:
            return 0.0
        
        escalated_count = sum(1 for conv in conversations if conv.get('escalated', False))
        return escalated_count / len(conversations)
