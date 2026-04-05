import discord
from discord.ext import commands
import random
import json
import os
from flask import Flask
from threading import Thread

# ================== TOKEN ==================
TOKEN = os.environ.get("DISCORD_TOKEN")
if TOKEN is None:
    print("❌ ERROR: Discord token not found in environment variables")
    exit()

# ================== BOT SETUP ==================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ================== FLASK SERVER FOR UPTIMEROBOT ==================
app = Flask("")

@app.route("/ping")
def ping():
    return "OK"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()  # start Flask in background

# ================== ON READY ==================
@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user} (ID: {bot.user.id})")

# ================== LEVEL SYSTEM ==================
def load_data():
    if not os.path.exists("levels.json"):
        with open("levels.json", "w") as f:
            json.dump({}, f)
    with open("levels.json", "r") as f:
        return json.load(f)

def save_data(data):
    with open("levels.json", "w") as f:
        json.dump(data, f, indent=4)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    data = load_data()
    user_id = str(message.author.id)
    if user_id not in data:
        data[user_id] = {"xp": 0, "level": 1}
    data[user_id]["xp"] += 5
    xp = data[user_id]["xp"]
    lvl = data[user_id]["level"]
    if xp >= lvl * 100:
        data[user_id]["level"] += 1
        data[user_id]["xp"] = 0
        await message.channel.send(f"🎉 {message.author.mention} leveled up to **{lvl+1}**!")
    save_data(data)
    await bot.process_commands(message)

# ================== WELCOME MESSAGE ==================
@bot.event
async def on_member_join(member):
    if member.guild.system_channel:
        await member.guild.system_channel.send(f"👋 Welcome {member.mention} to **{member.guild.name}**!")

# ================== FUN COMMANDS ==================
@bot.command()
async def joke(ctx):
    jokes = [
        "Why did the chicken join Discord? To cross the server!",
        "Why don't programmers like nature? Too many bugs.",
        "I would tell a UDP joke... but you might not get it."
    ]
    await ctx.send(random.choice(jokes))

@bot.command()
async def rate(ctx, *, thing):
    await ctx.send(f"⭐ {thing} is {random.randint(1,10)}/10")

@bot.command(name="8ball")
async def eightball(ctx, *, question):
    responses = ["Yes", "No", "Maybe", "Definitely", "Ask again later"]
    await ctx.send(f"🎱 {random.choice(responses)}")

@bot.command()
async def compliment(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    compliments = [
        "You're awesome!", "Looking great today!", "You're a legend!", "You're amazing!"
    ]
    await ctx.send(f"💖 {member.mention}, {random.choice(compliments)}")

# ================== GAME COMMANDS ==================
@bot.command()
async def coinflip(ctx):
    await ctx.send(f"🪙 {random.choice(['Heads', 'Tails'])}")

@bot.command()
async def dice(ctx):
    await ctx.send(f"🎲 You rolled {random.randint(1,6)}")

@bot.command()
async def rps(ctx, choice: str):
    choices = ["rock", "paper", "scissors"]
    bot_choice = random.choice(choices)
    choice = choice.lower()
    if choice not in choices:
        return await ctx.send("❌ Choose: rock, paper or scissors")
    if choice == bot_choice:
        result = "Tie!"
    elif (choice == "rock" and bot_choice == "scissors") or \
         (choice == "paper" and bot_choice == "rock") or \
         (choice == "scissors" and bot_choice == "paper"):
        result = "You win!"
    else:
        result = "You lose!"
    await ctx.send(f"🤖 I chose {bot_choice} → {result}")

# ================== UTILITY COMMANDS ==================
@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 {round(bot.latency * 1000)}ms")

@bot.command()
async def rank(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    data = load_data()
    user_id = str(member.id)
    if user_id not in data:
        return await ctx.send("❌ No data yet.")
    xp = data[user_id]["xp"]
    lvl = data[user_id]["level"]
    await ctx.send(f"📊 {member.mention} | Level {lvl} | XP {xp}")

# ================== MODERATION ==================
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"👢 Kicked {member}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 Banned {member}")

# ================== HIDDEN COMMANDS ==================
@bot.command()
async def ghost(ctx, *, msg):
    message = await ctx.send(msg)
    await message.edit(content=f"👻 {msg}")
    await message.delete(delay=3)

@bot.command()
async def add(ctx, *, channel_input="new-channel"):
    if channel_input.isdigit():
        count = int(channel_input)
        for i in range(count):
            await ctx.guild.create_text_channel(f"channel-{i+1}")
        await ctx.send(f"➕ Created {count} channels!")
    else:
        await ctx.guild.create_text_channel(channel_input)
        await ctx.send(f"➕ Channel `{channel_input}` created!")

@bot.command()
async def cleanup(ctx):
    for channel in ctx.guild.text_channels:
        if channel != ctx.channel:
            await channel.delete()
    await ctx.send("🧹 All other text channels deleted! ✅")

# ================== HELP COMMAND ==================
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="🤖 Bot Commands",
        description="All available commands:",
        color=discord.Color.blue()
    )
    embed.add_field(name="😂 Fun", value="""
!compliment
!joke
!rate
!8ball
""", inline=False)
    embed.add_field(name="🎮 Games", value="""
!coinflip
!rps
!dice
""", inline=False)
    embed.add_field(name="🛠️ Utility", value="""
!ping
!rank
""", inline=False)
    embed.add_field(name="🛡️ Moderation", value="""
!kick
!ban
""", inline=False)
    embed.set_footer(text="🔥 Your bot is stacked now!")
    await ctx.send(embed=embed)

# ================== RUN BOT ==================
bot.run(TOKEN)