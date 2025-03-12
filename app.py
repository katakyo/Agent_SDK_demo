import os
import streamlit as st
import sys

# スタイルとタイトル設定
st.set_page_config(page_title="OpenAI Agents UI", layout="wide")
st.title("OpenAI Agents デモ")
st.markdown("OpenAI Agents SDKを使用した対話型アシスタント")

# モジュールからインポート
from src.config.settings import load_config
from src.ui.sidebar import setup_sidebar, show_error_sidebar
from src.ui.chat import initialize_chat, process_message
from src.ui.guide import show_usage_guide

# 設定の読み込み
api_key = load_config()
if api_key is None:
    st.error("APIキーが見つかりません。'.env'ファイルを確認してください。")
    st.stop()
else:
    # 環境変数を設定
    os.environ["OPENAI_API_KEY"] = api_key

# サイドバーセットアップ
agent_name, instructions, selected_model = setup_sidebar()

# チャットインターフェース初期化
user_input = initialize_chat()

# ユーザー入力があれば処理
if user_input:
    error_message = process_message(user_input, agent_name, instructions, selected_model)
    if error_message:
        show_error_sidebar(error_message)

# 使い方ガイド表示
show_usage_guide() 