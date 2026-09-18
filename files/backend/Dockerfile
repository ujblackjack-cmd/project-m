FROM python:3.14-slim

WORKDIR /app

# requirements.txt가 백엔드 폴더 안에 있어야 합니다
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# server.py 파일의 FastAPI 인스턴스(app)를 실행합니다
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]