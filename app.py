import os
import streamlit as st
import sys
import asyncio
from dotenv import load_dotenv

# OpenAI Agents SDKをインポート
from agents import Agent, Runner
import openai

# .envファイルのパスを指定して読み込む
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# スタイルとタイトル設定
st.set_page_config(page_title="OpenAI Agents UI", layout="wide")
st.title("OpenAI Agents デモ")
st.markdown("OpenAI Agents SDKを使用した対話型アシスタント")

# サイドバーに設定パネルを追加
st.sidebar.header("エージェント設定")

# 環境変数からAPIキーを取得
api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    st.error("APIキーが見つかりません。'.env'ファイルを確認してください。")
    st.stop()
else:
    # 環境変数を設定
    os.environ["OPENAI_API_KEY"] = api_key
    st.sidebar.success("APIキーを正常に読み込みました")

# エージェント名の入力
agent_name = st.sidebar.text_input("エージェント名", "Assistant")

# 指示の入力
default_instructions = "You are a helpful assistant, always respond in Japanese"
instructions = st.sidebar.text_area("指示", default_instructions, height=150)

# モデル選択
models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
selected_model = st.sidebar.selectbox("モデル", models)

# 複数のエージェントプリセット
st.sidebar.header("エージェントプリセット")
presets = {
    "日本語アシスタント": {
        "name": "日本語アシスタント",
        "instructions": "あなたは役立つアシスタントです。常に日本語で応答してください。",
        "model": "gpt-3.5-turbo"
    },
    "英語翻訳者": {
        "name": "英語翻訳者",
        "instructions": "あなたは日本語を英語に翻訳するエキスパートです。自然で流暢な英語に翻訳してください。",
        "model": "gpt-3.5-turbo"
    },
    "プログラミングヘルパー": {
        "name": "プログラミングヘルパー",
        "instructions": "あなたはプログラミングの専門家です。コードの説明、デバッグ、最適化のアドバイスを日本語で提供してください。",
        "model": "gpt-3.5-turbo"
    }
}

selected_preset = st.sidebar.selectbox("プリセットを選択", ["カスタム"] + list(presets.keys()))

if selected_preset != "カスタム":
    preset = presets[selected_preset]
    agent_name = preset["name"]
    instructions = preset["instructions"]
    selected_model = preset["model"]
    st.sidebar.info(f"プリセット '{selected_preset}' を読み込みました")

# メインエリア
st.header("対話")

# セッション状態の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# 過去のメッセージを表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ユーザー入力
user_input = st.chat_input("メッセージを入力してください...")

# Streamlitスレッドでasyncioを実行するためのヘルパー関数
def run_async(coroutine):
    """新しいイベントループを作成してコルーチンを実行するヘルパー関数"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()

if user_input:
    # ユーザーメッセージをチャット履歴に追加
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # ユーザーメッセージを表示
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # 処理中表示
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("考え中...")
    
    try:
        # エージェントの作成
        agent = Agent(
            name=agent_name,
            instructions=instructions,
            model=selected_model
        )
        
        # 実行と結果の取得
        with st.spinner('レスポンスを生成中...'):
            # Runner.run_syncの代わりに非同期処理を実行
            result = run_async(Runner.run(agent, user_input))
            response = result.final_output
        
        # アシスタントメッセージをチャット履歴に追加
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # 応答を表示（処理中を上書き）
        message_placeholder.markdown(response)
        
    except openai.RateLimitError as e:
        error_msg = f"OpenAI APIのクォータエラーが発生しました。\nエラー詳細: {e}"
        message_placeholder.error(error_msg)
        st.sidebar.error("対処方法:\n1. OpenAIダッシュボードでクォータを確認\n2. 請求情報を更新\n3. 別のAPIキーを使用")
    except Exception as e:
        error_msg = f"エラーが発生しました: {e}"
        message_placeholder.error(error_msg)
        st.sidebar.error(f"詳細エラー: {str(e)}")

# 使い方ガイド
with st.expander("使い方"):
    st.markdown("""
    ### 基本的な使い方
    1. サイドバーでエージェントの設定を行います（名前、指示、使用モデルなど）
    2. メッセージ入力欄にプロンプトを入力してエンターキーを押します
    3. AIからの応答が表示されます
    
    ### プリセットの使用
    サイドバーの「エージェントプリセット」から事前設定されたエージェントを選択できます。
    
    ### カスタム設定
    プリセットで「カスタム」を選択すると、自由にエージェント設定をカスタマイズできます。
    
    ### 注意事項
    - GPT-4モデルは高コストですので、テスト目的ではGPT-3.5-turboの使用をおすすめします
    - APIクォータに注意してください
    """) 