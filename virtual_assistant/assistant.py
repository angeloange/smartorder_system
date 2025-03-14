import azure.cognitiveservices.speech as speechsdk
from .config import AZURE_SPEECH_KEY, AZURE_SPEECH_REGION, ASSISTANT_CONFIG

class VirtualAssistant:
    def __init__(self):
        # 初始化 Azure 語音服務
        self.speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_SPEECH_KEY, 
            region=AZURE_SPEECH_REGION
        )
        self.speech_config.speech_synthesis_voice_name = ASSISTANT_CONFIG["voice"]
        
        # 初始化語音合成器
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config
        )

    async def speak(self, text):
        """讓虛擬助手說話"""
        result = await self.speech_synthesizer.speak_text_async(text)
        return result.result

    async def listen(self):
        """監聽用戶語音輸入"""
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config
        )
        result = await speech_recognizer.recognize_once_async()
        return result.text if result.result.reason == speechsdk.ResultReason.RecognizedSpeech else None
