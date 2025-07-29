from openai import OpenAI
import asyncio

class VideoAnalyzer:
    def __init__(self, api_key: str, base_url: str = None, model_name: str = "gpt-4o"):
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        self.conversation_history = []
        self.system_instruction = "You are a video analyzer, you have to watch the video user provided, and respond with detailed description of the video. User may ask follow-up questions. User is using language zh-tw, please also use zh-tw to reply them."

    async def analyze_video_transcript(self, video_base64: str):
        """
        Analyzes a video from a base64 encoded string using OpenAI API.
        """
        # Reset history for new video
        self.conversation_history = [
            {
                "role": "system",
                "content": self.system_instruction
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
                self.client.chat.completions.create,
                model=self.model_name,
                messages=self.conversation_history,
                max_tokens=9000,
            )
            reply = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": reply})
            return reply + "\n\n" + "-# Reply to this message to ask follow-up questions."
        except Exception as e:
            print(f"Error analyzing video: {e}")
            return f"Error: Could not analyze the video. {e}"

    async def ask_question(self, question: str):
        """
        Asks a follow-up question about the video.
        """
        if not self.conversation_history:
            return "Error: You need to analyze a video first before asking follow-up questions."

        self.conversation_history.append({"role": "user", "content": question})

        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model_name,
                messages=self.conversation_history,
                max_tokens=4095,
            )
            reply = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            print(f"Error during follow-up: {e}")
            return f"Error: Could not get a response. {e}"