import discord
import anthropic
import os
from flask import Flask
import threading

# ── Keep-alive web server for Render/UptimeRobot ──────────────────
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run_web():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_web, daemon=True).start()

# ── Discord bot setup ─────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == client.user:
        return

    # Only respond when the bot is @mentioned
    if client.user not in message.mentions:
        return

    # Remove the mention from the message text
    user_text = message.content.replace(f"<@{client.user.id}>", "").strip()

    if not user_text:
        await message.reply("Hey! Ask me anything 👋")
        return

    async with message.channel.typing():
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system="You are a helpful and friendly Discord bot assistant.",
            messages=[{"role": "user", "content": user_text}]
        )
        reply = response.content[0].text

    # Discord has a 2000 char limit per message
    if len(reply) > 2000:
        reply = reply[:1997] + "..."

    await message.reply(reply)

client.run(os.environ["DISCORD_TOKEN"])
