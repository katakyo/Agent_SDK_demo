FROM python:3.11-slim

WORKDIR /app

# 必要なパッケージをインストール
RUN pip install --no-cache-dir python-dotenv==1.0.0 openai>=1.66.0 openai-agents streamlit

COPY . .

# ポートを公開
EXPOSE 8501

# Streamlitアプリケーションを起動
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"] 