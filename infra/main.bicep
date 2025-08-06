targetScope = 'subscription'

@description('Environment name (e.g., dev, test, prod)')
param environmentName string

@description('Location for all resources')
param location string

@description('Resource group name')
param resourceGroupName string

@description('App Service Plan SKU')
@allowed(['F1', 'B1', 'B2', 'S1'])
param appServicePlanSku string = 'F1'

@description('Computer Vision SKU (F0 for free tier)')
@allowed(['F0', 'S1'])
param computerVisionSku string = 'F0'

@description('Text Analytics SKU (F0 for free tier)')
@allowed(['F0', 'S'])
param textAnalyticsSku string = 'F0'

// Variables
var resourceToken = uniqueString(subscription().id, location, environmentName)
var tags = {
  'azd-env-name': environmentName
  Environment: environmentName
  Application: 'ITSM-AI-Agent'
}

// Create Resource Group
resource resourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

// Deploy resources to the resource group
module appResources 'app-resources.bicep' = {
  name: 'app-resources'
  scope: resourceGroup
  params: {
    location: location
    resourceToken: resourceToken
    tags: tags
    appServicePlanSku: appServicePlanSku
    computerVisionSku: computerVisionSku
    textAnalyticsSku: textAnalyticsSku
  }
}

// Outputs
output RESOURCE_GROUP_ID string = resourceGroup.id
output WEB_APP_NAME string = appResources.outputs.webAppName
output WEB_APP_URL string = appResources.outputs.webAppUrl
output AZURE_OPENAI_ENDPOINT string = appResources.outputs.openAiEndpoint
output COSMOS_ENDPOINT string = appResources.outputs.cosmosEndpoint
output COMPUTER_VISION_ENDPOINT string = appResources.outputs.computerVisionEndpoint
output TEXT_ANALYTICS_ENDPOINT string = appResources.outputs.textAnalyticsEndpoint
output STORAGE_ACCOUNT_NAME string = appResources.outputs.storageAccountName
output KEY_VAULT_NAME string = appResources.outputs.keyVaultName
