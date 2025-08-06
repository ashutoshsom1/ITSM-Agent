# PowerShell deployment script for ITSM AI Agent
Write-Host "🚀 Deploying ITSM AI Agent to Azure..." -ForegroundColor Green
Write-Host "💰 Using cost-optimized configuration for free subscription" -ForegroundColor Yellow

# Check if azd is authenticated
Write-Host "🔐 Checking Azure authentication..." -ForegroundColor Cyan
$authCheck = azd auth status 2>&1
if ($authCheck -like "*Not logged in*" -or $authCheck -like "*error*") {
    Write-Host "⚠️  Not authenticated. Please login to Azure..." -ForegroundColor Yellow
    azd auth login
}

# Set environment variables for deployment
$env:AZURE_ENV_NAME = "itsm-agent-dev"
$env:AZURE_LOCATION = "eastus"

Write-Host "📋 Environment Configuration:" -ForegroundColor Cyan
Write-Host "   Environment: $env:AZURE_ENV_NAME"
Write-Host "   Location: $env:AZURE_LOCATION"
Write-Host "   Subscription: b9ebc70b-3ef0-43f7-b2bc-160b91db4cd9"

# Deploy infrastructure
Write-Host "🏗️  Deploying Azure infrastructure..." -ForegroundColor Green
Write-Host "   This will create:" -ForegroundColor White
Write-Host "   ✅ Resource Group" -ForegroundColor Green
Write-Host "   ✅ App Service (Free F1 tier)" -ForegroundColor Green
Write-Host "   ✅ Cosmos DB (Free tier with 1000 RU/s)" -ForegroundColor Green
Write-Host "   ✅ Computer Vision (Free F0 tier)" -ForegroundColor Green
Write-Host "   ✅ Text Analytics (Free F0 tier)" -ForegroundColor Green
Write-Host "   ✅ Storage Account (Standard LRS)" -ForegroundColor Green
Write-Host "   ✅ Key Vault" -ForegroundColor Green
Write-Host "   ✅ Application Insights" -ForegroundColor Green
Write-Host ""

# Start deployment
try {
    azd up --environment itsm-agent-dev
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📊 Getting deployment outputs..." -ForegroundColor Cyan
        
        # Get outputs
        $outputs = azd env get-values --environment itsm-agent-dev
        
        Write-Host "🔗 Your ITSM AI Agent Resources:" -ForegroundColor Green
        Write-Host "=================================" -ForegroundColor Green
        
        # Parse and display key outputs
        $outputs | ForEach-Object {
            if ($_ -like "WEB_APP_URL=*") {
                $url = $_.Split('=')[1]
                Write-Host "🌐 Web App URL: $url" -ForegroundColor Cyan
            }
            elseif ($_ -like "WEB_APP_NAME=*") {
                $name = $_.Split('=')[1]
                Write-Host "📱 Web App Name: $name" -ForegroundColor Cyan
            }
        }
        
        Write-Host ""
        Write-Host "🎯 Next Steps:" -ForegroundColor Yellow
        Write-Host "1. Update your .env file with the Azure resource endpoints"
        Write-Host "2. Deploy your Python application code"
        Write-Host "3. Configure Microsoft Copilot Studio integration"
        Write-Host ""
        Write-Host "💡 To update .env file, run: .\update-env.ps1" -ForegroundColor Green
        
    } else {
        Write-Host "❌ Deployment failed. Check the error messages above." -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Deployment error: $_" -ForegroundColor Red
}
