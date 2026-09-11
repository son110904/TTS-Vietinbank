# VieNeu-TTS v3 Turbo — API server

API tổng hợp giọng nói tiếng Việt, dựa trên VieNeu-TTS v3 Turbo — model được chọn sau khi
đánh giá WER/UTMOS/SIM-o trên 4 model (mms-tts-vie, valtec-tts, VieNeu-TTS v3 Nano, VieNeu-TTS v3 Turbo).

## Cài đặt

```bash
pip install -r requirements.txt
```

## Chuẩn bị giọng mặc định

Đặt 1 file `ref_audio.wav` (mono, 3-10 giây, giọng rõ) cùng thư mục với `app.py` — đây là giọng
mặc định dùng khi người gọi API không tự truyền `ref_audio_base64` riêng. Có thể dùng lại chính
file `ref_audio.wav` đã lấy từ VIVOS lúc đánh giá model.

## Chạy server

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Server load model **1 lần khi khởi động** (không load lại mỗi request), nên request đầu tiên
có thể hơi lâu hơn các request sau.

## Gọi thử

```bash
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Xin chào, đây là bài kiểm tra API."}' \
  --output output.wav
```

Hoặc dùng `client_example.py` (có sẵn ví dụ dùng giọng mặc định lẫn tự truyền giọng riêng để clone):

```bash
python client_example.py
```

## Endpoint

| Endpoint | Method | Mô tả |
|---|---|---|
| `/health` | GET | Kiểm tra server còn sống, trả về tên model + sample rate |
| `/tts` | POST | Body JSON: `{"text": str, "ref_audio_base64": str (tuỳ chọn), "denoise": bool}` → trả về file `.wav` |

## Giới hạn hiện tại (nên biết trước khi giao cho mentor)

- Server xử lý **tuần tự, không có hàng đợi** — nếu nhiều người gọi cùng lúc, request sẽ xếp hàng chờ
  nhau (do model chỉ có 1 instance dùng chung). Nếu cần xử lý đồng thời nhiều hơn, cân nhắc chạy
  nhiều worker (`uvicorn app:app --workers N`), lưu ý mỗi worker sẽ load riêng 1 bản model
  (tốn thêm RAM tương ứng số worker).
- Chưa có giới hạn tốc độ gọi (rate limiting) hay xác thực (API key) — phù hợp dùng nội bộ,
  chưa nên public ra ngoài nếu chưa thêm các lớp bảo vệ này.
- `MAX_CHARS = 2000` trong `app.py` — chỉnh nếu cần văn bản dài hơn.
