# Sử dụng Python bản nhẹ
FROM python:3.9-slim

# Cài đặt masscan và các thư viện hệ thống cần thiết
RUN apt-get update && apt-get install -y masscan && rm -rf /var/lib/apt/lists/*

# Copy toàn bộ code vào máy chủ
WORKDIR /app
COPY . .

# Cài đặt thư viện Python
RUN pip install -r requirements.txt

# Lệnh khởi chạy file chính
CMD ["python", "main.py"]
