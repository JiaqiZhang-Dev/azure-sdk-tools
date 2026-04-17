import { MemoryStorage } from 'botbuilder';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { Application, ActionPlanner, PromptManager } from '@microsoft/teams-ai';
import { RAGModel } from '../models/RAGModel.js';
import config from '../config/config.js';
import { ConversationHandler } from '../input/ConversationHandler.js';
import { ManagedIdentityCredential, TokenCredential } from '@azure/identity';

const conversationHandler = new ConversationHandler();
await conversationHandler.initialize();

let credential: TokenCredential = new ManagedIdentityCredential(config.userManagedIdentityClientID);

// Create AI components
const model = new RAGModel(conversationHandler, credential);

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const prompts = new PromptManager({
  promptsFolder: path.join(__dirname, '../prompts'),
});

const planner = new ActionPlanner({
  model,
  prompts,
  defaultPrompt: 'chat',
});

// Define storage and application
const storage = new MemoryStorage();
const app = new Application({
  storage,
  ai: {
    planner,
  },
});

export default app;
