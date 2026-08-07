import discord
from discord.ext import commands
import os
import time
import threading
from flask import Flask

# --- خادم الويب الوهمي لبقاء البوت نشطاً على Render مجاناً ---
app = Flask('')

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

def is_limited(user_id, action_dict, threshold, window):
    now = time.time()
    if user_id not in action_dict:
        action_dict[user_id] = []
    
    action_dict[user_id].append(now)
    # تنظيف العمليات القديمة خارج النافذة الزمنية
    action_dict[user_id] = [t for t in action_dict[user_id] if now - t < window]
    
    # إذا تجاوز عدد العمليات الحد الأقصى (THRESHOLD)
    return len(action_dict[user_id]) > threshold

@bot.event
async def on_guild_channel_delete(channel):
    try:
        guild = channel.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            user = entry.user
            if user.id == guild.owner_id or user.bot: 
                return
            
            # threshold=1 يعني العملية الأولى تعتبر، وعند الوصول للثانية (تجاوز 1) يتم الحظر خلال 5 ثوانٍ
            if is_limited(user.id, channel_actions, threshold=1, window=5.0):
                member = guild.get_member(user.id)
                if member:
                    await guild.ban(member, reason="Anti-Nuke: حذف قناتين في وقت قصير")
            break
    except Exception as e:
        print(f"خطأ في مراقبة القنوات: {e}")

@bot.event
async def on_guild_role_delete(role):
    try:
        guild = role.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            user = entry.user
            if user.id == guild.owner_id or user.bot: 
                return
            
            # threshold=1 يعني رتبتين في 5 ثوانٍ
            if is_limited(user.id, role_actions, threshold=1, window=5.0):
                member = guild.get_member(user.id)
                if member:
                    await guild.ban(member, reason="Anti-Nuke: حذف رتبتين في وقت قصير")
            break
    except Exception as e:
        print(f"خطأ في مراقبة الرتب: {e}")

@bot.event
async def on_member_ban(guild, user):
    try:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            admin = entry.user
            if admin.id == guild.owner_id or admin.bot: 
                return
            
            # threshold=1 يعني عضوين في دقيقة (60 ثانية)
            if is_limited(admin.id, ban_actions, threshold=1, window=60.0):
                member = guild.get_member(admin.id)
                if member:
                    await guild.ban(member, reason="Anti-Nuke: حظر عضوين بشكل مكثف")
            break
    except Exception as e:
        print(f"خطأ في مراقبة الحظر: {e}")

@bot.event
async def on_ready():
    print(f"تم تشغيل بوت الحماية بنجاح باسم {bot.user}")

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    bot.run(TOKEN)
