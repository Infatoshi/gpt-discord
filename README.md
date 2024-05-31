# gpt-discord

Requires an `OPENAI_API_KEY` and `DISCORD_TOKEN` (configure this in the discord developer portal) in the `.env` file.
Uses GPT-3.5-Turbo by default but feel free to change it.
```
python -m venv gpt-ds
source gpt-ds/bin/activate
pip install -r requirements.txt
mkdir conversation_logs
python bot.py
```
Usage:
`/prompt <yourprompthere>` requests a completion based on current conversation context
`/newchat` Create a new chat if the conversation is long enough (to prevent spamming)

Enjoy :)
