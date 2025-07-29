import discord
import re
import asyncio
import base64

from load_config import discord_token
from analyze import generate_analyze, ask_followup
from split import splitmsg
from download_video import download_video, remove_video

client = discord.Client(intents=discord.Intents.all())

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Check if the bot is mentioned at the beginning of the message for video analysis
    if message.content.startswith(f"<@{str(client.user.id)}>"):
        parts = [p for p in message.content.split(" ") if p]
        if len(parts) < 2:
            await message.reply("Please provide a URL after mentioning me.")
            return

        url = parts[1]
        if re.match(r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)", url):
            
            reply_msg = await message.reply("## <a:loading:1281561134968606750> Downloading video...")
            
            video_filename = None
            try:
                # Download the video
                video_filename = download_video(url)
                if not video_filename:
                    await reply_msg.edit(content="Failed to download the video. It might be private, region-locked, or an invalid URL.")
                    return

                await reply_msg.edit(content="## <a:loading:1281561134968606750> Encoding video for analysis...")

                # Read and encode the video file in base64
                with open(video_filename, "rb") as video_file:
                    video_base64 = base64.b64encode(video_file.read()).decode('utf-8')

                await reply_msg.edit(content="## <a:loading:1281561134968606750> Analyzing Video... This may take a while...")
                
                # Send to analysis
                reply_text = await generate_analyze(video_base64)
                
                await reply_msg.edit(content=f"✅ Analysis Complete!")

                reply_chunks = await splitmsg(reply_text)
                for i, chunk in enumerate(reply_chunks):
                    if i == 0:
                        await message.reply(chunk)
                    else:
                        await message.channel.send(chunk)
                
            except Exception as e:
                await reply_msg.edit(content=f"An unexpected error occurred: {e}")
            finally:
                # Clean up the downloaded file
                if video_filename:
                    remove_video(video_filename)
            return
        else:
            await message.reply("Invalid URL provided.")
            return
        
    # Check if the bot is mentioned in a reply for follow-up questions
    if message.reference and message.reference.message_id:
        try:
            replied_to_message = await message.channel.fetch_message(message.reference.message_id)
            if replied_to_message.author == client.user:
                await message.add_reaction("<a:loading:1281561134968606750>")
                
                follow_up_reply = await ask_followup(message.content)
                
                reply_chunks = await splitmsg(follow_up_reply)
                for i, chunk in enumerate(reply_chunks):
                     if i == 0:
                        await message.reply(chunk)
                     else:
                        await message.channel.send(chunk)

                await message.remove_reaction("<a:loading:1281561134968606750>", client.user)
                return
        except discord.NotFound:
            pass
        except Exception as e:
            print(f"Error during follow-up check: {e}")

client.run(discord_token)