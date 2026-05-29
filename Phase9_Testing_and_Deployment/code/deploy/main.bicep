@description('Location for all resources.')
param location string = resourceGroup().location

@description('Short name for the workload. Used as a prefix for resource names.')
@minLength(2)
@maxLength(12)
param workloadName string = 'agent365'

@description('Container image to deploy, e.g. myregistry.azurecr.io/agent:latest')
param containerImage string

@description('Azure OpenAI endpoint URL.')
param azureOpenAiEndpoint string

@secure()
@description('Azure OpenAI API key.')
param azureOpenAiApiKey string

@description('Azure OpenAI deployment name (e.g. gpt-4o-mini).')
param azureOpenAiDeployment string = 'gpt-4o-mini'

var prefix = toLower(workloadName)

// ---- Log Analytics ----
resource law 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${prefix}-law'
  location: location
  properties: {
    retentionInDays: 30
    sku: { name: 'PerGB2018' }
  }
}

// ---- Application Insights ----
resource appi 'Microsoft.Insights/components@2020-02-02' = {
  name: '${prefix}-appi'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: law.id
  }
}

// ---- Container Apps Environment ----
resource cae 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${prefix}-cae'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: law.properties.customerId
        sharedKey: law.listKeys().primarySharedKey
      }
    }
  }
}

// ---- Container App ----
resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${prefix}-app'
  location: location
  properties: {
    managedEnvironmentId: cae.id
    configuration: {
      ingress: {
        external: true
        targetPort: 3978
        transport: 'auto'
        allowInsecure: false
      }
      secrets: [
        { name: 'aoai-key', value: azureOpenAiApiKey }
        { name: 'appi-conn', value: appi.properties.ConnectionString }
      ]
    }
    template: {
      containers: [
        {
          name: 'agent'
          image: containerImage
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'PORT', value: '3978' }
            { name: 'AZURE_OPENAI_ENDPOINT', value: azureOpenAiEndpoint }
            { name: 'AZURE_OPENAI_DEPLOYMENT', value: azureOpenAiDeployment }
            { name: 'AZURE_OPENAI_API_VERSION', value: '2024-10-21' }
            { name: 'AZURE_OPENAI_API_KEY', secretRef: 'aoai-key' }
            { name: 'AZURE_APP_INSIGHTS_CONNECTION_STRING', secretRef: 'appi-conn' }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: { path: '/healthz', port: 3978 }
              initialDelaySeconds: 10
              periodSeconds: 30
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

output appUrl string = 'https://${app.properties.configuration.ingress.fqdn}'
output appInsightsName string = appi.name
