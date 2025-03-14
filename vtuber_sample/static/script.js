function generateAudio() {
    let textInput = document.getElementById("text-input").value;
    let subtitle = document.getElementById("subtitle");
    let audioPlayer = document.getElementById("audio-player");
    let vtuberImg = document.getElementById("vtuber-img");

    if (!textInput) {
        alert("請輸入文字！");
        return;
    }

    subtitle.textContent = textInput;

    fetch("/generate_audio", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ text: textInput }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }

        audioPlayer.src = data.audio_url;
        audioPlayer.play();

        // 播放時嘴巴張開
        vtuberImg.src = "/static/vtuber_open.png";

        audioPlayer.onended = function() {
            // 播放完畢後嘴巴閉上
            vtuberImg.src = "/static/vtuber_closed.png";
        };
    })
    .catch(error => console.error("Error:", error));
}
