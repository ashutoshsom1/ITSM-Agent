@description('Application resources for ITSM AI Agent')

// Parameters
param location string
param resourceToken string
param tags object
param appServicePlanSku string
param computerVisionSku string
param textAnalyticsSku string

// Resource names
var appServicePlanName = 'asp-itsm-${resourceToken}'
var webAppName = 'app-itsm-${resourceToken}'
var cosmosAccountName = 'cosmos-itsm-${resourceToken}'
var storageAccountName = 'st${replace(resourceToken, '-', '')}${uniqueString(resourceToken)}'
var computerVisionName = 'cv-itsm-${resourceToken}'
var textAnalyticsName = 'ta-itsm-${resourceToken}'
var keyVaultName = 'kv-itsm-${resourceToken}'
var appInsightsName = 'ai-itsm-${resourceToken}'
var logAnalyticsName = 'log-itsm-${resourceToken}'
var managedIdentityName = 'id-itsm-${resourceToken}'

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

// User-assigned Managed Identity
resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: managedIdentityName
  location: location
  tags: tags
}

// App Service Plan (Free tier for cost optimization)
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  tags: tags
  sku: {
    name: appServicePlanSku
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

// Web App
resource webApp 'Microsoft.Web/sites@2023-01-01' = {
  name: webAppName
  location: location
  tags: union(tags, {
    'azd-service-name': 'api'
  })
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      alwaysOn: appServicePlanSku != 'F1' // F1 doesn't support always on
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      cors: {
        allowedOrigins: ['*']
        supportCredentials: false
      }
      appSettings: [
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
      ]
    }
    httpsOnly: true
  }
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
}

// Web App Site Extension
resource siteExtension 'Microsoft.Web/sites/siteextensions@2023-01-01' = {
  parent: webApp
  name: 'python311x64'
}

// Diagnostic settings for Web App
resource webAppDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'webAppDiagnostics'
  scope: webApp
  properties: {
    workspaceId: logAnalytics.id
    logs: [
      {
        category: 'AppServiceHTTPLogs'
        enabled: true
      }
      {
        category: 'AppServiceConsoleLogs'
        enabled: true
      }
      {
        category: 'AppServiceAppLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

// Cosmos DB Account (Free tier)
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: cosmosAccountName
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
      }
    ]
    databaseAccountOfferType: 'Standard'
    enableAutomaticFailover: false
    enableMultipleWriteLocations: false
    enableFreeTier: true // Free tier
    publicNetworkAccess: 'Enabled'
  }
}

// Cosmos DB Database
resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  parent: cosmosAccount
  name: 'itsm_agent'
  properties: {
    resource: {
      id: 'itsm_agent'
    }
    options: {
      throughput: 400 // Minimum throughput
    }
  }
}

// Cosmos DB Containers
resource conversationsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'conversations'
  properties: {
    resource: {
      id: 'conversations'
      partitionKey: {
        paths: ['/user_id']
        kind: 'Hash'
      }
      defaultTtl: 604800 // 7 days
    }
  }
}

resource usersContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'users'
  properties: {
    resource: {
      id: 'users'
      partitionKey: {
        paths: ['/user_id']
        kind: 'Hash'
      }
    }
  }
}

resource agentsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'agents'
  properties: {
    resource: {
      id: 'agents'
      partitionKey: {
        paths: ['/agent_id']
        kind: 'Hash'
      }
    }
  }
}

resource ticketsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'tickets'
  properties: {
    resource: {
      id: 'tickets'
      partitionKey: {
        paths: ['/user_id']
        kind: 'Hash'
      }
    }
  }
}

// Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

// Blob Container
resource blobContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: '${storageAccount.name}/default/agent-files'
  properties: {
    publicAccess: 'None'
  }
}

// Computer Vision (Free tier)
resource computerVision 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: computerVisionName
  location: location
  tags: tags
  sku: {
    name: computerVisionSku
  }
  kind: 'ComputerVision'
  properties: {
    customSubDomainName: computerVisionName
    publicNetworkAccess: 'Enabled'
  }
}

// Text Analytics (Free tier)
resource textAnalytics 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: textAnalyticsName
  location: location
  tags: tags
  sku: {
    name: textAnalyticsSku
  }
  kind: 'TextAnalytics'
  properties: {
    customSubDomainName: textAnalyticsName
    publicNetworkAccess: 'Enabled'
  }
}

// Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    accessPolicies: [
      {
        tenantId: subscription().tenantId
        objectId: managedIdentity.properties.principalId
        permissions: {
          secrets: ['get', 'list']
        }
      }
    ]
    enabledForTemplateDeployment: false
    enabledForDiskEncryption: false
    enabledForDeployment: false
    enableRbacAuthorization: false
  }
}

// Key Vault Secrets
resource cosmosKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'COSMOS-KEY'
  properties: {
    value: cosmosAccount.listKeys().primaryMasterKey
  }
}

resource computerVisionKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'COMPUTER-VISION-KEY'
  properties: {
    value: computerVision.listKeys().key1
  }
}

resource textAnalyticsKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'TEXT-ANALYTICS-KEY'
  properties: {
    value: textAnalytics.listKeys().key1
  }
}

resource storageKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'STORAGE-CONNECTION-STRING'
  properties: {
    value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'
  }
}

// Role assignments for managed identity
resource cosmosContributorRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(cosmosAccount.id, managedIdentity.id, 'b24988ac-6180-42a0-ab88-20f7382dd24c')
  scope: cosmosAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b24988ac-6180-42a0-ab88-20f7382dd24c') // Cosmos DB Contributor
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource storageContributorRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, managedIdentity.id, 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe') // Storage Blob Data Contributor
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Outputs
output webAppName string = webApp.name
output webAppUrl string = 'https://${webApp.properties.defaultHostName}'
output cosmosEndpoint string = cosmosAccount.properties.documentEndpoint
output openAiEndpoint string = 'https://eastus.api.cognitive.microsoft.com/' // Use existing OpenAI resource
output computerVisionEndpoint string = computerVision.properties.endpoint
output textAnalyticsEndpoint string = textAnalytics.properties.endpoint
output storageAccountName string = storageAccount.name
output keyVaultName string = keyVault.name
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
output appInsightsConnectionString string = appInsights.properties.ConnectionString
output managedIdentityPrincipalId string = managedIdentity.properties.principalId
