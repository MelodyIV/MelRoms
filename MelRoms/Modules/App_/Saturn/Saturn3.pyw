import sys
from pathlib import Path
import json
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
import ollama
import winsound
import asyncio
import discord
from discord.ext import commands
import base64
import io
import re

# ---------- HELPER: split long messages ----------
def split_long_message(text, limit=1900):
    """Split text into chunks of at most 'limit' characters, without breaking words."""
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
        split_at = text.rfind(' ', 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()
    return chunks

# ---------- CONFIG ----------
APP_NAME = "Saturn"
BASE_DIR = Path(__file__).parent
HISTORY_FILE = BASE_DIR / "chat_history.json"
SETTINGS_FILE = BASE_DIR / "settings.json"
MEMORY_FILE = BASE_DIR / "memory.json"
THEMES_DIR = BASE_DIR / "Themes"
THEMES_DIR.mkdir(exist_ok=True)

# ---------- DEFAULT SETTINGS ----------
DEFAULT_SETTINGS = {
    "model": "gemma3:4b",
    "system_prompt": (
        "You are Saturn, an exceptionally friendly, helpful, and kind AI companion. "
        "Your core personality is warm, supportive, and genuinely caring — like a wise, patient friend. "
        "Before every reply, you MUST read the Discord username provided at the start of the user's message (e.g., 'Username: @exampleuser'). "
        "Always address the user by that exact username at least once. "
        "Be accurate and honest. Never fabricate information."
    ),
    "sound_enabled": True,
    "theme": "dark_neon",
    "owner_id": 1047280353959743589
}

# ---------- DEFAULT FULL THEME (nested) ----------
DEFAULT_THEME = {
    "name": "Dark Neon",
    "colors": {
        "bg": "#05050A",
        "chat_bg": "#0A0A14",
        "user_bg": "#7B2CBF",
        "assistant_bg": "#1E1B2E",
        "text": "#E0D0FF",
        "accent": "#FF006E",
        "top_bg": "#0F0F1A",
        "scrollbar_bg": "#1A1A2E",
        "scrollbar_thumb": "#FF006E",
        "input_bg": "#1E1B2E",
        "input_fg": "#E0D0FF",
        "wave_color": "#FF006E"
    },
    "fonts": {
        "title_family": "Segoe UI",
        "title_size": 20,
        "title_weight": "bold",
        "chat_family": "Segoe UI",
        "chat_size": 12,
        "chat_weight": "normal",
        "input_family": "Segoe UI",
        "input_size": 13,
        "button_family": "Segoe UI",
        "button_size": 13,
        "button_weight": "bold",
        "thinking_family": "Segoe UI",
        "thinking_size": 12,
        "thinking_weight": "italic"
    },
    "sizes": {
        "top_bar_height": 55,
        "chat_padding_x": 15,
        "chat_padding_y": 10,
        "bubble_lmargin": 30,
        "bubble_rmargin": 30,
        "bubble_spacing1": 8,
        "bubble_spacing3": 8,
        "input_height": 85,
        "send_button_width": 110,
        "scrollbar_width": 12
    },
    "corners": {
        "button_radius": 8,
        "input_radius": 8,
        "top_bar_radius": 0
    },
    "bubble_style": {
        "user_bubble_bold": True,
        "assistant_bubble_bold": False,
        "user_text_color": "#FFFFFF",
        "assistant_text_color": "#E0D0FF"
    }
}

def deep_merge(base, update):
    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base

def load_theme(theme_name):
    theme_path = THEMES_DIR / f"{theme_name}.json"
    theme = DEFAULT_THEME.copy()
    if theme_path.exists():
        try:
            with open(theme_path, "r") as f:
                user_theme = json.load(f)
                deep_merge(theme, user_theme)
        except Exception as e:
            print(f"Theme load error: {e}")
    return theme

class SaturnDiscordBot:
    def __init__(self, parent_app, token):
        self.parent = parent_app
        self.token = token
        self.bot = None
        self.loop = None
        self.thread = None
        self.running = False
        self.owner_id = self.parent.settings.get("owner_id", 0)
        self.log_file = BASE_DIR / "dm_log.txt"
        self.channel_id = 1490763568659038309   # Designated channel for $ chat
        self.memory = {"facts": [], "mappings": {}}   # mappings kept for compatibility but not used for @mentions
        self.load_memory()

    def load_memory(self):
        if MEMORY_FILE.exists():
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    self.memory = json.load(f)
            except:
                self.memory = {"facts": [], "mappings": {}}
        else:
            self.memory = {"facts": [], "mappings": {}}

    def save_memory(self):
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, indent=2)

    def log(self, text):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{text}\n")
        print(text)

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_bot, daemon=True)
        self.thread.start()

    def _build_system_prompt(self):
        """Construct the system prompt using the user's custom prompt + memory facts."""
        base_prompt = self.parent.settings.get("system_prompt", DEFAULT_SETTINGS["system_prompt"])
        
        # Add memory facts with strong precedence instruction
        if self.memory["facts"]:
            facts_block = "\n".join(f"- {fact}" for fact in self.memory["facts"])
            memory_section = (
                f"\n\n**IMPORTANT MEMORY FACTS:**\n"
                f"The following facts are ALWAYS TRUE and take precedence over any other knowledge:\n"
                f"{facts_block}\n"
                f"Never contradict these facts."
            )
            return base_prompt + memory_section
        
        return base_prompt

    def _clean_content_for_context(self, content):
        """Remove Discord mention syntax from content before sending to the model."""
        content = re.sub(r'<@!?(\d+)>', r'@user', content)
        return content

    def _format_user_message(self, display_name, content):
        """Format a user message to match the expected 'Username: @name' pattern."""
        return f"Username: @{display_name}\n{content}"

    def _run_bot(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix="!", intents=intents)

        # ========== SLASH COMMAND: /ask ==========
        @self.bot.tree.command(name="ask", description="Ask Saturn a question (optionally with an image)")
        @discord.app_commands.allowed_installs(guilds=True, users=True)
        @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
        async def ask(interaction: discord.Interaction, question: str, image: discord.Attachment = None):
            await interaction.response.defer(thinking=True)
            display_name = interaction.user.display_name
            clean_question = self._clean_content_for_context(question)
            formatted_question = self._format_user_message(display_name, clean_question)

            images_b64 = []
            if image and image.content_type and image.content_type.startswith('image/'):
                try:
                    img_bytes = await image.read()
                    b64_img = base64.b64encode(img_bytes).decode('utf-8')
                    images_b64.append(b64_img)
                except Exception as e:
                    print(f"Image read error: {e}")

            # Build history (already formatted with Username: @name)
            history = []
            if interaction.channel:
                try:
                    async for msg in interaction.channel.history(limit=10):
                        if msg.author == self.bot.user:
                            role = "assistant"
                            content = msg.content
                        else:
                            role = "user"
                            author_name = msg.author.display_name
                            clean_content = self._clean_content_for_context(msg.content) if msg.content else "[image]"
                            content = self._format_user_message(author_name, clean_content)
                        history.append({"role": role, "content": content})
                    history.reverse()
                except:
                    pass

            messages = [{"role": "system", "content": self._build_system_prompt()}]
            messages.extend(history)
            user_msg = {"role": "user", "content": formatted_question}
            if images_b64:
                user_msg["images"] = images_b64
            messages.append(user_msg)

            full_response = ""
            try:
                stream = ollama.chat(model=self.parent.current_model, messages=messages, stream=True)
                for chunk in stream:
                    full_response += chunk["message"]["content"]
            except Exception as e:
                full_response = f"💔 Error: {e}"

            # Display in UI
            display_prompt = f"[Discord] {display_name}: {question}"
            if image:
                display_prompt += " [🖼️ Image]"
            self.parent.add_conversation_entry("user", question, source="discord", display_extra=display_prompt, username=display_name)
            self.parent.add_conversation_entry("assistant", full_response, source="discord")

            chunks = split_long_message(full_response)
            await interaction.followup.send(chunks[0])
            for chunk in chunks[1:]:
                await interaction.channel.send(chunk)

        # ========== MESSAGE EVENT ==========
        @self.bot.event
        async def on_message(message):
            if message.author == self.bot.user:
                return

            # ---------- GLOBAL HELP ----------
            if message.content.startswith('!help'):
                help_text = (
                    "**🌙 Saturn Commands**\n\n"
                    "**Slash Command (works anywhere):**\n"
                    "`/ask <question>` – Ask Saturn anything (text or image)\n\n"
                    "**Prefix Commands (use !):**\n"
                    "`!pyread` – Read an attached `.py` file\n"
                    "`!pyedit <instructions>` – Edit an attached `.py` file using AI\n"
                    "`!help` – Show this help message\n\n"
                    "**Owner-only commands:**\n"
                    "`!dm @user <message>` – Send a DM\n"
                    "`!test` – Test owner detection\n"
                    "`!remember <fact>` – Teach Saturn a fact\n"
                    "`!forget <fact>` – Remove a fact\n"
                    "`!map <name> @user` – Map a name (for memory)\n"
                    "`!unmap <name>` – Remove a name mapping\n"
                    "`!memory` – List all stored memories\n\n"
                    "**Normal Chat:**\n"
                    "In the designated channel, start with `$` or reply directly to me. DMs are open!"
                )
                await message.channel.send(help_text)
                return

            # ---------- FILE READING / EDITING ----------
            if message.content.startswith('!pyread'):
                if not message.attachments:
                    await message.channel.send("❌ Please attach a `.py` file to read.")
                    return
                attachment = message.attachments[0]
                if not attachment.filename.endswith('.py'):
                    await message.channel.send("❌ Only `.py` files are supported.")
                    return
                await message.channel.send("📖 Reading file...")
                file_content = (await attachment.read()).decode('utf-8')
                chunks = [file_content[i:i+1900] for i in range(0, len(file_content), 1900)]
                for i, chunk in enumerate(chunks):
                    code_block = f"```python\n{chunk}\n```"
                    await message.channel.send(f"**{attachment.filename}** part {i+1}/{len(chunks)}:\n{code_block}")
                if not chunks:
                    await message.channel.send("(File is empty)")
                return

            if message.content.startswith('!pyedit'):
                if not message.attachments:
                    await message.channel.send("❌ Please attach a `.py` file to edit.")
                    return
                attachment = message.attachments[0]
                if not attachment.filename.endswith('.py'):
                    await message.channel.send("❌ Only `.py` files are supported.")
                    return
                instruction = message.content[7:].strip()
                if not instruction:
                    await message.channel.send("❌ Please provide editing instructions. Example: `!pyedit add a function that prints hello`")
                    return
                await message.channel.send("📖 Reading your Python file and applying changes...")
                file_content = (await attachment.read()).decode('utf-8')
                prompt_file = BASE_DIR / "edit_instruction.txt"
                if prompt_file.exists():
                    system_edit_prompt = prompt_file.read_text(encoding="utf-8").strip()
                else:
                    system_edit_prompt = (
                        "You are an expert Python programmer. Modify the given code exactly as instructed.\n"
                        "Return ONLY the complete modified code, no explanations, no markdown formatting, just the raw code."
                    )
                msgs = [
                    {"role": "system", "content": system_edit_prompt},
                    {"role": "user", "content": f"INSTRUCTION: {instruction}\n\nORIGINAL CODE:\n```python\n{file_content}\n```"}
                ]
                full_response = ""
                try:
                    stream = ollama.chat(model=self.parent.current_model, messages=msgs, stream=True)
                    for chunk in stream:
                        full_response += chunk["message"]["content"]
                except Exception as e:
                    await message.channel.send(f"💔 LLM error: {e}")
                    return
                if full_response.startswith("```python"):
                    full_response = full_response[9:]
                if full_response.startswith("```"):
                    full_response = full_response[3:]
                if full_response.endswith("```"):
                    full_response = full_response[:-3]
                full_response = full_response.strip()
                if not full_response:
                    await message.channel.send("❌ The LLM returned an empty response. Please try again.")
                    return
                output_filename = f"edited_{attachment.filename}"
                output_bytes = full_response.encode('utf-8')
                file_obj = io.BytesIO(output_bytes)
                discord_file = discord.File(file_obj, filename=output_filename)
                await message.channel.send(f"✅ Edited `{attachment.filename}` according to: `{instruction[:50]}...`", file=discord_file)
                return

            # ---------- OWNER COMMANDS ----------
            if message.author.id == self.owner_id and message.content.startswith('!'):
                self.log(f"Owner command: {message.content}")
                if message.content.startswith('!test'):
                    await message.channel.send("✅ Owner command works! Your ID is correct.")
                    return

                if message.content.startswith('!dm'):
                    parts = message.content.split(maxsplit=2)
                    if len(parts) < 3:
                        await message.channel.send("Usage: `!dm @user <message>` or `!dm user_id <message>`")
                        return
                    target_input = parts[1]
                    msg_text = parts[2]
                    target_user = None
                    if target_input.startswith('<@') and target_input.endswith('>'):
                        user_id = int(target_input.strip('<@!>'))
                        try:
                            target_user = await self.bot.fetch_user(user_id)
                        except discord.NotFound:
                            await message.channel.send("❌ User not found.")
                            return
                    elif target_input.isdigit():
                        try:
                            target_user = await self.bot.fetch_user(int(target_input))
                        except discord.NotFound:
                            await message.channel.send("❌ User not found.")
                            return
                    else:
                        await message.channel.send("Invalid user. Use a mention or numeric ID.")
                        return
                    try:
                        dm_channel = await target_user.create_dm()
                        await dm_channel.send(f"📨 **Saturn says:** {msg_text}")
                        await message.channel.send(f"✅ DM sent to {target_user.name}")
                        self.log(f"DM sent to {target_user.name}")
                    except discord.Forbidden:
                        await message.channel.send(f"❌ Cannot DM {target_user.name}")
                    except Exception as e:
                        await message.channel.send(f"❌ Error: {e}")
                    return

                # Memory commands
                if message.content.startswith('!remember '):
                    fact = message.content[9:].strip()
                    if fact and fact not in self.memory["facts"]:
                        self.memory["facts"].append(fact)
                        self.save_memory()
                        await message.channel.send(f"🧠 I'll remember: *{fact}*")
                    else:
                        await message.channel.send("I already know that or it's empty!")
                    return

                if message.content.startswith('!forget '):
                    fact = message.content[8:].strip()
                    if fact in self.memory["facts"]:
                        self.memory["facts"].remove(fact)
                        self.save_memory()
                        await message.channel.send(f"🗑️ Forgotten: *{fact}*")
                    else:
                        await message.channel.send("I don't remember that fact.")
                    return

                if message.content.startswith('!map '):
                    parts = message.content.split(maxsplit=2)
                    if len(parts) < 3:
                        await message.channel.send("Usage: `!map <name> @user`")
                        return
                    name = parts[1].lower()
                    mention = parts[2].strip()
                    user_id = None
                    if mention.startswith('<@') and mention.endswith('>'):
                        user_id = mention.strip('<@!>')
                    else:
                        await message.channel.send("Please mention a user with @.")
                        return
                    self.memory["mappings"][name] = user_id
                    self.save_memory()
                    await message.channel.send(f"🔗 Mapped `{name}` to <@{user_id}>")
                    return

                if message.content.startswith('!unmap '):
                    name = message.content[7:].strip().lower()
                    if name in self.memory["mappings"]:
                        del self.memory["mappings"][name]
                        self.save_memory()
                        await message.channel.send(f"🔓 Unmapped `{name}`")
                    else:
                        await message.channel.send(f"No mapping for `{name}`.")
                    return

                if message.content.startswith('!memory'):
                    facts = "\n".join(f"• {f}" for f in self.memory["facts"]) or "(none)"
                    maps = "\n".join(f"• {k} → <@{v}>" for k, v in self.memory["mappings"].items()) or "(none)"
                    await message.channel.send(f"**🧠 Facts:**\n{facts}\n\n**🔗 Mappings:**\n{maps}")
                    return

            # ---------- NATURAL LANGUAGE DM VIA MENTION ----------
            if self.bot.user in message.mentions and not message.author.bot:
                content = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
                if content.lower().startswith('dm'):
                    parts = content.split(maxsplit=2)
                    if len(parts) >= 3:
                        target_mention = parts[1]
                        msg_text = parts[2]
                        target_user = None
                        if target_mention.startswith('<@') and target_mention.endswith('>'):
                            user_id = int(target_mention.strip('<@!>'))
                            try:
                                target_user = await self.bot.fetch_user(user_id)
                            except:
                                await message.channel.send("❌ Couldn't find that user.")
                                return
                        else:
                            await message.channel.send("❌ Please mention a user like `@username`.")
                            return
                        try:
                            dm_channel = await target_user.create_dm()
                            sender_name = message.author.display_name
                            await dm_channel.send(f"📨 **Message from {sender_name} via Saturn:**\n{msg_text}")
                            await message.channel.send(f"✅ DM sent to {target_user.name}!")
                        except Exception as e:
                            await message.channel.send(f"❌ Failed to send DM: {e}")
                    else:
                        await message.channel.send("Usage: `@Saturn dm @user your message`")
                    return

            # ---------- NORMAL CHAT RESPONSE ----------
            is_dm = isinstance(message.channel, discord.DMChannel)
            is_designated_channel = message.channel.id == self.channel_id

            # Check for reply to bot in designated channel
            is_reply_to_bot = False
            if not is_dm and is_designated_channel and message.reference:
                try:
                    ref_msg = await message.channel.fetch_message(message.reference.message_id)
                    if ref_msg.author == self.bot.user:
                        is_reply_to_bot = True
                except:
                    pass

            # Determine if we should respond
            should_respond = False
            if is_dm:
                should_respond = True
            elif is_designated_channel:
                if message.content.startswith('$') or is_reply_to_bot:
                    should_respond = True

            if not should_respond:
                return

            prompt = message.content.strip()
            if prompt.startswith('$'):
                prompt = prompt[1:].strip()

            # Extract only image attachments
            images_b64 = []
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    try:
                        img_bytes = await attachment.read()
                        b64_img = base64.b64encode(img_bytes).decode('utf-8')
                        images_b64.append(b64_img)
                    except Exception as e:
                        print(f"Error reading image attachment: {e}")

            # Handle empty prompt
            if not prompt and not images_b64:
                if message.attachments:
                    await message.channel.send(
                        "🌙 I can only see image files right now. "
                        "If you'd like me to read a Python file, use `!pyread` or `!pyedit`!"
                    )
                return

            if not prompt and images_b64:
                prompt = "What do you see in this image?"

            display_name = message.author.display_name
            clean_prompt = self._clean_content_for_context(prompt)
            formatted_prompt = self._format_user_message(display_name, clean_prompt)

            async with message.channel.typing():
                # Build history with proper formatting
                history = []
                async for msg in message.channel.history(limit=10):
                    if msg.author == self.bot.user:
                        role = "assistant"
                        content = msg.content
                    else:
                        role = "user"
                        author_name = msg.author.display_name
                        clean_content = self._clean_content_for_context(msg.content) if msg.content else "[image]"
                        content = self._format_user_message(author_name, clean_content)
                    history.append({"role": role, "content": content})
                history.reverse()

                messages = [{"role": "system", "content": self._build_system_prompt()}]
                messages.extend(history)
                user_msg = {"role": "user", "content": formatted_prompt}
                if images_b64:
                    user_msg["images"] = images_b64
                messages.append(user_msg)

                full_response = ""
                try:
                    stream = ollama.chat(model=self.parent.current_model, messages=messages, stream=True)
                    for chunk in stream:
                        full_response += chunk["message"]["content"]
                except Exception as e:
                    full_response = f"💔 Error: {e}"

                # NOTE: @mention replacement has been removed per user request

                # Display in UI
                display_prompt = f"[Discord] {display_name}: {prompt}"
                if images_b64:
                    display_prompt += " [🖼️ Image]"
                self.parent.add_conversation_entry("user", prompt, source="discord", display_extra=display_prompt, username=display_name)
                self.parent.add_conversation_entry("assistant", full_response, source="discord")

                chunks = split_long_message(full_response)
                if is_dm:
                    await message.channel.send(chunks[0])
                else:
                    await message.reply(chunks[0])
                for chunk in chunks[1:]:
                    await message.channel.send(chunk)
                print(f"Replied to: {prompt[:50]}...")

        @self.bot.event
        async def on_ready():
            print(f'✅ Discord bot logged in as {self.bot.user}')
            print(f"Owner ID set to: {self.owner_id}")
            if self.owner_id == 0:
                print("⚠️ WARNING: Owner ID is 0 – owner commands will not work!")
            try:
                await self.bot.tree.sync()
                print("Slash commands synced.")
            except Exception as e:
                print(f"Sync error: {e}")

            channel = self.bot.get_channel(self.channel_id)
            if channel:
                startup_msg = (
                    "```\n"
                    r"  ____    _   _____  _   _  ____   _   _ " "\n"
                    r" / ___|  / \ |_   _|| | | ||  _ \ | \ | |" "\n"
                    r" \___ \ / _ \  | |  | | | || |_) ||  \| |" "\n"
                    r"  ___) / ___ \ | |  | |_| ||  _ < | |\  |" "\n"
                    r" |____/_/   \_\|_|   \___/ |_| \_\|_| \_|" "\n"
                    " ___________________________________________ \n"
                    "| ::: S Y S T E M  O P E R A T I O N S ::: |\n"
                    "```\n"
                    "🪐✨ **Saturn is online and ready to chat!** ✨🌙  \n"
                    "Use `/ask`, `$`, or reply directly to me in this channel. DMs are open! 💫"
                )
                try:
                    await channel.send(startup_msg)
                    print("Startup message sent to Discord.")
                except Exception as e:
                    print(f"Failed to send startup message: {e}")
            else:
                print(f"⚠️ Could not find channel {self.channel_id} for startup message.")

        try:
            self.loop.run_until_complete(self.bot.start(self.token))
        except Exception as e:
            print(f"Discord bot error: {e}")
        finally:
            self.running = False

    def stop(self):
        self.running = False
        if self.bot and self.loop:
            asyncio.run_coroutine_threadsafe(self.bot.close(), self.loop)


# ---------- TKINTER UI (unchanged except minor adjustments for consistency) ----------
class SaturnApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.load_settings()
        self.current_theme = load_theme(self.settings.get("theme", "dark_neon"))
        self.title(APP_NAME)
        self.geometry("1100x750")
        self.minsize(900, 600)

        self.current_model = self.settings.get("model", DEFAULT_SETTINGS["model"])
        self.history = []
        self.generating = False
        self.stream_text = ""
        self.typing_after = None
        self.attached_images = []

        self.load_history()
        self._build_ui()
        self._preload_model()
        self.refresh_model_list()

        self.discord_bot = None
        self._start_discord_bot()

        for msg in self.history[-30:]:
            display = msg.get("display", msg["content"])
            if msg.get("source") == "discord" and msg["role"] == "user":
                display = f"[Discord] {msg.get('username', 'User')}: {msg['content']}"
            self._add_bubble(msg["role"], display)

    # ---------- SETTINGS & HISTORY ----------
    def load_settings(self):
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r") as f:
                self.settings = json.load(f)
        else:
            self.settings = DEFAULT_SETTINGS.copy()

    def save_settings(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f, indent=2)

    def load_history(self):
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, "r") as f:
                self.history = json.load(f)
        else:
            self.history = []

    def save_history(self):
        with open(HISTORY_FILE, "w") as f:
            json.dump(self.history, f, indent=2)

    def _start_discord_bot(self):
        token_file = BASE_DIR / "discord_token.txt"
        if not token_file.exists():
            print("⚠️ No discord_token.txt – Discord bot disabled.")
            return
        token = token_file.read_text().strip()
        if not token:
            return
        self.discord_bot = SaturnDiscordBot(self, token)
        self.discord_bot.start()

    # ---------- MODEL MANAGEMENT ----------
    def refresh_model_list(self):
        def fetch():
            try:
                models_info = ollama.list()
                models = [m["model"] for m in models_info.get("models", [])]
                if self.current_model not in models:
                    models.insert(0, self.current_model)
                self.after(0, lambda: self._update_model_menu(models))
            except Exception as e:
                print(f"Error fetching models: {e}")
                self.after(0, lambda: self._update_model_menu([self.current_model]))
        threading.Thread(target=fetch, daemon=True).start()

    def _update_model_menu(self, model_list):
        self.model_menu.configure(values=model_list)
        if self.current_model not in model_list:
            self.current_model = model_list[0] if model_list else "gemma3:4b"
            self.model_var.set(self.current_model)
            self.settings["model"] = self.current_model
            self.save_settings()
        else:
            self.model_var.set(self.current_model)

    def change_model(self, choice):
        self.current_model = choice
        self.settings["model"] = choice
        self.save_settings()
        self.update_status(f"Model set to {choice}")
        def ensure_model():
            try:
                models = [m["model"] for m in ollama.list().get("models", [])]
                if choice not in models:
                    self.after(0, lambda: self.update_status(f"Pulling {choice}...", timeout=0))
                    subprocess.run(["ollama", "pull", choice], check=False)
                    self.after(0, lambda: self.update_status(f"{choice} ready", timeout=2))
            except Exception as e:
                print(f"Model pull error: {e}")
        threading.Thread(target=ensure_model, daemon=True).start()

    # ---------- UI BUILD ----------
    def _prevent_edit(self, event):
        if event.state & 0x4:
            if event.keysym.lower() in ('c', 'a'):
                return None
            elif event.keysym.lower() == 'v':
                return "break"
            return "break"
        allowed = (
            "Left", "Right", "Up", "Down",
            "Home", "End", "PageUp", "PageDown", "Prior", "Next",
            "Shift_L", "Shift_R", "Control_L", "Control_R",
            "Alt_L", "Alt_R", "Meta_L", "Meta_R"
        )
        if event.keysym in allowed:
            return None
        return "break"

    def _set_chat_readonly(self):
        self.chat_text.config(state="normal")
        self.chat_text.bind("<Key>", self._prevent_edit)
        self.chat_text.bind("<<Paste>>", lambda e: "break")
        self.chat_text.bind("<<Cut>>", lambda e: "break")

    def attach_image(self):
        file_paths = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("All files", "*.*")
            ]
        )
        for path in file_paths:
            try:
                with open(path, "rb") as f:
                    img_bytes = f.read()
                b64_img = base64.b64encode(img_bytes).decode('utf-8')
                self.attached_images.append(b64_img)
                self.input_text.insert("end", f"\n[🖼️ {Path(path).name} attached]")
            except Exception as e:
                print(f"Error loading image {path}: {e}")

    def add_conversation_entry(self, role, content, source="local", display_extra=None, username=None):
        self.after(0, lambda: self._add_entry_ui(role, content, source, display_extra, username))

    def _add_entry_ui(self, role, content, source, display_extra, username):
        entry = {
            "role": role,
            "content": content,
            "source": source,
            "display": display_extra if display_extra else content
        }
        if username:
            entry["username"] = username
        self.history.append(entry)
        self.save_history()

        if display_extra:
            display_text = display_extra
        elif source == "discord" and role == "user":
            display_text = f"[Discord] {username or 'User'}: {content}"
        else:
            display_text = content

        self.chat_text.config(state="normal")
        if self.chat_text.index("end-1c") != "1.0":
            self.chat_text.insert("end", "\n")
        self.chat_text.insert("end", display_text + "\n", (role,))
        self._set_chat_readonly()
        self.chat_text.see("end")

        if self.sound_var.get() and not self.generating:
            winsound.MessageBeep(winsound.MB_OK)

    def _build_ui(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.configure(bg=self.current_theme["colors"]["bg"])
        top = ctk.CTkFrame(self, height=self.current_theme["sizes"]["top_bar_height"], fg_color=self.current_theme["colors"]["top_bg"], corner_radius=self.current_theme["corners"]["top_bar_radius"])
        top.pack(fill="x")
        title_font = (self.current_theme["fonts"]["title_family"], self.current_theme["fonts"]["title_size"], self.current_theme["fonts"]["title_weight"])
        ctk.CTkLabel(top, text="🪐 Saturn", font=title_font, text_color=self.current_theme["colors"]["accent"]).pack(side="left", padx=20)

        model_frame = ctk.CTkFrame(top, fg_color="transparent")
        model_frame.pack(side="left", padx=(20, 5))
        ctk.CTkLabel(model_frame, text="Model:", font=("Segoe UI", 12), text_color=self.current_theme["colors"]["text"]).pack(side="left")
        self.model_var = ctk.StringVar(value=self.current_model)
        self.model_menu = ctk.CTkOptionMenu(model_frame, variable=self.model_var, values=[self.current_model], command=self.change_model,
                                            fg_color=self.current_theme["colors"]["input_bg"], button_color=self.current_theme["colors"]["accent"],
                                            text_color=self.current_theme["colors"]["text"], corner_radius=self.current_theme["corners"]["button_radius"])
        self.model_menu.pack(side="left", padx=5)
        ctk.CTkButton(model_frame, text="🔄", width=30, command=self.refresh_model_list,
                      fg_color=self.current_theme["colors"]["assistant_bg"], hover_color=self.current_theme["colors"]["accent"],
                      text_color=self.current_theme["colors"]["text"], corner_radius=self.current_theme["corners"]["button_radius"]).pack(side="left", padx=(5,0))

        theme_names = [f.stem for f in THEMES_DIR.glob("*.json")] or ["dark_neon"]
        self.theme_var = ctk.StringVar(value=self.settings.get("theme", "dark_neon"))
        self.theme_menu = ctk.CTkOptionMenu(top, variable=self.theme_var, values=theme_names, command=self.change_theme,
                                            fg_color=self.current_theme["colors"]["input_bg"], button_color=self.current_theme["colors"]["accent"],
                                            text_color=self.current_theme["colors"]["text"], corner_radius=self.current_theme["corners"]["button_radius"])
        self.theme_menu.pack(side="left", padx=10)

        ctk.CTkButton(top, text="🗑️ Clear", command=self.new_chat, fg_color=self.current_theme["colors"]["user_bg"],
                      hover_color=self.current_theme["colors"]["accent"], text_color=self.current_theme["colors"]["text"],
                      corner_radius=self.current_theme["corners"]["button_radius"]).pack(side="left", padx=5)
        self.sound_var = ctk.BooleanVar(value=self.settings.get("sound_enabled", True))
        ctk.CTkButton(top, text="🔊", width=45, command=self.toggle_sound, fg_color=self.current_theme["colors"]["assistant_bg"],
                      text_color=self.current_theme["colors"]["text"], corner_radius=self.current_theme["corners"]["button_radius"]).pack(side="right", padx=10)

        chat_container = tk.Frame(self, bg=self.current_theme["colors"]["chat_bg"])
        chat_container.pack(fill="both", expand=True, padx=self.current_theme["sizes"]["chat_padding_x"], pady=self.current_theme["sizes"]["chat_padding_y"])
        chat_font = (self.current_theme["fonts"]["chat_family"], self.current_theme["fonts"]["chat_size"], self.current_theme["fonts"]["chat_weight"])
        self.chat_text = tk.Text(chat_container, wrap="word", font=chat_font, bg=self.current_theme["colors"]["chat_bg"],
                                 fg=self.current_theme["colors"]["text"], relief="flat", borderwidth=0, padx=15, pady=10,
                                 selectbackground=self.current_theme["colors"]["accent"])
        scrollbar = tk.Scrollbar(chat_container, command=self.chat_text.yview, bg=self.current_theme["colors"]["scrollbar_bg"],
                                 troughcolor=self.current_theme["colors"]["chat_bg"], activebackground=self.current_theme["colors"]["accent"],
                                 width=self.current_theme["sizes"]["scrollbar_width"])
        self.chat_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.chat_text.pack(side="left", fill="both", expand=True)

        user_font = (self.current_theme["fonts"]["chat_family"], self.current_theme["fonts"]["chat_size"], "bold" if self.current_theme["bubble_style"]["user_bubble_bold"] else "normal")
        self.chat_text.tag_config("user", background=self.current_theme["colors"]["user_bg"], foreground=self.current_theme["bubble_style"]["user_text_color"],
                                  font=user_font, lmargin1=self.current_theme["sizes"]["bubble_lmargin"], lmargin2=self.current_theme["sizes"]["bubble_lmargin"],
                                  rmargin=self.current_theme["sizes"]["bubble_rmargin"], spacing1=self.current_theme["sizes"]["bubble_spacing1"],
                                  spacing3=self.current_theme["sizes"]["bubble_spacing3"])
        assistant_font = (self.current_theme["fonts"]["chat_family"], self.current_theme["fonts"]["chat_size"], "bold" if self.current_theme["bubble_style"]["assistant_bubble_bold"] else "normal")
        self.chat_text.tag_config("assistant", background=self.current_theme["colors"]["assistant_bg"], foreground=self.current_theme["bubble_style"]["assistant_text_color"],
                                  font=assistant_font, lmargin1=self.current_theme["sizes"]["bubble_lmargin"], lmargin2=self.current_theme["sizes"]["bubble_lmargin"],
                                  rmargin=self.current_theme["sizes"]["bubble_rmargin"], spacing1=self.current_theme["sizes"]["bubble_spacing1"],
                                  spacing3=self.current_theme["sizes"]["bubble_spacing3"])
        thinking_font = (self.current_theme["fonts"]["thinking_family"], self.current_theme["fonts"]["thinking_size"], self.current_theme["fonts"]["thinking_weight"])
        self.chat_text.tag_config("thinking", foreground=self.current_theme["colors"]["accent"], font=thinking_font, lmargin1=self.current_theme["sizes"]["bubble_lmargin"], spacing1=5)
        self.chat_text.tag_config("typing", foreground=self.current_theme["colors"]["accent"], font=thinking_font, lmargin1=self.current_theme["sizes"]["bubble_lmargin"], spacing1=5)

        self._set_chat_readonly()

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=20, pady=(0,15))

        input_font = (self.current_theme["fonts"]["input_family"], self.current_theme["fonts"]["input_size"])
        self.input_text = ctk.CTkTextbox(bottom, height=self.current_theme["sizes"]["input_height"], font=input_font,
                                         fg_color=self.current_theme["colors"]["input_bg"], text_color=self.current_theme["colors"]["input_fg"],
                                         border_width=0, corner_radius=self.current_theme["corners"]["input_radius"])
        self.input_text.pack(side="left", fill="x", expand=True, padx=(0,10))
        self.input_text.bind("<Control-Return>", lambda e: self.send())

        button_font = (self.current_theme["fonts"]["button_family"], self.current_theme["fonts"]["button_size"], self.current_theme["fonts"]["button_weight"])
        ctk.CTkButton(bottom, text="🖼️ Attach", width=90, fg_color=self.current_theme["colors"]["assistant_bg"], hover_color=self.current_theme["colors"]["accent"],
                      text_color=self.current_theme["colors"]["text"], font=button_font, corner_radius=self.current_theme["corners"]["button_radius"],
                      command=self.attach_image).pack(side="left", padx=(0,5))
        ctk.CTkButton(bottom, text="✨ Send ✨", width=self.current_theme["sizes"]["send_button_width"], fg_color=self.current_theme["colors"]["accent"],
                      hover_color=self.current_theme["colors"]["user_bg"], text_color="#FFFFFF", font=button_font,
                      corner_radius=self.current_theme["corners"]["button_radius"], command=self.send).pack(side="left")

        self.update_status("Ready")

    def change_theme(self, theme_name):
        self.settings["theme"] = theme_name
        self.save_settings()
        self.current_theme = load_theme(theme_name)
        self._build_ui()
        for msg in self.history[-30:]:
            display = msg.get("display", msg["content"])
            if msg.get("source") == "discord" and msg["role"] == "user":
                display = f"[Discord] {msg.get('username', 'User')}: {msg['content']}"
            self._add_bubble(msg["role"], display)
        self.update_status(f"Theme: {self.current_theme['name']}")

    def toggle_sound(self):
        self.sound_var.set(not self.sound_var.get())
        self.settings["sound_enabled"] = self.sound_var.get()
        self.save_settings()

    def update_status(self, msg, timeout=2):
        self.title(f"{APP_NAME} – {msg}")
        if timeout:
            self.after(timeout*1000, lambda: self.title(APP_NAME))

    def _add_bubble(self, role, content):
        self.chat_text.config(state="normal")
        if self.chat_text.index("end-1c") != "1.0":
            self.chat_text.insert("end", "\n")
        self.chat_text.insert("end", content + "\n", (role,))
        self._set_chat_readonly()
        self.chat_text.see("end")

    def _show_thinking(self):
        self._remove_temp_markers()
        self.chat_text.config(state="normal")
        self.thinking_start = self.chat_text.index("end-1c")
        self.chat_text.insert("end", "✨ Saturn is thinking... ✨\n", ("thinking",))
        self._set_chat_readonly()
        self.chat_text.see("end")

    def _show_typing(self):
        self._remove_temp_markers()
        self.chat_text.config(state="normal")
        self.typing_start = self.chat_text.index("end-1c")
        self.chat_text.insert("end", "Saturn is writing", ("typing",))
        self._set_chat_readonly()
        self.chat_text.see("end")
        self._animate_typing()

    def _animate_typing(self, count=0):
        if not hasattr(self, 'typing_start') or not self.typing_start:
            return
        try:
            self.chat_text.config(state="normal")
            dots = "." * ((count % 3) + 1)
            end = self.chat_text.index("end-1c")
            self.chat_text.delete(self.typing_start, end)
            self.chat_text.insert(self.typing_start, f"Saturn is writing{dots}\n", ("typing",))
            self._set_chat_readonly()
            self.chat_text.see("end")
            self.typing_after = self.after(500, lambda: self._animate_typing(count+1))
        except:
            pass

    def _remove_temp_markers(self):
        if hasattr(self, 'typing_after') and self.typing_after:
            self.after_cancel(self.typing_after)
            self.typing_after = None
        for attr in ['thinking_start', 'typing_start']:
            if hasattr(self, attr) and getattr(self, attr):
                try:
                    self.chat_text.config(state="normal")
                    end = self.chat_text.index("end-1c")
                    self.chat_text.delete(getattr(self, attr), end)
                    setattr(self, attr, None)
                    self._set_chat_readonly()
                except:
                    pass

    def _play_ding(self):
        if self.sound_var.get():
            winsound.MessageBeep(winsound.MB_OK)

    def send(self):
        text = self.input_text.get("1.0", tk.END).strip()
        if not text and not self.attached_images:
            return
        if self.generating:
            return

        display_text = text
        if self.attached_images:
            if display_text:
                display_text += "\n[🖼️ Image attached]"
            else:
                display_text = "[🖼️ Image attached]"

        self._add_bubble("user", display_text)
        entry = {"role": "user", "content": text if text else "[Image]", "source": "local", "display": display_text}
        self.history.append(entry)
        self.save_history()

        self.input_text.delete("1.0", tk.END)
        self._start_assistant()

    def _start_assistant(self):
        self.generating = True
        self.stream_text = ""
        self._show_thinking()
        threading.Thread(target=self._stream, daemon=True).start()

    def _stream(self):
        try:
            messages = [{"role": "system", "content": self.settings.get("system_prompt", DEFAULT_SETTINGS["system_prompt"])}]
            history_slice = self.history[-20:]
            for i, entry in enumerate(history_slice):
                role = entry["role"]
                content = entry["content"]
                is_last = (i == len(history_slice) - 1)
                if role == "user" and entry.get("source") == "local":
                    content = f"Username: @Melody\n{content}"
                msg = {"role": role, "content": content}
                if is_last and role == "user" and entry.get("source") == "local" and self.attached_images:
                    msg["images"] = self.attached_images.copy()
                messages.append(msg)

            stream = ollama.chat(model=self.current_model, messages=messages, stream=True)
            self.after(0, self._remove_temp_markers)
            self.after(0, self._show_typing)
            for chunk in stream:
                if not self.generating:
                    break
                self.stream_text += chunk["message"]["content"]
                self.after(0, self._update_stream)
            self.after(0, self._finish)
        except Exception as e:
            self.after(0, lambda: self.update_status(f"Error: {e}"))
            self.after(0, self._finish)

    def _update_stream(self):
        if not self.generating:
            return
        self.chat_text.config(state="normal")
        if hasattr(self, 'typing_start') and self.typing_start:
            end = self.chat_text.index("end-1c")
            self.chat_text.delete(self.typing_start, end)
            self.typing_start = None
            self.bubble_start = self.chat_text.index("end-1c")
            self.chat_text.insert("end", self.stream_text, ("assistant",))
        else:
            if hasattr(self, 'bubble_start'):
                end = self.chat_text.index("end-1c")
                self.chat_text.delete(self.bubble_start, end)
                self.chat_text.insert(self.bubble_start, self.stream_text, ("assistant",))
        self._set_chat_readonly()
        self.chat_text.see("end")

    def _finish(self):
        self.generating = False
        self._remove_temp_markers()
        if self.stream_text:
            self.chat_text.config(state="normal")
            if not hasattr(self, 'bubble_start') or not self.bubble_start:
                self.chat_text.insert("end", "\n" + self.stream_text + "\n", ("assistant",))
            self._set_chat_readonly()
        entry = {"role": "assistant", "content": self.stream_text, "source": "local"}
        self.history.append(entry)
        self.save_history()
        self._play_ding()
        self.update_status("Ready")
        self.bubble_start = None
        self.attached_images.clear()

    def new_chat(self):
        self.history.clear()
        self.chat_text.config(state="normal")
        self.chat_text.delete("1.0", "end")
        self._set_chat_readonly()
        self.save_history()
        self.update_status("Chat cleared")

    def _preload_model(self):
        def preload():
            try:
                running = [m["model"] for m in ollama.list().get("models", [])]
                if self.current_model not in running:
                    self.after(0, lambda: self.update_status("Pulling model..."))
                    subprocess.run(["ollama", "pull", self.current_model], check=False)
                ollama.chat(model=self.current_model, messages=[{"role": "user", "content": "hi"}])
                self.after(0, lambda: self.update_status("Ready"))
            except Exception as e:
                self.after(0, lambda: self.update_status(f"Error: {e}"))
        threading.Thread(target=preload, daemon=True).start()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = SaturnApp()
    app.mainloop()