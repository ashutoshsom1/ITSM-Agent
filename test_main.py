"""
Basic tests for the ITSM AI Agent API
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

# Import the FastAPI app
from main import app

# Create test client
client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint"""
    response = client.get("/")  # Changed from "/health" to "/"
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "message" in data  # Changed from "version" to "message"


def test_root_endpoint():
    """Test the root endpoint redirects to docs"""
    response = client.get("/")
    assert response.status_code == 200


def test_openapi_schema():
    """Test that OpenAPI schema is accessible"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data


@patch('main.memory_service')
@patch('main.openai_service')
@patch('main.context_analyzer')
def test_chat_endpoint(mock_context_analyzer, mock_openai, mock_memory):
    """Test the chat endpoint"""
    # Mock the services with proper async returns
    async def mock_get_user_profile(*args):
        return {
            "user_id": "test-user-123",
            "preferences": {},
            "common_topics": []
        }
    
    async def mock_create_user_profile(*args):
        return {
            "user_id": "test-user-123",
            "preferences": {},
            "common_topics": []
        }
    
    async def mock_store_conversation(*args):
        return None
    
    async def mock_get_conversation_history(*args, **kwargs):
        return []
    
    async def mock_update_user_preferences(*args):
        return None
    
    async def mock_analyze_conversation_context(*args):
        return {
            "sentiment": {"score": 0.5},
            "complexity": 0.3,
            "user_insights": {}
        }
    
    async def mock_generate_response(*args):
        return "Hello! How can I help you today?"
    
    # Apply the async mocks
    mock_memory.get_user_profile = mock_get_user_profile
    mock_memory.create_user_profile = mock_create_user_profile
    mock_memory.store_conversation = mock_store_conversation
    mock_memory.get_conversation_history = mock_get_conversation_history
    mock_memory.update_user_preferences = mock_update_user_preferences
    mock_context_analyzer.analyze_conversation_context = mock_analyze_conversation_context
    mock_openai.generate_response = mock_generate_response
    
    # Test chat request
    test_payload = {
        "message": "Hello",
        "user_id": "test-user-123",
        "conversation_id": "test-conv-123"
    }
    
    response = client.post("/api/conversation", json=test_payload)
    if response.status_code != 200:
        print(f"Response error: {response.status_code}")
        print(f"Response text: {response.text}")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "conversation_id" in data
    assert "user_id" in data


def test_chat_endpoint_missing_fields():
    """Test chat endpoint with missing required fields"""
    # Missing user_id
    test_payload = {
        "message": "Hello",
        "conversation_id": "test-conv-123"
    }
    
    response = client.post("/api/conversation", json=test_payload)  # Changed from "/api/chat" to "/api/conversation"
    assert response.status_code == 422  # Validation error


@patch('main.memory_service')
@patch('main.openai_service')
@patch('main.vision_service')
def test_analyze_image_endpoint(mock_vision, mock_openai, mock_memory):
    """Test the image analysis endpoint"""
    # Mock the vision service to return the actual structure
    async def mock_analyze_image(*args):
        return {
            "analysis": {
                "analysis_type": "fallback",
                "categories": ["general"],
                "color_info": {
                    "dominant_colors": ["Color analysis available"],
                    "is_bw": False
                },
                "confidence": 0.5
            },
            "detected_issues": ["Low resolution image"],
            "suggestions": ["Try taking a higher resolution screenshot or photo"]
        }
    
    async def mock_get_user_profile(*args):
        return {"user_id": "test-user-123", "preferences": {}}
    
    async def mock_get_conversation_history(*args, **kwargs):
        return []
    
    async def mock_generate_image_response(*args):
        return "I can see this is a low resolution image..."
    
    async def mock_store_conversation(*args):
        return None
    
    mock_vision.analyze_image = mock_analyze_image
    mock_memory.get_user_profile = mock_get_user_profile
    mock_memory.get_conversation_history = mock_get_conversation_history
    mock_memory.store_conversation = mock_store_conversation
    mock_openai.generate_image_response = mock_generate_image_response
    
    # Create a simple test image (1x1 pixel PNG)
    test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
    
    response = client.post(
        "/api/analyze-image",
        files={"file": ("test.png", test_image_data, "image/png")},
        data={"user_id": "test-user-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data
    assert "suggestions" in data
    assert "detected_issues" in data
def test_analyze_image_no_file():
    """Test image analysis endpoint without file"""
    response = client.post(
        "/api/analyze-image",
        data={"user_id": "test-user-123"}
    )
    
    assert response.status_code == 422  # Validation error


@patch('main.handoff_service')
def test_handoff_request_endpoint(mock_handoff):
    """Test the human handoff request endpoint"""
    # Mock the handoff service to return the actual structure
    async def mock_initiate_handoff(*args):
        return {
            "handoff_id": "2bfa7109-b140-4c1e-8565-ad8469ba7dd9",
            "status": "assigned",
            "message": "I'm connecting you with Sarah Johnson, who specializes in technical_support, troubleshooting. They'll be with you shortly!",
            "agent_info": {
                "name": "Sarah Johnson",
                "specializations": ["technical_support", "troubleshooting"],
                "rating": 4.8,
                "estimated_response_time": "1-2 minutes"
            },
            "estimated_wait_time": 2,
            "handoff_type": "immediate"
        }
    
    mock_handoff.initiate_handoff = mock_initiate_handoff
    
    test_payload = {
        "user_id": "test-user-123",
        "conversation_id": "test-conv-123",
        "reason": "Need technical help",
        "priority": "medium"
    }
    
    response = client.post("/api/human-handoff", params=test_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "handoff_id" in data  # Changed from "ticket_id" to "handoff_id"
    assert "status" in data
    assert "agent_info" in data


def test_capabilities_endpoint():
    """Test the capabilities endpoint"""
    response = client.get("/api/capabilities")
    assert response.status_code == 200
    
    data = response.json()
    assert "capabilities" in data  # Changed from "$schema" to "capabilities"
    assert "supported_formats" in data
    assert "max_conversation_history" in data
    assert "response_time_sla" in data


if __name__ == "__main__":
    pytest.main([__file__])
