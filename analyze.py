from load_config import gemini_api_key
import google.genai as genai
import asyncio

client = genai.Client(api_key=gemini_api_key)

def upload_to_gemini(path):
    file = client.files.upload(path=path)
    print(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 2000,
    "response_mime_type": "text/plain",
}

safety_settings=[
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "block_none"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "block_none"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "block_none"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "block_none"
    }
]

system_instruction="You are a video analyzer, you have to watch the video user provided, and respond with detailed description of the video. User may ask follow-up questions. User is using language zh-tw, please also use zh-tw to reply them."

async def generate_analyze(file):
    global convo
    convo = client.chats.create(
        model='models/gemini-1.5-pro',
        history=[],
        config=dict(
            generation_config=generation_config,
            safety_settings=safety_settings,
            system_instruction=system_instruction,
        )
    )
    is_finished = False

    retry_times = 0
    while not is_finished:
        try:
            reply_msg = await client.aio.chats.send_message(
                chat=convo.name,
                contents=[file]
            )
            is_finished = True
        except Exception as e:
            print(f"Error: {e}")
            print("retrying...")
            retry_times += 1
            await asyncio.sleep(1)

            if retry_times > 5:
                return "Error: Too many retries. Please try again later. Last error: " + str(e)

    return reply_msg.text + "\n\n" + "-# Reply to this message to ask follow-up questions."

async def ask_followup(question):
    global convo

    retry_times = 0
    is_finished = False
    while not is_finished:
        try:
            reply_msg = await client.aio.chats.send_message(
                chat=convo.name,
                contents=[question]
            )
            is_finished = True
        except Exception as e:
            print(f"Error: {e}")
            print("retrying...")
            retry_times += 1
            await asyncio.sleep(1)

            if retry_times > 5:
                return "Error: Too many retries. Please try again later. Last error: " + str(e)
    return reply_msg.text