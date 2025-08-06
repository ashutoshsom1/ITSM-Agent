"""
Teams integration utilities for Microsoft Copilot Studio
"""
from typing import Dict, Any, Optional, List
from utils.logging import get_logger
from utils.error_handler import AgentError

logger = get_logger("teams_integration")


class TeamsMessage:
    """Represents a Teams message"""
    
    def __init__(
        self,
        text: str,
        user_id: str,
        conversation_id: str,
        channel_id: Optional[str] = None,
        message_id: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        mentions: Optional[List[Dict[str, Any]]] = None
    ):
        self.text = text
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.channel_id = channel_id
        self.message_id = message_id
        self.attachments = attachments or []
        self.mentions = mentions or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "text": self.text,
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "channel_id": self.channel_id,
            "message_id": self.message_id,
            "attachments": self.attachments,
            "mentions": self.mentions
        }
    
    @classmethod
    def from_teams_activity(cls, activity: Dict[str, Any]) -> "TeamsMessage":
        """Create TeamsMessage from Teams activity"""
        return cls(
            text=activity.get("text", ""),
            user_id=activity.get("from", {}).get("id", ""),
            conversation_id=activity.get("conversation", {}).get("id", ""),
            channel_id=activity.get("channelId"),
            message_id=activity.get("id"),
            attachments=activity.get("attachments", []),
            mentions=activity.get("entities", [])
        )


class TeamsResponse:
    """Represents a Teams response"""
    
    def __init__(
        self,
        text: str,
        response_type: str = "message",
        attachments: Optional[List[Dict[str, Any]]] = None,
        suggested_actions: Optional[List[Dict[str, Any]]] = None,
        adaptive_card: Optional[Dict[str, Any]] = None
    ):
        self.text = text
        self.response_type = response_type
        self.attachments = attachments or []
        self.suggested_actions = suggested_actions or []
        self.adaptive_card = adaptive_card
    
    def to_bot_framework_activity(self) -> Dict[str, Any]:
        """Convert to Bot Framework activity format"""
        activity = {
            "type": "message",
            "text": self.text,
            "attachments": self.attachments
        }
        
        if self.suggested_actions:
            activity["suggestedActions"] = {
                "actions": self.suggested_actions
            }
        
        if self.adaptive_card:
            activity["attachments"].append({
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": self.adaptive_card
            })
        
        return activity


def create_adaptive_card(
    title: str,
    subtitle: Optional[str] = None,
    text: Optional[str] = None,
    facts: Optional[List[Dict[str, str]]] = None,
    actions: Optional[List[Dict[str, Any]]] = None,
    image_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create an Adaptive Card for Teams
    
    Args:
        title: Card title
        subtitle: Card subtitle
        text: Card text content
        facts: List of fact name-value pairs
        actions: List of action buttons
        image_url: URL for hero image
        
    Returns:
        Adaptive Card JSON
    """
    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": []
    }
    
    # Add hero image
    if image_url:
        card["body"].append({
            "type": "Image",
            "url": image_url,
            "size": "Large"
        })
    
    # Add title
    if title:
        card["body"].append({
            "type": "TextBlock",
            "text": title,
            "size": "Large",
            "weight": "Bolder"
        })
    
    # Add subtitle
    if subtitle:
        card["body"].append({
            "type": "TextBlock",
            "text": subtitle,
            "size": "Medium",
            "weight": "Bolder",
            "color": "Accent"
        })
    
    # Add text content
    if text:
        card["body"].append({
            "type": "TextBlock",
            "text": text,
            "wrap": True
        })
    
    # Add facts
    if facts:
        card["body"].append({
            "type": "FactSet",
            "facts": facts
        })
    
    # Add actions
    if actions:
        card["actions"] = actions
    
    return card


def create_hero_card(
    title: str,
    subtitle: Optional[str] = None,
    text: Optional[str] = None,
    images: Optional[List[str]] = None,
    buttons: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Create a Hero Card for Teams
    
    Args:
        title: Card title
        subtitle: Card subtitle
        text: Card text
        images: List of image URLs
        buttons: List of button actions
        
    Returns:
        Hero Card JSON
    """
    card = {
        "contentType": "application/vnd.microsoft.card.hero",
        "content": {
            "title": title
        }
    }
    
    if subtitle:
        card["content"]["subtitle"] = subtitle
    
    if text:
        card["content"]["text"] = text
    
    if images:
        card["content"]["images"] = [{"url": img} for img in images]
    
    if buttons:
        card["content"]["buttons"] = buttons
    
    return card


def create_suggested_actions(actions: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Create suggested actions for Teams messages
    
    Args:
        actions: List of actions with 'title' and 'value' keys
        
    Returns:
        List of suggested action objects
    """
    return [
        {
            "type": "imBack",
            "title": action["title"],
            "value": action["value"]
        }
        for action in actions
    ]


def extract_teams_user_info(activity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract user information from Teams activity
    
    Args:
        activity: Teams activity object
        
    Returns:
        Dictionary with user information
    """
    from_info = activity.get("from", {})
    channel_data = activity.get("channelData", {})
    
    return {
        "user_id": from_info.get("id", ""),
        "user_name": from_info.get("name", ""),
        "user_aad_id": from_info.get("aadObjectId", ""),
        "tenant_id": channel_data.get("tenant", {}).get("id", ""),
        "team_id": channel_data.get("team", {}).get("id", ""),
        "channel_id": activity.get("conversation", {}).get("id", ""),
        "conversation_type": activity.get("conversation", {}).get("conversationType", ""),
    }


def format_proactive_message(
    message: str,
    user_name: Optional[str] = None,
    suggestions: Optional[List[str]] = None
) -> TeamsResponse:
    """
    Format a proactive message for Teams
    
    Args:
        message: Main message text
        user_name: User's display name for personalization
        suggestions: List of suggested follow-up actions
        
    Returns:
        TeamsResponse object
    """
    # Personalize message if user name is available
    if user_name:
        greeting = f"Hi {user_name}! "
    else:
        greeting = "Hi there! "
    
    formatted_message = greeting + message
    
    # Create suggested actions if provided
    suggested_actions = []
    if suggestions:
        suggested_actions = create_suggested_actions([
            {"title": suggestion, "value": suggestion}
            for suggestion in suggestions
        ])
    
    return TeamsResponse(
        text=formatted_message,
        suggested_actions=suggested_actions
    )


def format_error_message(error_message: str, show_details: bool = False) -> TeamsResponse:
    """
    Format an error message for Teams
    
    Args:
        error_message: Error message to display
        show_details: Whether to show detailed error information
        
    Returns:
        TeamsResponse object
    """
    if show_details:
        text = f"❌ **Error:** {error_message}"
    else:
        text = "❌ I'm having trouble processing your request. Please try again or contact support if the issue persists."
    
    suggested_actions = create_suggested_actions([
        {"title": "🔄 Try Again", "value": "try again"},
        {"title": "🆘 Get Help", "value": "help"},
        {"title": "👥 Talk to Human", "value": "human"}
    ])
    
    return TeamsResponse(
        text=text,
        suggested_actions=suggested_actions
    )
