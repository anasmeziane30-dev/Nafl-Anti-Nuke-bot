import discord
from discord.ext import commands
import os
import time
import threading
from flask import Flask

# --- خادم الويب الوهمي لبقاء البوت نشطاً على Render مجاناً ---
app = Flask(__name__)

@app.route('/')
def home():
    return "I am alive!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

# --- إعدادات البوت الأساسية ---
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.moderation = True
intents.guild_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)
TOKEN = os.getenv("TOKEN")

# القواميس لتتبع العمليات
channel_actions = {}
role_actions = {}
ban_actions = {}

def is_limited(user_id, action_dict, threshold, window=60.0):
    now = time.time()
    if user_id not in action_dict:
        action_dict[user_id] = []
    
    action_dict[user_id].append(now)
    action_dict[user_id] = [t for t in action_dict[user_id] if now - t < window]
    
    return len(action_dict[user_id]) > threshold

@bot.event
async def on_guild_channel_delete(channel):
    guild = channel.guild
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
        user = entry.user
        if user.id == guild.owner_id or user.bot: return
        if is_limited(user.id, channel_actions, 0): # حظر فوري
            await guild.ban(user, reason="Anti-Nuke: حذف قنوات")
        break

@bot.event
async def on_guild_role_delete(role):
    guild = role.guild
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        user = entry.user
        if user.id == guild.owner_id or user.bot: return
        if is_limited(user.id, role_actions, 0): # حظر فوري
            await guild.ban(user, reason="Anti-Nuke: حذف رتب")
        break

@bot.event
async def on_member_ban(guild, user):
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
        admin = entry.user
        if admin.id == guild.owner_id or admin.bot: return
        # threshold=1 يعني إذا قام بحظر شخصين (الأول يعتبر، الثاني يفعّل البان)
        if is_limited(admin.id, ban_actions, 1, window=60.0): 
            await guild.ban(admin, reason="Anti-Nuke: حظر أعضاء بشكل مكثف")
        break

@bot.event
async def on_ready():
    print(f"تم تشغيل بوت الحماية باسم {bot.user}")

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    bot.run(TOKEN)
