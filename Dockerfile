FROM python:3.11-slim

WORKDIR /app

# requirements.txtをコピー
COPY requirements.txt .

# 必要なパッケージをrequirements.txtからインストール
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ポートを公開
EXPOSE 8501

# Streamlitアプリケーションを起動
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"] 