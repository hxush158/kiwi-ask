using 'main.bicep'

// Globally unique. Change the suffix if the name is taken.
param keyVaultName = 'kv-kiwiask-dev-01'

// Your Entra object ID, read from the environment so it is not committed:
//   export PRINCIPAL_ID=$(az ad signed-in-user show --query id -o tsv)
param principalId = readEnvironmentVariable('PRINCIPAL_ID')
