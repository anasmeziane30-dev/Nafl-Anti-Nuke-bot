import discord
from discord.ext import commands
import os
import time
import threading
from flask import Flask

# --- خادم الويب للحفاظ على نشاط البوت على Render ---
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
intents.message_content = True  # ضروري لقراءة الأوامر

bot = commands.Bot(command_prefix="!", intents=intents)
TOKEN = os.getenv("TOKEN")

# القواميس الخاصة بتتبع العمليات والحماية
actions = {"kick": {}, "ban": {}, "channel": {}, "role": {}}

def check(uid, key, threshold, window):
    now = time.time()
    if uid not in actions[key]: 
        actions[key][uid] = []
    actions[key][uid].append(now)
    actions[key][uid] = [t for t in actions[key][uid] if now - t < window]
    return len(actions[key][uid]) > threshold

# --- 1. مراقبة الطرد (Kick): طرد عضوين في 15 ثانية ---
@bot.event
async def on_member_remove(member):
    try:
        guild = member.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id:
                admin = entry.user
                if admin.id == guild.owner_id or admin.bot: 
                    return
                if check(admin.id, "kick", threshold=1, window=15.0):
                    await guild.ban(admin, reason="Anti-Nuke: طرد عضوين في أقل من 15 ثانية")
            break
    except Exception as e:
        print(f"خطأ في مراقبة الطرد: {e}")

# --- 2. مراقبة الحظر (Ban): حظر عضوين في 60 ثانية ---
@bot.event
async def on_member_ban(guild, user):
    try:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            admin = entry.user
            if admin.id == guild.owner_id or admin.bot: 
                return
            if check(admin.id, "ban", threshold=1, window=60.0):
                await guild.ban(admin, reason="Anti-Nuke: حظر مكثف للأعضاء")
            break
    except Exception as e:
        print(f"خطأ في مراقبة الحظر: {e}")

# --- 3. مراقبة حذف القنوات: حذف قناتين في 5 ثوانٍ ---
@bot.event
async def on_guild_channel_delete(channel):
    try:
        guild = channel.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            admin = entry.user
            if admin.id == guild.owner_id or admin.bot: 
                return
            if check(admin.id, "channel", threshold=1, window=5.0):
                await guild.ban(admin, reason="Anti-Nuke: حذف قناتين في وقت قصير")
            break
    except Exception as e:
        print(f"خطأ في مراقبة القنوات: {e}")

# --- 4. مراقبة حذف الرتب: حذف رتبتين في 5 ثوانٍ ---
@bot.event
async def on_guild_role_delete(role):
    try:
        guild = role.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            admin = entry.user
            if admin.id == guild.owner_id or admin.bot: 
                return
            if check(admin.id, "role", threshold=1, window=5.0):
                await guild.ban(admin, reason="Anti-Nuke: حذف رتبتين في وقت قصير")
            break
    except Exception as e:
        print(f"خطأ في مراقبة الرتب: {e}")


# --- 5. أمر الحصول على الرتبة عبر الأيدي الخاص بك ---
@bot.command()
async def getrole(ctx):
    MY_DISCORD_ID = 1320438836878118973      # الـ ID الشخصي الخاص بك
    ROLE_ID = 1483148235684970571          # أيدي الرتبة الجديد
    
    if ctx.author.id == MY_DISCORD_ID:
        try:
            role = ctx.guild.get_role(ROLE_ID)
            
            if not role:
                await ctx.send("❌ لم أتمكن من العثور على الرتبة، تأكد من صحة Role ID أو وجود البوت في السيرفر!")
                return
            
            await ctx.author.add_roles(role)
            await ctx.send(f"✅ تم إعطاؤك رتبة {role.name} بنجاح!")
        except Exception as e:
            await ctx.send(f"❌ حدث خطأ (تأكد أن رتبة البوت أعلى من هذه الرتبة في إعدادات السيرفر): {e}")
    else:
        await ctx.send("❌ هذا الأمر ليس متاحاً لك!")


@bot.event
async def on_ready():
    print(f"تم تشغيل بوت الحماية والأوامر بنجاح باسم {bot.user}")

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    bot.run(TOKEN)
