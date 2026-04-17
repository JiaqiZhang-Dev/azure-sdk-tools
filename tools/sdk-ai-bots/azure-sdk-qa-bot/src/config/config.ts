// Storage account name
const storageAccountName = process.env.STORAGE_ACCOUNT_NAME;

const config = {
  // Teams app
  MicrosoftAppId: process.env.BOT_ID,
  MicrosoftAppType: process.env.BOT_TYPE,
  MicrosoftAppTenantId: process.env.BOT_TENANT_ID,
  MicrosoftAppPassword: process.env.BOT_PASSWORD,
  // auth
  userManagedIdentityClientID: process.env.BOT_ID,
  ragScope: process.env.RAG_SERVICE_SCOPE,
  // RAG backend
  ragEndpoint: process.env.RAG_ENDPOINT,
  // Azure Table Storage
  azureStorageUrl: storageAccountName ? `https://${storageAccountName}.table.core.windows.net/` : undefined,
  azureTableNameForConversation: process.env.AZURE_TABLE_NAME_FOR_CONVERSATION,
  // Local config
  isLocal: process.env.IS_LOCAL === 'true',
};

export const ragApiPaths = {
  completion: '/completion',
};

export const contactCardVersion = `1.0.0`;

export default config;
