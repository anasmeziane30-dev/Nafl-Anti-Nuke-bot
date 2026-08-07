import discord
from discord.ext import commands
import os
import time
import threading
from flask import Flask

app = Flask('')
@app.route('/')
def home(): return "I am alive!"
def run_web(): app.run(host='0.0.0.0', port=8080)

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.moderation = True

bot = commands.Bot(command_prefix="!", intents=intents)
TOKEN = os.getenv("TOKEN")

# القواميس
actions = {"kick": {}, "ban": {}, "channel": {}, "role": {}}

def check(uid, key, threshold, window):
    now = time.time()
    if uid not in actions[key]: actions[key][uid] = []
    actions[key][uid].append(now)
    actions[key][uid] = [t for t in actions[key][uid] if now - t < window]
    return len(actions[key][uid]) > threshold

@bot.event
async def on_member_remove(member):
    async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
        if entry.target.id == member.id:
            if check(entry.user.id, "kick", 1, 10.0):
                await member.guild.ban(entry.user, reason="Anti-Nuke: طرد مكثف")
        break

@bot.event
async def on_member_ban(guild, user):
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
        if check(entry.user.id, "ban", 1, 60.0):
            await guild.ban(entry.user, reason="Anti-Nuke: حظر مكثف")
        break

@bot.event
async def on_guild_channel_delete(channel):
    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
        if check(entry.user.id, "channel", 1, 5.0):
            await channel.guild.ban(entry.user, reason="Anti-Nuke: حذف قنوات")
        break

@bot.event
async def on_guild_role_delete(role):
    async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        if check(entry.user.id, "role", 1, 5.0):
            await role.guild.guild.ban(entry.user, reason="Anti-Nuke: حذف رتب")
        break

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    bot.run(TOKEN)
