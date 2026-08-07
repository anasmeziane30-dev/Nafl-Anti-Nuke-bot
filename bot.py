import discord
from discord.ext import commands
import os
import time

# إعدادات الصلاحيات (Intents)
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.moderation = True  # تعادل الإشراف في الإصدارات الحديثة
intents.guild_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# قراءة التوكن من متغيرات البيئة في Render بأمان تام
TOKEN = os.getenv("TOKEN")

# إعدادات الحد الأقصى للتخريب (عدد العمليات خلال 5 ثوانٍ)
THRESHOLD = 3
TIME_WINDOW = 5.0
actions_map = {}

def check_action_limit(guild_id, user_id, action_type):
    key = f"{guild_id}-{user_id}-{action_type}"
    now = time.time()
    
    if key not in actions_map:
        actions_map[key] = []
    
    # إضافة الوقت الحالي للعملية
    actions_map[key].append(now)
    
    # تصفية العمليات القديمة خارج النافذة الزمنية
    actions_map[key] = [t for t in actions_map[key] if now - t < TIME_WINDOW]
    
    return len(actions_map[key]) > THRESHOLD

async def punish_user(member, guild, reason):
    try:
        # عدم معاقبة صاحب السيرفر أو البوتات نفسها
        if member.id == guild.owner_id or member.bot:
            return
        
        print(f"[Anti-Nuke] تم رصد تخريب من قبل {member} بسبب: {reason}")
        await guild.ban(member, reason=f"Anti-Nuke: {reason}")
    except Exception as e:
        print(f"فشل معاقبة المستخدم {member}: {e}")

# مراقبة حذف القنوات
@bot.event
async def on_guild_channel_delete(channel):
    try:
        guild = channel.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            user = entry.user
            member = guild.get_member(user.id)
            if member and check_action_limit(guild.id, member.id, "CHANNEL_DELETE"):
                await punish_user(member, guild, "حذف عدد كبير من القنوات دفعة واحدة")
            break
    except Exception as e:
        print(e)

# مراقبة حذف الرتب
@bot.event
async def on_guild_role_delete(role):
    try:
        guild = role.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            user = entry.user
            member = guild.get_member(user.id)
            if member and check_action_limit(guild.id, member.id, "ROLE_DELETE"):
                await punish_user(member, guild, "حذف عدد كبير من الرتب دفعة واحدة")
            break
    except Exception as e:
        print(e)

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح باسم {bot.user} وحماية السيرفرات مفعلة!")

# تشغيل البوت
if TOKEN:
    bot.run(TOKEN)
else:
    print("خطأ: لم يتم العثور على التوكن في متغيرات البيئة (TOKEN).")
