# # 使用 Python 3.11 作為基底映像
# FROM python:3.11

# # 更新系統套件並安裝必要的依賴
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     python3-pip \
#     && apt-get clean && rm -rf /var/lib/apt/lists/*

# # 設定工作目錄
# WORKDIR /app

# # 將專案檔案加入容器
# COPY . /app

# # 安裝 Python 相依套件
# RUN pip install --no-cache-dir -r requirements.txt

# # 暴露應用程式的埠
# EXPOSE 8006

# # 執行應用程式
# CMD ["python", "-u", "app/main.py"]

# 使用 Python 3.11 作為基底映像
FROM python:3.11

# 更新系統套件並安裝必要的依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \   
    python3-pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 設定工作目錄
WORKDIR /app

# 創建 /data 資料夾並設置權限
RUN mkdir -p /chromadb && chmod 777 /chromadb

# 聲明 /data 資料夾為持久化掛載點
VOLUME ["/chromadb"]

# 將專案檔案加入容器
COPY . /app

# 安裝 Python 相依套件
RUN pip install --no-cache-dir -r requirements.txt

# 單獨安裝與 requirements.txt 衝突的套件
RUN pip install --no-cache-dir \
    llama-index-vector-stores-chroma \
    llama-index-core==0.12.10.post1 \
    llama_index==0.12.10 \
    llama-index-embeddings-ollama==0.5.0 \
    llama-index-llms-openai==0.3.12

# 暴露應用程式的埠
EXPOSE 8006

# 執行應用程式
CMD ["python", "-u", "app/main.py"]
