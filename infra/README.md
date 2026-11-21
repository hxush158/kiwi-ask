# KiwiAsk infrastructure (M0)

`main.bicep` deploys the M0 resources into one resource group:

| Resource | Default name |
| --- | --- |
| Foundry resource (AI Services, Entra ID only, API keys disabled) | `ais-kiwiask-dev` |
| Foundry project | `proj-kiwiask-dev` |
| Model deployments (GlobalStandard, created one after another) | `chat-mini` (gpt-5-mini, 20K TPM), `embed-small` (text-embedding-3-small, 50K TPM) |
| Log Analytics workspace + Application Insights | `log-kiwiask-dev`, `appi-kiwiask-dev` |
| Key Vault (RBAC, soft delete 7 days, no purge protection) | set in `main.bicepparam` |
| Role assignments for `PRINCIPAL_ID`, scoped to single resources | Cognitive Services OpenAI User (Foundry), Key Vault Secrets Officer (Key Vault) |

All resources are tagged `project=kiwi-ask`.

## Before you deploy

1. Check the model versions are still available in the region:

   ```bash
   az cognitiveservices model list -l australiaeast \
     --query "[?model.name=='gpt-5-mini' || model.name=='text-embedding-3-small'].{name:model.name, version:model.version}" -o table
   ```

   If a version differs, update `chatDeployment` / `embedDeployment` in `main.bicep`.

2. Make sure `keyVaultName` in `main.bicepparam` is not taken (Key Vault names are
   global, and deleted vaults keep their name during soft delete).

3. Set your object ID (read by `main.bicepparam`, never committed):

   ```bash
   export PRINCIPAL_ID=$(az ad signed-in-user show --query id -o tsv)
   ```

## Validate, preview, deploy

```bash
az bicep build -f infra/main.bicep
az bicep lint -f infra/main.bicep

az group create -n rg-kiwiask-dev -l australiaeast --tags project=kiwi-ask

# Preview only: shows what would be created, changes nothing.
az deployment group what-if -g rg-kiwiask-dev \
  -f infra/main.bicep -p infra/main.bicepparam

# Deploy after reviewing the what-if output.
az deployment group create -g rg-kiwiask-dev \
  -f infra/main.bicep -p infra/main.bicepparam \
  --query properties.outputs
```

Put the `openAIEndpoint` output into `.env` as `AZURE_OPENAI_ENDPOINT`.
Role assignments can take a few minutes before calls succeed.

## Tear down

```bash
az group delete -n rg-kiwiask-dev
az keyvault purge -n <keyVaultName>   # frees the Key Vault name after soft delete
```
