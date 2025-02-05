import nextcord as discord
import pyautogui
import subprocess
import os
import keyboard
import time
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TRUSTED_USERS = list(map(int, os.getenv("TRUSTED_USERS").split(",")))

# Get screen resolution
screen_width, screen_height = pyautogui.size()

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Rate limit and cooldown tracking
user_last_command_time = {}
key_cooldowns = {}
KEY_COOLDOWN_TIME = 600  # 10 minutes

# Function to check cooldown
def is_key_on_cooldown(key_combination):
    if key_combination in key_cooldowns:
        last_used = key_cooldowns[key_combination]
        if time.time() - last_used < KEY_COOLDOWN_TIME:
            return True
    return False

# Function to register key cooldown
def register_key_cooldown(key_combination):
    key_cooldowns[key_combination] = time.time()

# Function to handle rate limiting
def can_execute_command(user_id):
    current_time = time.time()
    last_time = user_last_command_time.get(user_id, 0)
    if current_time - last_time < 2:  # 2-second cooldown per user
        return False
    user_last_command_time[user_id] = current_time
    return True

# Function to check if a URL is valid
def is_valid_url(url):
    url_regex = re.compile(
        r'^(https?:\/\/)?'  # http:// or https:// (optional)
        r'([\da-z\.-]+)\.([a-z\.]{2,6})'  # domain
        r'([\/\w \.-]*)*\/?$'  # path (optional)
    )
    return bool(url_regex.match(url))

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return  

    if message.author.id not in TRUSTED_USERS:
        await message.channel.send(f"❌ {message.author.mention}, you are untrusted and cannot use this bot.")
        return  

    command = message.content.lower()

    # Rate limiting check
    if not can_execute_command(message.author.id):
        await message.channel.send("❌ You're sending commands too quickly. Please wait a moment.")
        return

    if command.startswith("!mouse "):
        _, direction, *amount = command.split()
        move_amount = int(amount[0]) if amount else 25
        x, y = pyautogui.position()

        if direction == "up":
            y -= move_amount
        elif direction == "down":
            y += move_amount
        elif direction == "left":
            x -= move_amount
        elif direction == "right":
            x += move_amount
        else:
            await message.channel.send("❌ Invalid direction! Use `up`, `down`, `left`, or `right`.")
            return

        x = max(0, min(x, screen_width - 1))
        y = max(0, min(y, screen_height - 1))

        pyautogui.moveTo(x, y)
        await message.channel.send(f"Moved mouse to ({x}, {y})")

    elif command.startswith("!click"):
        pyautogui.click()
        await message.channel.send("🖱️ Clicked the mouse!")

    elif command.startswith("!type"):
        text = message.content[6:]
        pyautogui.write(text)
        await message.channel.send(f"Typed: `{text}`")

    elif command.startswith("!key "):
        key_combination = message.content[5:].strip()

        if key_combination in ["alt+f4", "win+l"]:
            if is_key_on_cooldown(key_combination):
                await message.channel.send(f"❌ `{key_combination}` can only be used once every 10 minutes. Try again later.")
                return

            try:
                keyboard.press_and_release(key_combination)
                register_key_cooldown(key_combination)
                await message.channel.send(f"Pressed keys: `{key_combination}`")
            except Exception as e:
                await message.channel.send(f"❌ Error: {str(e)}")
        else:
            try:
                keyboard.press_and_release(key_combination)
                await message.channel.send(f"Pressed keys: `{key_combination}`")
            except Exception as e:
                await message.channel.send(f"❌ Error: {str(e)}")

    elif command.startswith("!open "):
        url = message.content[6:].strip()

        # Check if the input is a valid URL
        if not is_valid_url(url):
            await message.channel.send(f"❌ `{url}` is not a valid URL. If you meant to search, try:\n🔎 https://www.google.com/search?q={url.replace(' ', '+')}")
            return

        try:
            chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"
            subprocess.run([chrome_path, url])
            await message.channel.send(f"🌐 Opening {url} in Google Chrome")
        except Exception as e:
            await message.channel.send(f"❌ Failed to open the website in Chrome. Error: {str(e)}")

    elif command.startswith("!help"):
        help_text = """
        **Bot Commands**:
        - `!mouse [up|down|left|right] [amount]` : Move the mouse in the specified direction.
        - `!click` : Click the mouse at the current position.
        - `!type [text]` : Type the specified text.
        - `!key [key combination]` : Press a key or combination (e.g., `alt+f4`, `win+l`).
        - `!open [url]` : Open the specified URL in Google Chrome.
        
        **Security & Limits**:
        - Commands are limited to 1 per 2 seconds per user.
        - `alt+f4` and `win+l` are restricted to one use per 10 minutes.
        - Untrusted users **cannot use the bot**.
        """
        await message.channel.send(help_text)

client.run(BOT_TOKEN)
