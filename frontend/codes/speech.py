import os
import time
import uuid
import azure.cognitiveservices.speech as speechsdk
from flask import Blueprint, jsonify, request, current_app, url_for
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 創建藍圖
speech_bp = Blueprint('speech', __name__)

# Azure 憑證
AZURE_SPEECH_KEY = os.environ.get('AZURE_SPEECH_KEY')
AZURE_SPEECH_REGION = os.environ.get('AZURE_SPEECH_REGION', 'eastasia')

# 聲音設定
VOICE_NAMES = {
    'female_warm': 'zh-TW-HsiaoChenNeural',   # 溫暖女聲
    'female_cheerful': 'zh-TW-HsiaoYuNeural',  # 活潑女聲
    'male_warm': 'zh-TW-YunJheNeural',         # 溫暖男聲
    'default': 'zh-TW-HsiaoYuNeural'         # 預設女聲
}

@speech_bp.route('/api/get_speech', methods=['POST'])
def get_speech():
    """生成語音檔案並返回URL"""
    data = request.json
    text = data.get('text', '')
    voice_style = data.get('style', 'default')
    speaking_rate = data.get('rate', 1.2)
    
    if not text:
        return jsonify({'success': False, 'error': '未提供文字'}), 400
    
    try:
        # 設置 Azure 語音配置
        speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_SPEECH_KEY, 
            region=AZURE_SPEECH_REGION
        )
        
        # 選擇聲音
        voice_name = VOICE_NAMES.get(voice_style, VOICE_NAMES['default'])
        speech_config.speech_synthesis_voice_name = voice_name
        
        # 添加表情、語調和語速控制 (SSML)
        ssml_text = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
               xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="zh-TW">
            <voice name="{voice_name}">
                <prosody rate="{speaking_rate}">
                    <mstts:express-as style="cheerful" styledegree="1.2">
                        {text}
                    </mstts:express-as>
                </prosody>
            </voice>
        </speak>
        """
        
        # 創建文件名和路徑
        filename = f"speech_{uuid.uuid4()}.mp3"
        
        # 確保路徑是絕對路徑
        temp_audio_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp_audio')
        os.makedirs(temp_audio_dir, exist_ok=True)
        
        # 文件完整路徑
        file_path = os.path.join(temp_audio_dir, filename)
        
        # 設置音頻輸出
        audio_config = speechsdk.audio.AudioOutputConfig(filename=file_path)
        
        # 創建語音合成器
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, 
            audio_config=audio_config
        )
        
        # 合成語音
        result = synthesizer.speak_ssml_async(ssml_text).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            # 創建可訪問的URL
            audio_url = f'/temp_audio/{filename}'
            
            # 記錄成功訊息
            current_app.logger.info(f"語音合成成功: {text[:30]}...")
            
            return jsonify({
                'success': True,
                'audio_url': audio_url
            })
        else:
            current_app.logger.error(f"語音合成失敗: {result.reason}")
            return jsonify({
                'success': False,
                'error': f'語音合成失敗: {result.reason}'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"語音API錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500