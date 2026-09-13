# Hướng dẫn 

## 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

## 2. Đảm bảo có file âm thanh mẫu

Kiểm tra trong thư mục dự án có file:

```bash
ref_audio.wav
```

Nếu chưa có, hãy thêm file audio mẫu vào cùng thư mục với `app.py`.

## 3. Chạy server

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Sau đó mở:

- http://localhost:8000/health
- http://localhost:8000/docs

## 4. Nếu dùng Docker

```bash
docker build -t vietinbank-tts .
docker run --rm -p 8000:7860 vietinbank-tts
```

## 5. Cách test
```bash
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Xin chào, đây là bài kiểm tra API."}' \
  --output output.wav
```
