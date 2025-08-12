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
    """Webhook endpoint for Microsoft Teams integration"""
    try:
        # Process Teams bot messages
        activity_type = payload.get("type")
        
        if activity_type == "message":
            # Handle regular message
            user_id = payload.get("from", {}).get("id")
            message_text = payload.get("text", "")
            conversation_id = payload.get("conversation", {}).get("id")
            
            # Process through main conversation endpoint
            request = ConversationRequest(
                user_id=user_id,
                message=message_text,
                conversation_id=conversation_id,
                user_name=payload.get("from", {}).get("name", "")
            )
            
            response = await process_conversation(request)
            return {"type": "message", "text": response.message}
            
        elif activity_type == "conversationUpdate":
            # Handle bot added to conversation
            return {"type": "message", "text": "Welcome! I'm your AI assistant. How can I help you today?"}
        
        return {"status": "processed"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing Teams webhook: {str(e)}")

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
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
