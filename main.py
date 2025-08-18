from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
import asyncio
from datetime import datetime, timedelta
import httpx
import base64
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Debug: Check if environment variables are loaded
print("=== Environment Variables Check ===")
print(f"AZURE_OPENAI_ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
print(f"AZURE_OPENAI_KEY: {'***' + os.getenv('AZURE_OPENAI_KEY', '')[-4:] if os.getenv('AZURE_OPENAI_KEY') else 'None'}")
print(f"AZURE_OPENAI_DEPLOYMENT_NAME: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')}")
print("=====================================")

# Import our custom modules
from services.memory_service import MemoryService
from services.openai_service import OpenAIService
from services.vision_service import VisionService
from services.human_handoff_service import HumanHandoffService
from models.conversation_models import ConversationRequest, ConversationResponse, UserProfile
from models.agent_models import AgentCapabilities, ProactiveResponse
from utils.context_analyzer import ContextAnalyzer
from utils.teams_integration import (
    TeamsMessage, TeamsResponse, create_adaptive_card, create_hero_card,
    create_suggested_actions, extract_teams_user_info, format_proactive_message,
    format_error_message
)

app = FastAPI(
    title="AI Agent API",
    description="Comprehensive AI Agent with Teams integration, contextual memory, and visual analysis",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
memory_service = MemoryService()
openai_service = OpenAIService()
vision_service = VisionService()
handoff_service = HumanHandoffService()
context_analyzer = ContextAnalyzer()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Agent API is running", "status": "healthy", "timestamp": datetime.now()}

@app.post("/api/conversation", response_model=ConversationResponse)
async def process_conversation(request: ConversationRequest):
    """
    Main conversation endpoint for processing user messages
    Integrates with Microsoft Copilot and Teams
    """
    try:
        # Get or create user profile
        user_profile = await memory_service.get_user_profile(request.user_id)
        if not user_profile:
            user_profile = await memory_service.create_user_profile(request.user_id, request.user_name)
        
        # Store conversation context
        await memory_service.store_conversation(
            request.user_id, 
            request.message, 
            "user",
            request.conversation_id
        )
        
        # Analyze context for proactive responses
        context_analysis = await context_analyzer.analyze_conversation_context(
            request.user_id, 
            request.message,
            user_profile
        )
        
        # Check if human handoff is needed
        if await _should_trigger_handoff(request.message, context_analysis):
            handoff_response = await handoff_service.initiate_handoff(
                request.user_id,
                request.conversation_id,
                request.message,
                context_analysis
            )
            return ConversationResponse(
                message=handoff_response["message"],
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                requires_handoff=True,
                agent_info=handoff_response.get("agent_info"),
                proactive_suggestions=[]
            )
        
        # Generate AI response
        conversation_history = await memory_service.get_conversation_history(
            request.user_id, 
            request.conversation_id,
            limit=10
        )
        
        ai_response = await openai_service.generate_response(
            request.message,
            conversation_history,
            user_profile,
            context_analysis
        )
        
        # Generate proactive suggestions
        proactive_suggestions = await _generate_proactive_suggestions(
            request.message,
            context_analysis,
            user_profile
        )
        
        # Store AI response
        await memory_service.store_conversation(
            request.user_id,
            ai_response,
            "assistant",
            request.conversation_id
        )
        
        # Update user profile based on interaction
        await memory_service.update_user_preferences(
            request.user_id,
            request.message,
            context_analysis
        )
        
        return ConversationResponse(
            message=ai_response,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            requires_handoff=False,
            proactive_suggestions=proactive_suggestions,
            user_insights=context_analysis.get("user_insights", {})
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing conversation: {str(e)}")

@app.post("/api/analyze-image")
async def analyze_image(
    file: UploadFile = File(...),
    user_id: str = None,
    conversation_id: str = None,
    context: str = None
):
    """
    Visual analysis endpoint for processing screenshots and images
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and process image
        image_data = await file.read()
        
        # Analyze image with Computer Vision
        analysis_result = await vision_service.analyze_image(image_data, context)
        
        # Generate contextual response based on image analysis
        # Always generate AI response, with user context if available
        if user_id:
            user_profile = await memory_service.get_user_profile(user_id)
            conversation_history = await memory_service.get_conversation_history(
                user_id, 
                conversation_id or "image_analysis",
                limit=5
            )
        else:
            # Default profile for anonymous users
            user_profile = {"user_id": "anonymous", "preferences": {}}
            conversation_history = []
        
        # Generate AI response based on image analysis
        ai_response = await openai_service.generate_image_response(
            analysis_result,
            context,
            conversation_history,
            user_profile
        )
        
        # Store interaction only if user_id is provided
        if user_id:
            await memory_service.store_conversation(
                user_id,
                f"[Image Analysis] {context or 'User shared an image'}",
                "user",
                conversation_id or "image_analysis"
            )
            
            await memory_service.store_conversation(
                user_id,
                ai_response,
                "assistant",
                conversation_id or "image_analysis"
            )
        
        return {
            "analysis": analysis_result,
            "ai_response": ai_response,
            "suggestions": analysis_result.get("suggestions", []),
            "detected_issues": analysis_result.get("detected_issues", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing image: {str(e)}")

@app.get("/api/user/{user_id}/profile")
async def get_user_profile(user_id: str):
    """Get user profile and preferences"""
    try:
        profile = await memory_service.get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving profile: {str(e)}")

@app.post("/api/user/{user_id}/profile")
async def update_user_profile(user_id: str, profile_data: Dict[str, Any]):
    """Update user profile and preferences"""
    try:
        updated_profile = await memory_service.update_user_profile(user_id, profile_data)
        return updated_profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating profile: {str(e)}")

@app.get("/api/user/{user_id}/conversations")
async def get_user_conversations(user_id: str, limit: int = 20):
    """Get user's conversation history"""
    try:
        conversations = await memory_service.get_user_conversations(user_id, limit)
        return {"conversations": conversations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving conversations: {str(e)}")

@app.post("/api/human-handoff")
async def request_human_handoff(
    user_id: str,
    conversation_id: str,
    reason: str,
    priority: str = "normal"
):
    """Request human agent handoff"""
    try:
        handoff_result = await handoff_service.initiate_handoff(
            user_id,
            conversation_id,
            reason,
            {"priority": priority}
        )
        return handoff_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initiating handoff: {str(e)}")

@app.get("/api/human-handoff/{handoff_id}/status")
async def get_handoff_status(handoff_id: str):
    """Get status of human handoff request"""
    try:
        status = await handoff_service.get_handoff_status(handoff_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting handoff status: {str(e)}")

@app.post("/api/proactive-insights")
async def get_proactive_insights(user_id: str, context: Dict[str, Any] = None):
    """Generate proactive insights and suggestions for user"""
    try:
        user_profile = await memory_service.get_user_profile(user_id)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Analyze recent activity
        recent_conversations = await memory_service.get_conversation_history(
            user_id, 
            limit=20
        )
        
        # Generate proactive insights
        insights = await context_analyzer.generate_proactive_insights(
            user_profile,
            recent_conversations,
            context
        )
        
        return {
            "insights": insights,
            "recommendations": insights.get("recommendations", []),
            "pattern_analysis": insights.get("patterns", {}),
            "next_best_actions": insights.get("next_actions", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")

@app.post("/api/webhooks/teams")
async def teams_webhook(payload: Dict[str, Any]):
    """Enhanced webhook endpoint for Microsoft Teams integration"""
    try:
        activity_type = payload.get("type")
        
        if activity_type == "message":
            # Extract user information using Teams integration utility
            user_info = extract_teams_user_info(payload)
            
            # Create TeamsMessage object
            teams_message = TeamsMessage.from_teams_activity(payload)
            
            # Process through main conversation endpoint
            request = ConversationRequest(
                user_id=teams_message.user_id,
                message=teams_message.text,
                conversation_id=teams_message.conversation_id,
                user_name=user_info.get("user_name", "")
            )
            
            try:
                response = await process_conversation(request)
                
                # Create enhanced Teams response with suggestions
                suggestions = [item.get("title", "") for item in response.proactive_suggestions[:3]]
                teams_response = format_proactive_message(
                    response.message,
                    user_info.get("user_name"),
                    suggestions
                )
                
                # Check if handoff is required and create appropriate card
                if response.requires_handoff:
                    handoff_card = create_adaptive_card(
                        title="🤝 Connecting you with a human agent",
                        text="I'm transferring your conversation to a human agent who can better assist you.",
                        facts=[
                            {"title": "Request ID", "value": response.conversation_id},
                            {"title": "Status", "value": "In Queue"}
                        ],
                        actions=[
                            {
                                "type": "Action.Submit",
                                "title": "Check Status",
                                "data": {"action": "check_handoff_status"}
                            }
                        ]
                    )
                    teams_response.adaptive_card = handoff_card
                
                return teams_response.to_bot_framework_activity()
                
            except Exception as e:
                # Return formatted error message
                error_response = format_error_message(str(e), show_details=False)
                return error_response.to_bot_framework_activity()
            
        elif activity_type == "conversationUpdate":
            # Enhanced welcome message with capabilities card
            members_added = payload.get("membersAdded", [])
            if any(member.get("id") != payload.get("recipient", {}).get("id") for member in members_added):
                welcome_card = create_adaptive_card(
                    title="👋 Welcome to your AI Assistant!",
                    subtitle="I'm here to help you with your ITSM needs",
                    text="Here's what I can do for you:",
                    facts=[
                        {"title": "💬 Contextual Memory", "value": "I remember our conversations"},
                        {"title": "🖼️ Visual Analysis", "value": "Share screenshots for analysis"},
                        {"title": "🤝 Human Handoff", "value": "Connect with human agents when needed"},
                        {"title": "🧠 Proactive Intelligence", "value": "Smart suggestions based on patterns"}
                    ],
                    actions=[
                        {
                            "type": "Action.Submit",
                            "title": "Get Started",
                            "data": {"action": "get_started"}
                        },
                        {
                            "type": "Action.Submit",
                            "title": "View Capabilities",
                            "data": {"action": "view_capabilities"}
                        }
                    ]
                )
                
                welcome_response = TeamsResponse(
                    text="Welcome! I'm your AI assistant. How can I help you today?",
                    adaptive_card=welcome_card
                )
                
                return welcome_response.to_bot_framework_activity()
        
        elif activity_type == "invoke":
            # Handle adaptive card actions
            action_data = payload.get("value", {})
            action_type = action_data.get("action")
            
            if action_type == "get_started":
                return {"type": "message", "text": "Great! You can ask me questions, share screenshots, or request help with any ITSM-related tasks."}
            elif action_type == "view_capabilities":
                capabilities = await get_agent_capabilities()
                return {"type": "message", "text": f"Here are my capabilities: {json.dumps(capabilities, indent=2)}"}
            elif action_type == "check_handoff_status":
                return {"type": "message", "text": "Your request is being processed by our human agents. You'll be contacted shortly."}
        
        return {"status": "processed"}
        
    except Exception as e:
        error_response = format_error_message(f"Error processing Teams webhook: {str(e)}")
        return error_response.to_bot_framework_activity()

@app.get("/api/capabilities")
async def get_agent_capabilities():
    """Get AI agent capabilities for Microsoft Copilot integration"""
    return {
        "capabilities": [
            {
                "name": "contextual_memory",
                "description": "Remembers conversations across sessions and learns user preferences",
                "enabled": True
            },
            {
                "name": "visual_analysis",
                "description": "Analyzes screenshots and images with AI-powered insights",
                "enabled": True
            },
            {
                "name": "human_handoff",
                "description": "Seamless transfer to human agents with full context",
                "enabled": True
            },
            {
                "name": "proactive_intelligence",
                "description": "Suggests solutions based on conversation patterns",
                "enabled": True
            },
            {
                "name": "multi_modal",
                "description": "Supports text, images, and voice interactions",
                "enabled": True
            }
        ],
        "supported_formats": ["text", "image", "json"],
        "max_conversation_history": 50,
        "response_time_sla": "< 2 seconds"
    }

@app.post("/api/teams/send-proactive-message")
async def send_proactive_teams_message(
    user_id: str,
    message: str,
    conversation_id: str,
    message_type: str = "info"
):
    """Send a proactive message to Teams user"""
    try:
        # Get user profile for personalization
        user_profile = await memory_service.get_user_profile(user_id)
        user_name = user_profile.get("user_name") if user_profile else None
        
        # Create appropriate message based on type
        if message_type == "alert":
            card = create_adaptive_card(
                title="🚨 Alert",
                text=message,
                actions=[
                    {
                        "type": "Action.Submit",
                        "title": "Acknowledge",
                        "data": {"action": "acknowledge_alert"}
                    },
                    {
                        "type": "Action.Submit", 
                        "title": "Get Help",
                        "data": {"action": "get_help"}
                    }
                ]
            )
            teams_response = TeamsResponse(text=message, adaptive_card=card)
        elif message_type == "reminder":
            suggestions = ["Snooze 15 min", "Mark Complete", "View Details"]
            teams_response = format_proactive_message(message, user_name, suggestions)
        else:
            teams_response = format_proactive_message(message, user_name)
        
        # In a real implementation, you would send this via Bot Framework
        # For now, we'll return the formatted message
        return {
            "status": "sent",
            "message": teams_response.to_bot_framework_activity(),
            "user_id": user_id,
            "conversation_id": conversation_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending proactive message: {str(e)}")

@app.post("/api/teams/create-card")
async def create_teams_card(
    card_type: str,
    title: str,
    content: Dict[str, Any]
):
    """Create various types of Teams cards"""
    try:
        if card_type == "adaptive":
            card = create_adaptive_card(
                title=title,
                subtitle=content.get("subtitle"),
                text=content.get("text"),
                facts=content.get("facts"),
                actions=content.get("actions"),
                image_url=content.get("image_url")
            )
        elif card_type == "hero":
            card = create_hero_card(
                title=title,
                subtitle=content.get("subtitle"),
                text=content.get("text"),
                images=content.get("images"),
                buttons=content.get("buttons")
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported card type: {card_type}")
        
        return {
            "card_type": card_type,
            "card": card
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating card: {str(e)}")

@app.post("/api/copilot-studio")
async def copilot_studio_endpoint(request: Dict[str, Any]):
    """
    Simplified endpoint for Microsoft Copilot Studio integration
    Expected input format from Copilot Studio:
    {
        "message": "user message",
        "user_id": "user123",
        "user_name": "John Doe",
        "conversation_id": "conv123"
    }
    """
    try:
        # Extract data from Copilot Studio request
        message = request.get("message", "")
        user_id = request.get("user_id", "copilot_user")
        user_name = request.get("user_name", "User")
        conversation_id = request.get("conversation_id", "copilot_conv")
        
        if not message:
            return {
                "response": "I didn't receive a message. Please try again.",
                "suggestions": ["Try asking a question", "Upload an image", "Request help"]
            }
        
        # Create conversation request
        conv_request = ConversationRequest(
            user_id=user_id,
            message=message,
            conversation_id=conversation_id,
            user_name=user_name
        )
        
        # Process through main conversation logic
        response = await process_conversation(conv_request)
        
        # Format response for Copilot Studio
        copilot_response = {
            "response": response.message,
            "suggestions": [item.get("title", "") for item in response.proactive_suggestions[:3]],
            "requires_human": response.requires_handoff,
            "user_insights": response.user_insights if hasattr(response, 'user_insights') else {}
        }
        
        # Add special handling for handoff
        if response.requires_handoff:
            copilot_response["handoff_message"] = "I'm connecting you with a human agent who can better assist you."
            copilot_response["suggestions"] = ["Wait for agent", "Provide more details", "Check status"]
        
        return copilot_response
        
    except Exception as e:
        return {
            "response": f"I'm having trouble processing your request. Please try again or contact support.",
            "suggestions": ["Try again", "Simplify your question", "Contact IT support"],
            "error": str(e) if app.debug else None
        }

# Helper functions
async def _should_trigger_handoff(message: str, context_analysis: Dict) -> bool:
    """Determine if human handoff should be triggered"""
    handoff_triggers = [
        "human", "agent", "person", "talk to someone",
        "escalate", "complaint", "angry", "frustrated"
    ]
    
    message_lower = message.lower()
    has_trigger_word = any(trigger in message_lower for trigger in handoff_triggers)
    
    # Check sentiment analysis
    sentiment_score = context_analysis.get("sentiment", {}).get("score", 0)
    high_negative_sentiment = sentiment_score < -0.7
    
    # Check complexity score
    complexity_score = context_analysis.get("complexity", 0)
    high_complexity = complexity_score > 0.8
    
    return has_trigger_word or high_negative_sentiment or high_complexity

async def _generate_proactive_suggestions(
    message: str, 
    context_analysis: Dict, 
    user_profile: Dict
) -> List[Dict]:
    """Generate proactive suggestions based on context"""
    suggestions = []
    
    # Pattern-based suggestions
    if "error" in message.lower() or "problem" in message.lower():
        suggestions.append({
            "type": "troubleshooting",
            "title": "Would you like me to analyze this issue step by step?",
            "action": "start_guided_troubleshooting"
        })
    
    if "screenshot" in message.lower() or "image" in message.lower():
        suggestions.append({
            "type": "visual_help",
            "title": "You can share a screenshot and I'll analyze it for you",
            "action": "upload_image"
        })
    
    # User history-based suggestions
    common_topics = user_profile.get("common_topics", [])
    if common_topics:
        suggestions.append({
            "type": "related_topic",
            "title": f"Based on your interests in {common_topics[0]}, you might also like...",
            "action": "explore_related_topics"
        })
    
    return suggestions

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,port=8000)
