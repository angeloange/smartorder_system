from flask import Flask, render_template, request, jsonify
import os
from gtts import gTTS

app = Flask(__name__)

AUDIO_FOLDER = "audio"
if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)

@app.route("/")
def index():
    return render_template("index.html")
from flask import send_from_directory

# 設定音訊資料夾的路由
@app.route("/audio/<path:filename>")
def serve_audio(filename):
    return send_from_directory("audio", filename)

@app.route("/generate_audio", methods=["POST"])
def generate_audio():
    data = request.json
    text = data.get("text", "")

    if not text:
        return jsonify({"error": "請輸入文字"}), 400

    file_path = os.path.join(AUDIO_FOLDER, "output.mp3")
    
    tts = gTTS(text, lang="zh-TW")
    tts.save(file_path)

    return jsonify({"audio_url": f"/audio/output.mp3"})

if __name__ == "__main__":
    app.run(debug=True)
