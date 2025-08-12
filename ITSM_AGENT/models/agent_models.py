from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class AgentCapabilityType(str, Enum):
    """Types of agent capabilities"""
    CONTEXTUAL_MEMORY = "contextual_memory"
    VISUAL_ANALYSIS = "visual_analysis"
    HUMAN_HANDOFF = "human_handoff"
    PROACTIVE_INTELLIGENCE = "proactive_intelligence"
    MULTI_MODAL = "multi_modal"
    WORKFLOW_AUTOMATION = "workflow_automation"

class AgentCapability(BaseModel):
    """Individual agent capability"""
    name: AgentCapabilityType = Field(..., description="Capability type")
    description: str = Field(..., description="Human-readable description")
    enabled: bool = Field(True, description="Whether capability is currently enabled")
    confidence_level: float = Field(1.0, description="Confidence in capability (0-1)")
    last_used: Optional[datetime] = Field(None, description="When capability was last used")
    usage_count: int = Field(0, description="Number of times capability has been used")

class AgentCapabilities(BaseModel):
    """Complete set of agent capabilities"""
    capabilities: List[AgentCapability] = Field(..., description="List of available capabilities")
    supported_formats: List[str] = Field(["text", "image", "json"], description="Supported input/output formats")
    max_conversation_history: int = Field(50, description="Maximum conversation history retained")
    response_time_sla: str = Field("< 2 seconds", description="Response time service level agreement")
    availability: float = Field(0.99, description="Service availability percentage")

class ProactiveResponseType(str, Enum):
    """Types of proactive responses"""
    SUGGESTION = "suggestion"
    WARNING = "warning"
    CELEBRATION = "celebration"
    WORKFLOW = "workflow"
    RESOURCE = "resource"
    TROUBLESHOOTING = "troubleshooting"

class ProactiveResponse(BaseModel):
    """Proactive response or suggestion"""
    type: ProactiveResponseType = Field(..., description="Type of proactive response")
    title: str = Field(..., description="Response title")
    description: str = Field(..., description="Detailed description")
    priority: str = Field("medium", description="Priority level (low/medium/high)")
    actionable: bool = Field(True, description="Whether response includes actionable items")
    actions: List[str] = Field([], description="Suggested actions user can take")
    confidence: float = Field(0.8, description="Confidence in suggestion relevance")
    triggers: List[str] = Field([], description="What triggered this response")
    expires_at: Optional[datetime] = Field(None, description="When suggestion expires")

class UserInsight(BaseModel):
    """Insight about user behavior or preferences"""
    insight_type: str = Field(..., description="Type of insight")
    description: str = Field(..., description="Human-readable insight description")
    confidence: float = Field(..., description="Confidence in insight accuracy")
    data_points: int = Field(..., description="Number of data points supporting insight")
    actionable_recommendations: List[str] = Field([], description="Recommendations based on insight")
    created_at: datetime = Field(default_factory=datetime.now, description="When insight was generated")

class PatternAnalysis(BaseModel):
    """Analysis of user interaction patterns"""
    pattern_type: str = Field(..., description="Type of pattern identified")
    frequency: float = Field(..., description="How often pattern occurs")
    strength: float = Field(..., description="Strength of pattern (0-1)")
    examples: List[str] = Field([], description="Examples of pattern occurrence")
    implications: List[str] = Field([], description="What this pattern suggests")
    recommendations: List[str] = Field([], description="Recommendations based on pattern")

class AgentPersonality(BaseModel):
    """Agent personality configuration"""
    communication_style: str = Field("friendly", description="Primary communication style")
    formality_level: str = Field("casual", description="Level of formality")
    enthusiasm_level: float = Field(0.7, description="Enthusiasm level (0-1)")
    empathy_level: float = Field(0.8, description="Empathy level (0-1)")
    technical_depth: str = Field("adaptive", description="Technical explanation depth")
    humor_enabled: bool = Field(True, description="Whether to use appropriate humor")
    celebration_enabled: bool = Field(True, description="Whether to celebrate user achievements")

class InteractionContext(BaseModel):
    """Context for current interaction"""
    session_id: Optional[str] = Field(None, description="Current session identifier")
    platform: str = Field("api", description="Platform/channel of interaction")
    user_timezone: Optional[str] = Field(None, description="User's timezone")
    user_language: str = Field("en", description="User's preferred language")
    accessibility_needs: List[str] = Field([], description="User's accessibility requirements")
    device_type: Optional[str] = Field(None, description="Type of device user is using")
    interaction_history_length: int = Field(0, description="Length of interaction history")

class AgentResponse(BaseModel):
    """Complete agent response structure"""
    content: str = Field(..., description="Main response content")
    capabilities_used: List[AgentCapabilityType] = Field([], description="Capabilities used in this response")
    proactive_responses: List[ProactiveResponse] = Field([], description="Proactive suggestions")
    user_insights: List[UserInsight] = Field([], description="New insights about user")
    confidence_score: float = Field(0.8, description="Confidence in response quality")
    processing_time_ms: int = Field(0, description="Time taken to generate response")
    next_best_actions: List[str] = Field([], description="Suggested next actions for user")
    
class AgentMetrics(BaseModel):
    """Agent performance metrics"""
    total_interactions: int = Field(0, description="Total number of interactions")
    successful_resolutions: int = Field(0, description="Number of successful issue resolutions")
    human_handoffs: int = Field(0, description="Number of handoffs to humans")
    average_response_time: float = Field(0.0, description="Average response time in seconds")
    user_satisfaction_score: float = Field(0.0, description="Average user satisfaction")
    capability_usage: Dict[str, int] = Field(default_factory=dict, description="Usage count per capability")
    error_rate: float = Field(0.0, description="Rate of errors or failed responses")
    uptime_percentage: float = Field(100.0, description="Service uptime percentage")
