import discord
import re
import asyncio
import base64
import os

from load_config import discord_token, openai_api_key, openai_base_url
from analyze import VideoAnalyzer
from split import splitmsg
from download_video import download_video, remove_video

LOADING_EMOJI = "<a:loading:1281561134968606750>"
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "[EXPRESS] gemini-2.5-pro")

client = discord.Client(intents=discord.Intents.all())
active_analyzers = {}

async def send_reply_chunks(message, text):
    """
    Splits a long message into chunks and sends them as replies.
    """
    reply_chunks = await splitmsg(text)
    for i, chunk in enumerate(reply_chunks):
        if i == 0:
            await message.reply(chunk)
        else:
            await message.channel.send(chunk)

async def process_video_analysis(message, url):
    """
    Handles the entire video analysis process for a given message and URL.
    """
    reply_msg = await message.reply(f"## {LOADING_EMOJI} Downloading video...")
    
    video_filename = None
    try:
        # 1. Download the video
        video_filename = download_video(url)
        if not video_filename:
            await reply_msg.edit(content="❌ **Download Failed:** The video might be private, region-locked, or the URL is invalid.")
            return

        # 2. Encode the video file in base64
        await reply_msg.edit(content=f"## {LOADING_EMOJI} Encoding video for analysis...")
        with open(video_filename, "rb") as video_file:
            video_base64 = base64.b64encode(video_file.read()).decode('utf-8')

        # 3. Send to analysis
        await reply_msg.edit(content=f"## {LOADING_EMOJI} Analyzing Video... This may take a while...")
        analyzer = VideoAnalyzer(api_key=openai_api_key, base_url=openai_base_url, model_name=OPENAI_MODEL_NAME)
        active_analyzers[message.channel.id] = analyzer
        reply_text = await analyzer.analyze_video_transcript(video_base64)
        
        # 4. Send the results
        await reply_msg.edit(content=f"✅ **Analysis Complete!**")
        await send_reply_chunks(message, reply_text)
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        await reply_msg.edit(content="❌ **An unexpected error occurred.** Please try again later or contact the administrator.")
    finally:
        # 5. Clean up the downloaded file
        if video_filename:
            remove_video(video_filename)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Check if the bot is mentioned at the beginning of the message for video analysis
    if message.content.startswith(f"<@{str(client.user.id)}>"):
        match = re.search(r'https?://\S+', message.content)
        if match:
            url = match.group(0)
            # Offload the processing to a separate function
            asyncio.create_task(process_video_analysis(message, url))
        else:
            await message.reply("請提供一個有效的影片 URL。")
        return
        
    # Check if the bot is mentioned in a reply for follow-up questions
    if message.reference and message.reference.message_id:
        try:
            replied_to_message = await message.channel.fetch_message(message.reference.message_id)
            if replied_to_message.author == client.user:
                analyzer = active_analyzers.get(message.channel.id)
                if not analyzer:
                    await message.reply("I don't have the context of the previous video. Please start a new analysis.")
                    return
                
                await message.add_reaction(LOADING_EMOJI)
                
                follow_up_reply = await analyzer.ask_question(message.content)
                
                await send_reply_chunks(message, follow_up_reply)

                await message.remove_reaction(LOADING_EMOJI, client.user)
                return
        except discord.NotFound:
            pass
        except Exception as e:
            print(f"Error during follow-up check: {e}")

client.run(discord_token)