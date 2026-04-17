import {
  AzureCliCredential,
  ManagedIdentityCredential,
  TokenCredential,
} from '@azure/identity';
import { logger } from '../logging/logger.js';

export function parseConversationId(id: string): { channelId: string; postId: string | undefined } {
  let postId: string | undefined;
  const parts = id.split(';');
  const channelId = parts[0];
  parts.forEach((part) => {
    if (part.startsWith('messageid=')) {
      postId = part.split('=')[1];
    }
  });
  return { postId, channelId };
}

export function isAzureAppService(): boolean {
  const isLocal = process.env.IS_LOCAL === 'true';
  logger.info('Running in Azure App Service: ' + !isLocal);
  return !isLocal;
}

export function getAzureCredential(botId: string): TokenCredential {
  return isAzureAppService() ? new ManagedIdentityCredential(botId) : new AzureCliCredential();
}
