import asyncio, aiosqlite
from hydrogram import Client, filters
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from hydrogram.errors import UserNotParticipant, FloodWait

# --- CONFIG ---
API_ID = 38256136
API_HASH = "b7f65470f7f82a9c6e0f996850282785"
BOT_TOKEN = "8634168215:AAFYyqs2N1vFsfmCy_POBO9-W8VuPuoEpag"
ADMIN_ID = 8454381782

UPDATE_CH = "@BankingForge" 
SUPPORT_GP = "@QuizForge"
YT_LINK = "https://www.youtube.com/channel/UCZXuqQLNamTv62VE0E4q_eQ"

bot = Client("banking_protected_pro", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
DB_NAME = "ultra_pro_vault.db"

# Global Variable for Bot Status
BOT_STATUS = True # True = ON, False = OFF

# --- DATABASE INIT ---
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS folders (name TEXT PRIMARY KEY, parent TEXT)")
        await db.execute("CREATE TABLE IF NOT EXISTS files (folder TEXT, file_id TEXT, title TEXT)")
        await db.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
        await db.commit()

# --- MAINTENANCE & JOIN CHECKER ---
async def is_allowed(c, m):
    if m.from_user.id == ADMIN_ID: return True
    
    # Check Bot Status
    if not BOT_STATUS:
        await m.reply_text("⚠️ **Bot Maintenance Mode par hai!**\n\nBhai, abhi bot off hai, thodi der baad try karna.")
        return False

    # Force Join Check
    try:
        await c.get_chat_member(UPDATE_CH, m.from_user.id)
        await c.get_chat_member(SUPPORT_GP, m.from_user.id)
        return True
    except UserNotParticipant:
        btn = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{UPDATE_CH[1:]}")],
            [InlineKeyboardButton("👥 Join Group", url=f"https://t.me/{SUPPORT_GP[1:]}")],
            [InlineKeyboardButton("🔄 Try Again", callback_data="dir_root")]
        ]
        await m.reply_text("❌ **Access Denied!**\nPehle Join Karein.", reply_markup=InlineKeyboardMarkup(btn))
        return False
    except Exception: return True

# --- ADMIN ON/OFF COMMANDS ---
@bot.on_message(filters.command("off") & filters.user(ADMIN_ID))
async def bot_off(c, m):
    global BOT_STATUS
    BOT_STATUS = False
    await m.reply_text("🔴 **Bot OFF ho gaya hai!**\nAb koi bhi user ise use nahi kar payega.")

@bot.on_message(filters.command("on") & filters.user(ADMIN_ID))
async def bot_on(c, m):
    global BOT_STATUS
    BOT_STATUS = True
    await m.reply_text("🟢 **Bot ON ho gaya hai!**\nSabhi users ab folders dekh sakte hain.")

# --- START ---
@bot.on_message(filters.command("start") & filters.private)
async def start(c, m):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users VALUES (?)", (m.from_user.id,))
        await db.commit()

    if not await is_allowed(c, m): return
    
    await m.reply_text(f"👋 Hello {m.from_user.first_name}!\nWelcome to **Banking Forge**.", 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📂 View Folders", callback_data="dir_root")]]))

# --- NAVIGATION ---
@bot.on_callback_query(filters.regex(r"dir_(.*)"))
async def navigate(c, q):
    # Check status for callbacks
    if q.from_user.id != ADMIN_ID and not BOT_STATUS:
        return await q.answer("⚠️ Bot abhi off hai!", show_alert=True)
    if not await is_allowed(c, q): return
    
    curr = q.matches[0].group(1)
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT name FROM folders WHERE parent=?", (curr,)) as cur: folders = await cur.fetchall()
        async with db.execute("SELECT COUNT(*) FROM files WHERE folder=?", (curr,)) as cur: f_count = (await cur.fetchone())[0]

    btn = [[InlineKeyboardButton(f"📁 {f[0]}", callback_data=f"dir_{f[0]}")] for f in folders]
    if f_count > 0: btn.append([InlineKeyboardButton(f"📄 View {f_count} Files", callback_data=f"view_{curr}")])
    if curr != "root": btn.append([InlineKeyboardButton("⬅️ Back", callback_data="dir_root")])
    
    await q.edit_message_text(f"📍 Location: **{curr}**", reply_markup=InlineKeyboardMarkup(btn) if btn else None)

# --- FOLDER & SAVE (Admin Only) ---
@bot.on_message(filters.command("addfolder") & filters.user(ADMIN_ID))
async def add_folder(c, m):
    args = m.text.split(None, 2)
    name, parent = args[1], args[2] if len(args) >= 3 else "root"
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO folders VALUES (?, ?)", (name, parent))
        await db.commit()
    await m.reply_text(f"✅ Folder `{name}` created.")

@bot.on_message((filters.video | filters.document) & filters.user(ADMIN_ID))
async def on_file(c, m):
    await m.reply_text(f"Reply with: `/save [FolderName] [Title]`")

@bot.on_message(filters.command("save") & filters.user(ADMIN_ID) & filters.reply)
async def save_file(c, m):
    args = m.text.split(None, 2)
    f_name, title = args[1], args[2]
    f_id = m.reply_to_message.video.file_id if m.reply_to_message.video else m.reply_to_message.document.file_id
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO files VALUES (?, ?, ?)", (f_name, f_id, title))
        await db.commit()
    await m.reply_text(f"✅ Saved: {title}")

# --- VIEW FILES ---
@bot.on_callback_query(filters.regex(r"view_(.*)"))
async def view_files(c, q):
    if not await is_allowed(c, q): return
    f_name = q.matches[0].group(1)
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT file_id, title FROM files WHERE folder=?", (f_name,)) as cur: files = await cur.fetchall()
    await q.message.delete()
    for f in files:
        await c.send_cached_media(chat_id=q.message.chat.id, file_id=f[0], caption=f"🎥 **{f[1]}**", protect_content=True)
        await asyncio.sleep(0.7)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())
    bot.run()