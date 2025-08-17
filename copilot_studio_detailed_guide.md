# Microsoft Copilot Studio Setup Guide - ITSM AI Assistant

## Overview
This guide will help you create your ITSM AI Assistant bot in Microsoft Copilot Studio and connect it to your FastAPI backend.

## Prerequisites
- ✅ Your FastAPI app is running on Azure App Service
- ✅ You have access to Microsoft Copilot Studio (https://copilotstudio.microsoft.com)
- ✅ You have a work/school Microsoft account

## Step 1: Access Copilot Studio

1. Go to https://copilotstudio.microsoft.com
2. Sign in with your work/school account
3. Select your environment (or create a new one)

## Step 2: Create Your Bot

1. Click **"Create"** in the top menu
2. Select **"New copilot"**
3. Choose **"Conversational"** type
4. Fill in the details:
   - **Name**: ITSM AI Assistant
   - **Description**: AI-powered IT Service Management assistant
   - **Instructions**: You are an intelligent ITSM assistant that helps users with IT support, troubleshooting, and service requests. You can analyze images, provide step-by-step guidance, and escalate to human agents when needed.
   - **Language**: English
5. Click **"Create"**

## Step 3: Configure Your API Connection

### 3A: Create a Custom Action
1. In your bot, go to **"Actions"** tab
2. Click **"+ Add an action"**
3. Choose **"Create a new action"**
4. Name it: **"Call ITSM API"**

### 3B: Set Up the HTTP Request
1. In the action editor, add **"Send an HTTP request"**
2. Configure the request:

**Method**: POST
**URL**: `https://YOUR-APP-SERVICE-NAME.azurewebsites.net/api/copilot-studio`

**Headers**:
```
Content-Type: application/json
```

**Body**:
```json
{
  "message": "{System.Activity.Text}",
  "user_id": "{System.User.Id}",
  "user_name": "{System.User.DisplayName}",
  "conversation_id": "{System.Conversation.Id}"
}
```

**Response parsing**:
- Save response as: `apiResponse`
- Parse as: JSON

## Step 4: Handle the Response

### 4A: Add Response Logic
1. After the HTTP request, add **"Send a message"**
2. In the message field, use: `{apiResponse.response}`

### 4B: Add Suggestions (Optional)
1. Add **"Show choices to user"** action
2. Configure:
   - **Prompt**: "What would you like to do next?"
   - **Choices**: Use `{apiResponse.suggestions}` (if available)

### 4C: Handle Human Handoff
1. Add a **"Condition"** action
2. Check if: `{apiResponse.requires_human}` equals `true`
3. If true:
   - Send message: `{apiResponse.handoff_message}`
   - Transfer to human agent (if configured)

## Step 5: Test Your Bot

1. Click **"Test"** in the top right
2. Try these test messages:
   - "Hello, I need help with a server issue"
   - "My computer is running slowly"
   - "I can't connect to the network"
3. Verify the bot calls your API and returns responses

## Step 6: Publish to Teams

1. Go to **"Channels"** tab
2. Turn on **"Microsoft Teams"**
3. Click **"Publish"**
4. Choose **"Publish to Teams"**
5. Install the bot in your Teams environment

## Step 7: Advanced Features

### Image Analysis Support
To support image uploads:

1. Create another action: **"Analyze Image"**
2. Use endpoint: `/api/analyze-image`
3. Handle file uploads from Teams

### Proactive Notifications
Set up scheduled flows to send proactive messages:

1. Use Power Automate
2. Trigger: Schedule
3. Action: Call your `/api/proactive-insights` endpoint
4. Send results to Teams

## Testing Your Setup

### Basic Conversation Test
```
User: "I have a printer issue"
Expected: Bot calls your API and returns troubleshooting steps
```

### Image Analysis Test
```
User: Uploads screenshot
Expected: Bot analyzes image and provides insights
```

### Human Handoff Test
```
User: "I'm frustrated, I need to talk to someone"
Expected: Bot triggers human handoff workflow
```

## Troubleshooting

### Bot Not Responding
1. Check your App Service is running
2. Verify the API endpoint URL is correct
3. Check App Service logs for errors
4. Test the API directly with Postman

### Authentication Issues
1. Ensure your App Service allows public access
2. Check CORS settings
3. Verify SSL certificate is valid

### Response Format Issues
1. Check your API returns JSON in the expected format
2. Verify response parsing in Copilot Studio
3. Test with simple responses first

## Sample API Response Format

Your `/api/copilot-studio` endpoint should return:

```json
{
  "response": "I can help you with your server issue. Let me analyze the problem...",
  "suggestions": [
    "Check server logs",
    "Run diagnostics", 
    "Contact admin"
  ],
  "requires_human": false,
  "user_insights": {
    "frequent_issues": ["server", "network"],
    "expertise_level": "intermediate"
  }
}
```

## Next Steps After Setup

1. **Customize the bot personality** in Copilot Studio
2. **Add more specialized topics** for common ITSM scenarios
3. **Set up analytics** to track bot usage
4. **Train the bot** with your organization's specific knowledge
5. **Configure human handoff** to your support team

## Support

If you encounter issues:
1. Check the Copilot Studio documentation
2. Test your API endpoints directly
3. Review the bot conversation logs
4. Contact your IT administrator for Teams permissions

Your ITSM AI Assistant is now ready to help your team with intelligent IT support! 🚀
