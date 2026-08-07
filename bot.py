import discord
from discord.ext import commands
import os
import time
import threading
from flask import Flask

# --- كود خادم الويب الوهمي للحفاظ على نشاط البوت ---
app = Flask(__name__)

@app.route('/')
def home():
    return "I am alive!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

# --- كود البوت الأساسي ---
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.moderation = True

bot = commands.Bot(command_prefix="!", intents=intents)
TOKEN = os.getenv("TOKEN")

THRESHOLD = 3
TIME_WINDOW = 5.0
actions_map = {}

def check_action_limit(guild_id, user_id, action_type):
    key = f"{guild_id}-{user_id}-{action_type}"
    now = time.time()
    if key not in actions_map:
        actions_map[key] = []
    actions_map[key].append(now)
    actions_map[key] = [t for t in actions_map[key] if now - t < TIME_WINDOW]
    return len(actions_map[key]) > THRESHOLD

async def punish_user(member, guild, reason):
    try:
        if member.id == guild.owner_id or member.bot:
            return
        await guild.ban(member, reason=f"Anti-Nuke: {reason}")
    except Exception as e:
        print(f"Error punishing user: {e}")

@bot.event
async def on_guild_channel_delete(channel):
    try:
        guild = channel.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            member = guild.get_member(entry.user.id)
            if member and check_action_limit(guild.id, member.id, "CHANNEL_DELETE"):
                await punish_user(member, guild, "حذف قنوات بشكل متكرر")
            break
    except Exception as e:
        print(f"Error in channelDelete: {e}")

@bot.event
async def on_guild_role_delete(role):
    try:
        guild = role.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            member = guild.get_member(entry.user.id)
            if member and check_action_limit(guild.id, member.id, "ROLE_DELETE"):
                await punish_user(member, guild, "حذف رتب بشكل متكرر")
            break
    except Exception as e:
        print(f"Error in roleDelete: {e}")

@bot.event
async def on_ready():
    print(f"تم التشغيل بنجاح باسم {bot.user}")

# تشغيل خادم الويب والبوت معاً
if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    bot.run(TOKEN)
