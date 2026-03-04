# Telegram Bot Setup

## 1. Create Bot

1. Message @BotFather on Telegram
2. Send `/newbot`
3. Name it (e.g., "CRB Operator")
4. Copy the bot token

## 2. Get Your Chat ID

1. Start a chat with your new bot
2. Send `/chatid`
3. Copy the number

## 3. Set Environment Variables

Add to your `.env`:

```
TELEGRAM_BOT_TOKEN=your-bot-token-here
TELEGRAM_ADMIN_CHAT_ID=your-chat-id-here
```

For voice notes, also set:
```
OPENAI_API_KEY=your-openai-key-here
```

## 4. Set Webhook (Production)

After deploying, register the webhook URL with Telegram:

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-app.railway.app/api/telegram/webhook"}'
```

## 5. Commands

| Command | Description |
|---------|-------------|
| /start | Welcome + command list |
| /health | System health check |
| /reports [period] | Report delivery stats |
| /leads | Recent quiz completions |
| /vendors [stale\|refresh] | Vendor data status |
| /briefing | Full morning digest |
| /capture <text> | GTD: add to inbox |
| /next [context] | GTD: next actions |
| /projects | GTD: active projects |
| /waiting | GTD: waiting-for list |
| /someday | GTD: someday/maybe |
| /review | GTD: review summary |
| /idea <text> | Capture an idea |
| /code <task> | Claude Code bridge |
