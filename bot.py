from telethon import TelegramClient, events
import asyncio
import os
import re

# --- APNI DETAILS ---
api_id = 38256136          
api_hash = 'b7f65470f7f82a9c6e0f996850282785'    

client = TelegramClient('downloader_session', api_id, api_hash)

async def progress_bar(current, total):
    print(f"Downloading: {current * 100 / total:.1f}%", end="\r")

async def main():
    await client.start()
    print("--- 🚀 Universal Topic Downloader Online ---")
    
    link = input("\nTopic ka link daalein: ").strip()
    
    # Numbers nikalne ka simple logic
    parts = link.split('/')
    # Link format handle karna: https://t.me/learningnitiall/26
    
    try:
        # Topic ID hamesha aakhri number hota hai agar msg_id na ho
        topic_id = int(parts[-1])
        chat_identifier = parts[-2]
        
        # Agar private channel link hai (contains /c/)
        if "/c/" in link:
            chat_id = int("-100" + chat_identifier)
        else:
            chat_id = chat_identifier

        print(f"🔍 Scanning Topic ID: {topic_id} in Chat: {chat_id}...")
        
        # Dialogs refresh (Zaroori hai topics access ke liye)
        await client.get_dialogs()

        video_count = 0
        # Hum pichle 500 messages scan karenge us specific Topic thread mein
        async for message in client.iter_messages(chat_id, limit=500, reply_to=topic_id):
            # Check if it's a video
            if message.video or (message.media and hasattr(message.media, 'document') and 'video' in (message.file.mime_type or '')):
                video_count += 1
                
                # Naam set karna
                caption = message.text[:20] if message.text else "video"
                clean_name = re.sub(r'[\\/*?:"<>|]', "", caption)
                filename = f"{clean_name}_{message.id}.mp4"

                print(f"\n🎬 Found #{video_count}: {filename}")
                path = await client.download_media(message, progress_callback=progress_bar)
                print(f"\n✅ Saved at: {os.path.abspath(path)}")
                
                # Telegram server ko thoda saans lene dein
                await asyncio.sleep(1.5)

        if video_count == 0:
            print("\n❌ Is Topic mein koi video nahi mili. Ho sakta hai ye Topic ID galat ho ya bot ko access na ho.")
        else:
            print(f"\n✨ Dhan-te-nan! Total {video_count} videos download ho gayi hain.")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("Tip: Link copy karne ke liye Topic ke naam par right-click karke 'Copy Link' karein.")

if __name__ == '__main__':
    asyncio.run(main())