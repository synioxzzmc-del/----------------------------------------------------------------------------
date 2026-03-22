import discord
from discord.ext import commands
from flask import Flask
import threading
import os
import time

# ── Keep-alive ─────────────────────────────────────────────────────
app = Flask(__name__)

@app.route("/")
def home():
    return "Honey Bee is alive! 🐝"

threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8080), daemon=True).start()

# ── Config ─────────────────────────────────────────────────────────
LTC_ADDRESS  = "LMSi7L5zdc6AsaJ5JgxUAPTmjnMJK1raKS"
GAMEPASS_URL = "https://www.roblox.com/game-pass/1502229786/1000"
PRICE_LTC    = "0.40$"
PRICE_ROBUX  = "100 Robux"
OWNER_ROLE   = "."  # only this role can use !setup

COLOUR = 0x1a1a2e
ACCENT = 0xf5c518
ERROR  = 0xff3333
OK     = 0x39ff14

# ── Bot setup ──────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

def embed(title, desc=None, color=COLOUR):
    e = discord.Embed(title=title, description=desc, color=color)
    e.set_footer(text="🐝 Honey Bee")
    return e

# ── Shop dropdown ──────────────────────────────────────────────────
class PaymentSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Pay with LTC", description=f"{PRICE_LTC} in LTC", emoji="💰"),
            discord.SelectOption(label="Pay with Robux", description=f"{PRICE_ROBUX} gamepass", emoji="🎮"),
        ]
        super().__init__(placeholder="Choose payment method...", options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user

        # Check if ticket already exists
        existing = discord.utils.get(guild.text_channels, name=f"ticket-{member.name.lower()}")
        if existing:
            await interaction.response.send_message(
                embed=embed("⚠️ Ticket exists.", f"You already have a ticket: {existing.mention}", ERROR),
                ephemeral=True
            )
            return

        # Get owner role for permissions
        owner_role = discord.utils.get(guild.roles, name=OWNER_ROLE)

        # Create private channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        if owner_role:
            overwrites[owner_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{member.name.lower()}",
            overwrites=overwrites,
            reason="Shop ticket"
        )

        # Send payment info based on selection
        if self.values[0] == "Pay with LTC":
            e = discord.Embed(title="🐝 BSS Sign — LTC Payment", color=ACCENT)
            e.add_field(name="💰 Price", value=f"`{PRICE_LTC}`", inline=True)
            e.add_field(name="📦 Item", value="BSS Sign", inline=True)
            e.add_field(name="🏦 LTC Address", value=f"`{LTC_ADDRESS}`", inline=False)
            e.add_field(name="📌 Instructions", value="1. Send exactly **$0.40 in LTC** to the address above\n2. Send a screenshot of the transaction here\n3. Staff will deliver your sign!", inline=False)
            e.set_footer(text="🐝 Honey Bee")
        else:
            e = discord.Embed(title="🐝 BSS Sign — Robux Payment", color=ACCENT)
            e.add_field(name="🎮 Price", value=f"`{PRICE_ROBUX}`", inline=True)
            e.add_field(name="📦 Item", value="BSS Sign", inline=True)
            e.add_field(name="🔗 Gamepass Link", value=f"[Click here to buy]({GAMEPASS_URL})", inline=False)
            e.add_field(name="📌 Instructions", value="1. Purchase the gamepass at the link above\n2. Send your **Roblox username** here\n3. Staff will deliver your sign!", inline=False)
            e.set_footer(text="🐝 Honey Bee")

        # Close ticket button
        close_view = discord.ui.View()
        close_btn = discord.ui.Button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger)

        async def close_callback(i: discord.Interaction):
            await i.response.send_message(embed=embed("🔒 Closing ticket...", color=ERROR))
            await channel.delete()

        close_btn.callback = close_callback
        close_view.add_item(close_btn)

        await channel.send(
            content=f"{member.mention} {''+owner_role.mention if owner_role else ''}",
            embed=e,
            view=close_view
        )

        await interaction.response.send_message(
            embed=embed("✅ Ticket opened!", f"Head to {channel.mention}", OK),
            ephemeral=True
        )

class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PaymentSelect())

# ── Setup command (owner role only) ───────────────────────────────
@bot.command(name="setup")
async def setup(ctx):
    role = discord.utils.get(ctx.guild.roles, name=OWNER_ROLE)
    if role not in ctx.author.roles:
        await ctx.send(embed=embed("❌ No permission.", "You need the `.` role.", ERROR))
        return

    e = discord.Embed(
        title="🐝 BSS Sign Shop",
        description="Welcome! Pick your payment method below to open a ticket and purchase a **BSS Sign**.\n\n💰 **$0.40 in LTC**\n🎮 **100 Robux**",
        color=ACCENT
    )
    e.set_footer(text="🐝 Honey Bee • Powered by Honey Bee Bot")
    await ctx.send(embed=e, view=ShopView())
    await ctx.message.delete()

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="🐝 BSS Signs Shop"))
    bot.add_view(ShopView())  # persist view after restart
    print(f"🐝 Honey Bee live as {bot.user}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass  # ignore unknown commands silently
    else:
        await ctx.send(embed=embed("💀 Error.", str(error), ERROR))

# ── Wait before connecting ─────────────────────────────────────────
print("⏳ Waiting 60 seconds before connecting to Discord...")
time.sleep(60)

import asyncio

async def main():
    try:
        await bot.start(os.environ["DISCORD_TOKEN"])
    except discord.errors.HTTPException as e:
        if e.status == 429:
            print(f"❌ Rate limited by Discord. Waiting 5 minutes...")
            time.sleep(300)
            await bot.start(os.environ["DISCORD_TOKEN"])
        else:
            print(f"❌ HTTP Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

asyncio.run(main())
