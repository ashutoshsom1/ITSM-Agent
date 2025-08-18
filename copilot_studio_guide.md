# Microsoft Copilot Studio Integration Guide

## What is Copilot Studio?
Microsoft Copilot Studio is a low-code platform that lets you create and deploy bots to Teams without needing App Registrations or complex setup.

## Step 1: Access Copilot Studio
1. Go to [Microsoft Copilot Studio](https://copilotstudio.microsoft.com/)
2. Sign in with your work/school account
3. Create a new bot or copilot

## Step 2: Create a Power Virtual Agent Bot
1. Click "Create" > "New Bot"
2. Name: "ITSM AI Assistant"
3. Choose your environment

## Step 3: Configure Custom API Connection
1. In your bot, go to "Actions" > "Add an action"
2. Choose "Call an HTTP endpoint"
3. Configure:
   - **URL**: `https://your-app-service.azurewebsites.net/api/conversation`
   - **Method**: POST
   - **Headers**: Content-Type: application/json
   - **Body**: 
   ```json
   {
     "user_id": "{System.User.Id}",
     "message": "{System.Activity.Text}",
     "conversation_id": "{System.Conversation.Id}",
     "user_name": "{System.User.DisplayName}"
   }
   ```

## Step 4: Handle the Response
1. Parse the JSON response from your API
2. Display the message to the user
3. Handle any proactive suggestions

## Step 5: Publish to Teams
1. In Copilot Studio, go to "Publish"
2. Choose "Microsoft Teams"
3. Click "Publish"
4. Share the bot with your team

## Benefits:
- ✅ No App Registration needed
- ✅ Easy deployment to Teams
- ✅ Built-in user management
- ✅ Integrated with Microsoft ecosystem

## Sample Bot Flow:
```
User: "I have a server issue"
↓
Bot calls your API: POST /api/conversation
↓
Your FastAPI processes the message
↓
Bot displays the AI response in Teams
```
