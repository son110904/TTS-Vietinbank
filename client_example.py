import base64

import requests

API_URL = "http://localhost:8000"  # đổi thành địa chỉ server thật khi deploy


def tts_default_voice(text: str, out_path: str = "output.wav"):
    """Dùng giọng mặc định (ref_audio.wav đặt sẵn trên server)."""
    resp = requests.post(f"{API_URL}/tts", json={"text": text})
    resp.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(resp.content)
    print(f"Đã lưu: {out_path}")


def tts_custom_voice(text: str, ref_audio_path: str, out_path: str = "output_cloned.wav"):
    """Clone giọng theo 1 file audio mẫu tự cung cấp."""
    with open(ref_audio_path, "rb") as f:
        ref_b64 = base64.b64encode(f.read()).decode("utf-8") #file âm thanh là binary, không gửi bằng json đc nên phải chuyển ra ascii bằng base64 để gửi
    resp = requests.post(
        f"{API_URL}/tts",
        json={"text": text, "ref_audio_base64": ref_b64},
    )
    resp.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(resp.content)
    print(f"Đã lưu: {out_path}")

if __name__ == "__main__":
    print(requests.get(f"{API_URL}/health").json())
    tts_default_voice("Xin chào, đây là API tổng hợp giọng nói tiếng Việt.")
    # tts_custom_voice("Xin chào", ref_audio_path="my_voice_sample.wav")
