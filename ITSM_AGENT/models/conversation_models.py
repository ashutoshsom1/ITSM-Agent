from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ConversationRequest(BaseModel):
    """Request model for conversation endpoint"""
    user_id: str = Field(..., description="Unique identifier for the user")
    message: str = Field(..., description="User's message content")
    conversation_id: Optional[str] = Field(None, description="Conversation thread identifier")
    user_name: Optional[str] = Field(None, description="User's display name")
    channel: Optional[str] = Field("api", description="Channel source (teams, api, copilot)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context metadata")

class ConversationResponse(BaseModel):
    """Response model for conversation endpoint"""
    message: str = Field(..., description="AI assistant's response")
    user_id: str = Field(..., description="User identifier")
    conversation_id: str = Field(..., description="Conversation thread identifier")
    requires_handoff: bool = Field(False, description="Whether human handoff is recommended")
    agent_info: Optional[Dict[str, Any]] = Field(None, description="Human agent information if handoff initiated")
    proactive_suggestions: List[Dict[str, Any]] = Field([], description="Proactive suggestions for the user")
    user_insights: Optional[Dict[str, Any]] = Field(None, description="Insights about user preferences and patterns")
    confidence_score: Optional[float] = Field(None, description="Confidence in the response quality")
    response_time_ms: Optional[int] = Field(None, description="Response generation time in milliseconds")

class UserProfile(BaseModel):
    """User profile model"""
    user_id: str = Field(..., description="Unique user identifier")
    user_name: Optional[str] = Field(None, description="User's display name")
    created_at: datetime = Field(default_factory=datetime.now, description="Profile creation timestamp")
    last_interaction: datetime = Field(default_factory=datetime.now, description="Last interaction timestamp")
    interaction_count: int = Field(0, description="Total number of interactions")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences and settings")
    common_topics: List[str] = Field([], description="Topics the user frequently discusses")
    conversation_patterns: Dict[str, Any] = Field(default_factory=dict, description="Conversation behavior patterns")
    sentiment_history: List[Dict[str, Any]] = Field([], description="Historical sentiment analysis")

class MessageHistory(BaseModel):
    """Individual message in conversation history"""
    message_id: str = Field(..., description="Unique message identifier")
    user_id: str = Field(..., description="User identifier")
    conversation_id: str = Field(..., description="Conversation thread identifier")
    message: str = Field(..., description="Message content")
    role: str = Field(..., description="Message role (user/assistant)")
    timestamp: datetime = Field(..., description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional message metadata")

class ConversationSummary(BaseModel):
    """Summary of a conversation thread"""
    conversation_id: str = Field(..., description="Conversation identifier")
    user_id: str = Field(..., description="User identifier")
    started_at: datetime = Field(..., description="Conversation start time")
    last_message_at: datetime = Field(..., description="Last message timestamp")
    message_count: int = Field(..., description="Total messages in conversation")
    topics: List[str] = Field([], description="Main topics discussed")
    sentiment_score: Optional[float] = Field(None, description="Overall conversation sentiment")
    resolution_status: Optional[str] = Field(None, description="Whether issue was resolved")

class ContextAnalysis(BaseModel):
    """Context analysis result"""
    sentiment: Dict[str, float] = Field(default_factory=dict, description="Sentiment analysis results")
    topics: List[str] = Field([], description="Identified topics")
    complexity: float = Field(0.0, description="Complexity score (0-1)")
    urgency: float = Field(0.0, description="Urgency score (0-1)")
    user_intent: Optional[str] = Field(None, description="Detected user intent")
    entities: List[Dict[str, Any]] = Field([], description="Named entities found")
    confidence: float = Field(0.0, description="Overall analysis confidence")
