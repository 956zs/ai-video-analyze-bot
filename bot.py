import discord
import re
import asyncio
import os
import httpx
import json

from load_config import discord_token
from split import splitmsg

LOADING_EMOJI = "<a:loading:1281561134968606750>"
API_BASE_URL = "http://127.0.0.1:8000" # Make sure this matches your API server address

client = discord.Client(intents=discord.Intents.all())
# Maps a channel ID to the last successful task_id for follow-up questions
channel_task_ids = {}

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
    Handles the video analysis process by calling the backend API.
    """
    reply_msg = await message.reply(f"## {LOADING_EMOJI} Requesting video analysis...")
    
    try:
        async with httpx.AsyncClient(timeout=None) as http_client:
            # 1. Start the analysis task
            response = await http_client.post(f"{API_BASE_URL}/analyze", json={"video_url": url})
            response.raise_for_status()
            data = response.json()
            task_id = data.get("task_id")

            if not task_id:
                await reply_msg.edit(content="❌ **API Error:** Could not start analysis task.")
                return

            # 2. Poll for the result
            while True:
                await asyncio.sleep(5) # Wait for 5 seconds before checking status
                status_response = await http_client.get(f"{API_BASE_URL}/status/{task_id}")
                status_response.raise_for_status()
                status_data = status_response.json()
                
                current_status = status_data.get("status")
                await reply_msg.edit(content=f"## {LOADING_EMOJI} Analysis in progress... (Status: {current_status})")

                if current_status == "completed":
                    result_response = await http_client.get(f"{API_BASE_URL}/result/{task_id}")
                    result_response.raise_for_status()
                    result_data = result_response.json()
                    
                    await reply_msg.edit(content="✅ **Analysis Complete!**")
                    await send_reply_chunks(message, result_data.get("result"))
                    channel_task_ids[message.channel.id] = task_id # Save task_id for follow-ups
                    break
                elif current_status == "failed":
                    result_response = await http_client.get(f"{API_BASE_URL}/result/{task_id}")
                    result_data = result_response.json()
                    error_message = result_data.get("result", "An unknown error occurred.")
                    await reply_msg.edit(content=f"❌ **Analysis Failed:** {error_message}")
                    break
    
    except httpx.RequestError as e:
        print(f"HTTP Request Error: {e}")
        await reply_msg.edit(content="❌ **API Connection Error:** Could not connect to the analysis service.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        await reply_msg.edit(content="❌ **An unexpected error occurred.** Please try again later or contact the administrator.")

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    url = None
    # Check for URL in DMs
    if isinstance(message.channel, discord.DMChannel):
        match = re.search(r'https?://\S+', message.content)
        if match:
            url = match.group(0)

    # Check for mentions or replies
    elif message.content.startswith(f"<@{str(client.user.id)}>") or (message.reference and f"<@{str(client.user.id)}>" in message.content):
        content_to_check = message.content
        
        # If it's a reply, check the replied message's content for a URL
        if message.reference and message.reference.message_id:
            try:
                replied_to_message = await message.channel.fetch_message(message.reference.message_id)
                
                # If the replied message is from the bot, it's a follow-up question
                if replied_to_message.author == client.user:
                    task_id = channel_task_ids.get(message.channel.id)
                    if task_id:
                        await message.add_reaction(LOADING_EMOJI)
                        async with httpx.AsyncClient(timeout=None) as http_client:
                            response = await http_client.post(
                                f"{API_BASE_URL}/ask",
                                json={"task_id": task_id, "question": message.content}
                            )
                            response.raise_for_status()
                            data = response.json()
                            await send_reply_chunks(message, data.get("answer", "No answer received."))
                        await message.remove_reaction(LOADING_EMOJI, client.user)
                        return # Stop further processing
                
                content_to_check = replied_to_message.content
            except discord.NotFound:
                pass # If replied message is not found, just check the current message
            except Exception as e:
                print(f"Error processing follow-up or fetching replied message: {e}")

        match = re.search(r'https?://\S+', content_to_check)
        if match:
            url = match.group(0)

    if url:
        asyncio.create_task(process_video_analysis(message, url))
    elif (isinstance(message.channel, discord.DMChannel) or message.content.startswith(f"<@{str(client.user.id)}>")):
        await message.reply("請提供一個有效的影片 URL。")

client.run(discord_token)