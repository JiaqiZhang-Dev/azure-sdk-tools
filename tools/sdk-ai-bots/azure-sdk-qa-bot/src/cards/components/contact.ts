export function createContactCard() {
  const card = {
    type: 'AdaptiveCard',
    body: [
      {
        type: 'TextBlock',
        text: '🤖 The following is AI-generated response that summarizes Jay Parikh\'s public talks/interviews for quick reference — not authored by Jay!',
        wrap: true,
      },
      {
        type: 'TextBlock',
        text: '📝 The bot cannot respond further to messages with edits; reply with @Parikh Public Lens for follow-up.',
        wrap: true,
      },
    ],
    $schema: 'http://adaptivecards.io/schemas/adaptive-card.json',
    version: '1.5',
  };
  return card;
}
