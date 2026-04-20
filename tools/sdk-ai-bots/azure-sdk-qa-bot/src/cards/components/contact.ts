import config from '../../config/config.js';

export function createContactCard() {
  const card = {
    type: 'AdaptiveCard',
    body: [
      {
        type: 'TextBlock',
        text: `🤖 This bot is an informal digest of Jay Parikh's public statements, powered by ${config.modelName}; it may be incomplete and should not be treated as official guidance.`,
        wrap: true,
      },
      {
        type: 'TextBlock',
        text: `📝 The bot cannot respond further to messages with edits; reply with @${config.botDisplayName} for follow-up.`,
        wrap: true,
      },
    ],
    $schema: 'http://adaptivecards.io/schemas/adaptive-card.json',
    version: '1.5',
  };
  return card;
}
