# ITSM AI Agent 🤖

A comprehensive AI-powered ITSM (IT Service Management) agent with Microsoft Teams and Copilot Studio integration, featuring contextual memory, visual analysis, human handoff capabilities, and proactive intelligence.

## ✨ Features

- 🧠 **Proactive Intelligence**: Suggests solutions based on conversation patterns and adapts responses to user context
- 💭 **Contextual Memory**: Remembers conversations across sessions and learns user preferences
- 👁️ **Visual Problem Solving**: Analyzes screenshots and images with AI
- 🤝 **Seamless Human Handoff**: Intelligent agent matching with full context transfer
- 🎉 **Delightful Experiences**: Celebrates achievements and provides personalized interactions
- 🔗 **Teams Integration**: Native Microsoft Teams bot with Copilot Studio compatibility

## 🏗️ Architecture

### Backend Services (Azure)
- **Azure Functions**: Serverless compute for real-time processing
- **Azure OpenAI**: GPT-4o for advanced AI capabilities
- **Azure Cognitive Services**: Computer Vision, Speech, Language Understanding
- **Azure Cosmos DB**: Global distribution for user context and memory
- **Azure Storage**: File and media processing
- **Azure Application Insights**: Monitoring and analytics
- **Azure Key Vault**: Secure credential management

### Frontend Integration
- **Microsoft Copilot Studio**: Primary bot interface and conversation flow
- **Microsoft Teams**: Native Teams integration
- **Power Platform**: Custom connectors and workflows

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Azure subscription
- Docker (optional, for containerized deployment)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Automate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Copy the environment template and fill in your Azure credentials:
```bash
cp .env.template .env
# Edit .env with your Azure service credentials
```

### 4. Run Locally
```bash
python start.py
```

The API will be available at `http://localhost:8000`

### 5. Deploy to Azure
Using Azure Developer CLI (recommended):
```bash
# Install Azure Developer CLI
# https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd

# Login to Azure
azd auth login

# Initialize and deploy
azd init
azd up
```

## 📡 API Endpoints

### Chat & Conversation
- `POST /api/chat` - Send message to AI agent
- `GET /api/conversations/{conversation_id}` - Get conversation history
- `DELETE /api/conversations/{conversation_id}` - Clear conversation

### Visual Analysis
- `POST /api/analyze-image` - Analyze screenshots or images
- `POST /api/analyze-with-context` - Analyze image with conversation context

### Human Handoff
- `POST /api/handoff/request` - Request human agent
- `GET /api/handoff/status/{ticket_id}` - Check handoff status
- `POST /api/handoff/complete` - Complete handoff session

### Memory & Context
- `GET /api/memory/{user_id}` - Get user memory/preferences
- `POST /api/memory/{user_id}` - Update user memory
- `DELETE /api/memory/{user_id}` - Clear user memory

### Proactive Intelligence
- `GET /api/suggestions/{user_id}` - Get proactive suggestions
- `POST /api/patterns/learn` - Learn from interaction patterns

### Teams Integration
- `POST /api/teams/webhook` - Teams bot webhook
- `GET /api/teams/manifest` - Teams app manifest

### Health & Monitoring
- `GET /health` - Health check endpoint
- `GET /metrics` - Application metrics
- `GET /` - API documentation (Swagger UI)

## 🔧 Configuration

### Environment Variables

#### Required
```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# Azure Cosmos DB
COSMOS_ENDPOINT=https://your-cosmos-account.documents.azure.com:443/
COSMOS_KEY=your-cosmos-key

# Azure Computer Vision
COMPUTER_VISION_ENDPOINT=https://your-vision-resource.cognitiveservices.azure.com/
COMPUTER_VISION_KEY=your-vision-key

# Azure Text Analytics
TEXT_ANALYTICS_ENDPOINT=https://your-textanalytics-resource.cognitiveservices.azure.com/
TEXT_ANALYTICS_KEY=your-textanalytics-key
```

#### Optional
```env
# Storage
STORAGE_CONNECTION_STRING=your-storage-connection-string

# Bot Framework
MICROSOFT_APP_ID=your-bot-app-id
MICROSOFT_APP_PASSWORD=your-bot-app-password

# Teams
TEAMS_APP_ID=your-teams-app-id
TEAMS_TENANT_ID=your-tenant-id
```

## 🤖 Microsoft Copilot Studio Integration

### 1. Create Custom Connector
1. Go to [Power Platform](https://make.powerapps.com/)
2. Navigate to **Data** > **Custom connectors**
3. Create new connector from **OpenAPI definition**
4. Use the API documentation at `/openapi.json`

### 2. Configure Bot Topics
Create topics in Copilot Studio that call your custom connector:

```yaml
# Example topic configuration
Topic: Image Analysis
Trigger: "analyze image", "look at this"
Actions:
  - Call custom connector: analyze-image
  - Display response with adaptive card
```

### 3. Teams App Integration
1. Download the Teams manifest from `/api/teams/manifest`
2. Upload to Teams App Studio
3. Configure webhook URL to your deployed endpoint

## 🐳 Docker Deployment

### Build Image
```bash
docker build -t itsm-ai-agent .
```

### Run Container
```bash
docker run -p 8000:8000 --env-file .env itsm-ai-agent
```

### Docker Compose
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
```

## 📊 Monitoring & Observability

### Application Insights
The application integrates with Azure Application Insights for:
- Request/response tracking
- Performance monitoring
- Error tracking
- Custom telemetry

### Health Checks
- `/health` - Basic health status
- `/health/detailed` - Detailed component health
- `/metrics` - Prometheus-compatible metrics

### Logging
Structured logging with configurable levels:
- File logging to `agent.log`
- Console output
- Azure Application Insights integration

## 🔒 Security

### Authentication
- Azure AD integration for Teams
- API key authentication for external calls
- Managed identity for Azure services

### Data Protection
- All secrets stored in Azure Key Vault
- HTTPS-only communication
- Data encryption at rest and in transit

## 🧪 Testing

### Run Tests
```bash
pytest tests/ -v
```

### Load Testing
```bash
# Install artillery
npm install -g artillery

# Run load test
artillery run tests/load-test.yml
```

## 📈 Performance

### Optimization Features
- Response caching
- Connection pooling
- Async/await throughout
- Efficient database queries
- Image optimization

### Scaling
- Horizontal scaling support
- Stateless design
- External state management (Cosmos DB)
- Container-ready

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linting
flake8 .
black .

# Run type checking
mypy .
```

## 📚 Documentation

- [API Documentation](http://localhost:8000/docs) - Interactive Swagger UI
- [Architecture Guide](docs/architecture.md)
- [Deployment Guide](docs/deployment.md)
- [Teams Integration Guide](docs/teams-integration.md)

## 🆘 Support

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check the docs folder
- **Teams**: Message the bot directly for help

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Microsoft Teams Platform
- Azure Cognitive Services
- OpenAI GPT-4
- FastAPI Framework
- Azure Developer CLI
