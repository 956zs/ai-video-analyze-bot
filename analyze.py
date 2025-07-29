from openai import OpenAI
import asyncio

from load_config import openai_api_key, openai_base_url

# Conditionally create the client based on whether a base_url is provided
if openai_base_url:
    client = OpenAI(
        api_key=openai_api_key,
        base_url=openai_base_url,
    )
else:
    client = OpenAI(
        api_key=openai_api_key,
    )

# To store conversation history
conversation_history = []

system_instruction = "You are a video analyzer, you have to watch the video user provided, and respond with detailed description of the video. User may ask follow-up questions. User is using language zh-tw, please also use zh-tw to reply them."

async def generate_analyze(video_base64: str):
    """
    Analyzes a video from a base64 encoded string using OpenAI API.
    """
    global conversation_history
    # Reset history for new video
    conversation_history = [
        {
            "role": "system",
            "content": system_instruction
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Please describe the contents of this video.",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:video/mp4;base64,{video_base64}",
                    },
                },
            ],
        }
    ]

    try:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="[EXPRESS] gemini-2.5-pro",
            messages=conversation_history,
            max_tokens=9000, # Increased max_tokens for more complete answers
        )
        reply = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": reply})
        return reply + "\n\n" + "-# Reply to this message to ask follow-up questions."
    except Exception as e:
        print(f"Error analyzing video: {e}")
        return f"Error: Could not analyze the video. {e}"

async def ask_followup(question: str):
    """
    Asks a follow-up question about the video.
    """
    global conversation_history
    if not conversation_history:
        return "Error: You need to analyze a video first before asking follow-up questions."

    conversation_history.append({"role": "user", "content": question})

    try:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="[EXPRESS] gemini-2.5-pro",
            messages=conversation_history,
            max_tokens=4095, # Increased max_tokens for more complete answers
        )
        reply = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        print(f"Error during follow-up: {e}")
        return f"Error: Could not get a response. {e}"