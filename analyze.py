from openai import OpenAI
import asyncio
import cv2
import base64
from PIL import Image
import io

class VideoAnalyzer:
    def __init__(self, api_key: str, base_url: str = None, model_name: str = "gpt-4o"):
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        self.conversation_history = []
        self.system_instruction = "You are a video analyzer, you have to watch the video user provided, and respond with detailed description of the video. User may ask follow-up questions. User is using language zh-tw, please also use zh-tw to reply them."

    def _process_video_frames(self, video_path: str, max_frames: int = 20):
        """
        Extracts frames from a video, converts them to base64, and returns a list.
        """
        video = cv2.VideoCapture(video_path)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0:
            return []
        
        # Ensure we don't try to read more frames than exist
        max_frames = min(max_frames, total_frames)
        
        # Calculate the interval to get an even distribution of frames
        interval = total_frames // max_frames if max_frames > 0 else total_frames

        base64_frames = []
        for i in range(max_frames):
            frame_id = i * interval
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
            success, frame = video.read()
            if not success:
                continue

            # Convert frame to JPEG in memory
            _, buffer = cv2.imencode(".jpg", frame)
            base64_frame = base64.b64encode(buffer).decode("utf-8")
            base64_frames.append(base64_frame)
        
        video.release()
        return base64_frames

    async def analyze_video_from_path(self, video_path: str):
        """
        Analyzes a video from a file path by processing its frames.
        """
        base64_frames = await asyncio.to_thread(self._process_video_frames, video_path)
        if not base64_frames:
            return "Error: Could not extract frames from the video. It might be corrupted or in an unsupported format."

        # Reset history for new video
        user_content = [
            {
                "type": "text",
                "text": "These are frames from a video. Please describe the contents of this video in detail.",
            }
        ]
        for frame in base64_frames:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{frame}"},
            })

        self.conversation_history = [
            {"role": "system", "content": self.system_instruction},
            {"role": "user", "content": user_content}
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