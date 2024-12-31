# 使用 Python 3.11 作為基底映像
FROM python:3.11

# 更新系統套件並安裝必要的依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 設定工作目錄
WORKDIR /app

# 將專案檔案加入容器
COPY . /app

# 安裝 Python 相依套件
RUN pip install --no-cache-dir -r requirements.txt

# 暴露應用程式的埠
EXPOSE 8006

# 執行應用程式
CMD ["python", "-u", "app/main.py"]