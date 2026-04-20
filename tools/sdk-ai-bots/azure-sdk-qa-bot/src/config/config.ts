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
  ragTenantId: process.env.RAG_TENANT_ID || 'digital_avatar_jay_parikh',
  // Azure Table Storage
  azureStorageUrl: storageAccountName ? `https://${storageAccountName}.table.core.windows.net/` : undefined,
  azureTableNameForConversation: process.env.AZURE_TABLE_NAME_FOR_CONVERSATION,
  // Local config
  isLocal: process.env.IS_LOCAL === 'true',
  // Bot display name
  botDisplayName: process.env.TEAMS_BOT_FULL_DISPLAY_NAME || 'Parikh Public Lens',
  // Feature flags
  showReferences: process.env.SHOW_REFERENCES?.toLowerCase() === 'true',
};

export const ragApiPaths = {
  completion: '/completion',
};

export const contactCardVersion = `1.0.0`;

export default config;
