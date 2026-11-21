// KiwiAsk M0 infrastructure.
// Deploy into an existing resource group (see infra/README.md).

targetScope = 'resourceGroup'

@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('Tags applied to every resource.')
param tags object = {
  project: 'kiwi-ask'
}

@description('Foundry (AI Services) resource name. Also used as the custom subdomain, so it must be globally unique.')
@minLength(2)
@maxLength(64)
param foundryName string = 'ais-kiwiask-dev'

@description('Foundry project name.')
param projectName string = 'proj-kiwiask-dev'

@description('Key Vault name. Globally unique, 3-24 characters.')
@minLength(3)
@maxLength(24)
param keyVaultName string

@description('Log Analytics workspace name.')
param logAnalyticsName string = 'log-kiwiask-dev'

@description('Application Insights name.')
param appInsightsName string = 'appi-kiwiask-dev'

@description('Object ID of the user or identity that calls the models and manages secrets.')
@minLength(36)
@maxLength(36)
param principalId string

@description('Type of the principal in principalId.')
@allowed([
  'User'
  'Group'
  'ServicePrincipal'
])
param principalType string = 'User'

@description('Chat model deployment settings.')
param chatDeployment object = {
  name: 'chat-mini'
  model: 'gpt-5-mini'
  version: '2025-08-07'
  capacity: 20
}

@description('Embedding model deployment settings.')
param embedDeployment object = {
  name: 'embed-small'
  model: 'text-embedding-3-small'
  version: '1'
  capacity: 50
}

// Built-in role definition IDs.
var cognitiveServicesOpenAIUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
var keyVaultSecretsOfficerRoleId = 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7'

// ---------- Foundry resource, project and model deployments ----------

resource foundry 'Microsoft.CognitiveServices/accounts@2026-09-01' = {
  name: foundryName
  location: location
  tags: tags
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: foundryName
    allowProjectManagement: true
    // Entra ID only: API keys are disabled at the platform level.
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2026-09-01' = {
  parent: foundry
  name: projectName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
}

resource chat 'Microsoft.CognitiveServices/accounts/deployments@2026-09-01' = {
  parent: foundry
  name: chatDeployment.name
  // Child operations on the same account must run one at a time:
  // project -> chat -> embed. Parallel writes fail with RequestConflict.
  dependsOn: [
    project
  ]
  sku: {
    name: 'GlobalStandard'
    capacity: chatDeployment.capacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: chatDeployment.model
      version: chatDeployment.version
    }
  }
}

resource embed 'Microsoft.CognitiveServices/accounts/deployments@2026-09-01' = {
  parent: foundry
  name: embedDeployment.name
  dependsOn: [
    chat
  ]
  sku: {
    name: 'GlobalStandard'
    capacity: embedDeployment.capacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: embedDeployment.model
      version: embedDeployment.version
    }
  }
}

// ---------- Monitoring ----------

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2026-03-01' = {
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

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
  }
}

// ---------- Key Vault ----------

resource keyVault 'Microsoft.KeyVault/vaults@2026-05-15' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: tenant().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    // enablePurgeProtection is omitted on purpose: it cannot be set to false,
    // and enabling it would block purging the vault when the lab is torn down.
  }
}

// ---------- Role assignments (scoped to single resources) ----------

resource openAIUserAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundry.id, principalId, cognitiveServicesOpenAIUserRoleId)
  scope: foundry
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesOpenAIUserRoleId)
    principalId: principalId
    principalType: principalType
  }
}

resource secretsOfficerAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, principalId, keyVaultSecretsOfficerRoleId)
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsOfficerRoleId)
    principalId: principalId
    principalType: principalType
  }
}

// ---------- Outputs ----------

@description('Foundry endpoint (cognitiveservices.azure.com).')
output foundryEndpoint string = foundry.properties.endpoint

@description('OpenAI-compatible endpoint used as AZURE_OPENAI_ENDPOINT in .env.')
output openAIEndpoint string = 'https://${foundry.properties.customSubDomainName}.openai.azure.com/'

@description('Key Vault URI.')
output keyVaultUri string = keyVault.properties.vaultUri

@description('Project name, for reference.')
output projectName string = project.name

@description('Application Insights resource name, for later modules.')
output appInsightsName string = appInsights.name
