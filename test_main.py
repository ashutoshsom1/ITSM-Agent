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
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


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


@patch('services.openai_service.OpenAIService')
@patch('services.memory_service.MemoryService')
def test_chat_endpoint(mock_memory, mock_openai):
    """Test the chat endpoint"""
    # Mock the services
    mock_openai_instance = AsyncMock()
    mock_openai_instance.generate_response.return_value = {
        "message": "Hello! How can I help you today?",
        "response_type": "message",
        "suggestions": ["Tell me about tickets", "Help with login"]
    }
    mock_openai.return_value = mock_openai_instance
    
    mock_memory_instance = AsyncMock()
    mock_memory_instance.get_conversation_history.return_value = []
    mock_memory_instance.save_message.return_value = None
    mock_memory.return_value = mock_memory_instance
    
    # Test chat request
    test_payload = {
        "message": "Hello",
        "user_id": "test-user-123",
        "conversation_id": "test-conv-123"
    }
    
    response = client.post("/api/chat", json=test_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "conversation_id" in data
    assert "timestamp" in data


def test_chat_endpoint_missing_fields():
    """Test chat endpoint with missing required fields"""
    # Missing user_id
    test_payload = {
        "message": "Hello",
        "conversation_id": "test-conv-123"
    }
    
    response = client.post("/api/chat", json=test_payload)
    assert response.status_code == 422  # Validation error


@patch('services.vision_service.VisionService')
def test_analyze_image_endpoint(mock_vision):
    """Test the image analysis endpoint"""
    # Mock the vision service
    mock_vision_instance = AsyncMock()
    mock_vision_instance.analyze_image.return_value = {
        "description": "A screenshot of a login error",
        "text_content": "Error: Invalid username or password",
        "detected_issues": ["Authentication error"],
        "suggestions": ["Check credentials", "Reset password"]
    }
    mock_vision.return_value = mock_vision_instance
    
    # Create a simple test image (1x1 pixel PNG)
    test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
    
    response = client.post(
        "/api/analyze-image",
        files={"image": ("test.png", test_image_data, "image/png")},
        data={"user_id": "test-user-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "description" in data
    assert "suggestions" in data


def test_analyze_image_no_file():
    """Test image analysis endpoint without file"""
    response = client.post(
        "/api/analyze-image",
        data={"user_id": "test-user-123"}
    )
    
    assert response.status_code == 422  # Validation error


@patch('services.human_handoff_service.HumanHandoffService')
def test_handoff_request_endpoint(mock_handoff):
    """Test the human handoff request endpoint"""
    # Mock the handoff service
    mock_handoff_instance = AsyncMock()
    mock_handoff_instance.request_human_agent.return_value = {
        "ticket_id": "TICKET-123",
        "status": "queued",
        "estimated_wait_time": 300,
        "queue_position": 1
    }
    mock_handoff.return_value = mock_handoff_instance
    
    test_payload = {
        "user_id": "test-user-123",
        "conversation_id": "test-conv-123",
        "reason": "Need technical help",
        "priority": "medium"
    }
    
    response = client.post("/api/handoff/request", json=test_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "ticket_id" in data
    assert "status" in data


def test_teams_manifest_endpoint():
    """Test the Teams manifest endpoint"""
    response = client.get("/api/teams/manifest")
    assert response.status_code == 200
    
    data = response.json()
    assert "$schema" in data
    assert "manifestVersion" in data
    assert "name" in data
    assert "bots" in data


if __name__ == "__main__":
    pytest.main([__file__])
