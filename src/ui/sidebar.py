import streamlit as st
import os
from src.config.settings import AVAILABLE_MODELS, DEFAULT_INSTRUCTIONS, DEFAULT_AGENT_NAME, AGENT_PRESETS

def setup_sidebar():
    """
    サイドバーのUIセットアップと設定の取得
    
    Returns:
        tuple: (agent_name, instructions, selected_model) - エージェント設定
    """
    st.sidebar.header("エージェント設定")
    
    # APIキーの状態表示
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        st.sidebar.success("APIキーを正常に読み込みました")
    
    # エージェント名の入力
    agent_name = st.sidebar.text_input("エージェント名", DEFAULT_AGENT_NAME)

    # 指示の入力
    instructions = st.sidebar.text_area("指示", DEFAULT_INSTRUCTIONS, height=150)

    # モデル選択
    selected_model = st.sidebar.selectbox("モデル", AVAILABLE_MODELS)

    # 複数のエージェントプリセット
    st.sidebar.header("エージェントプリセット")
    
    selected_preset = st.sidebar.selectbox("プリセットを選択", ["カスタム"] + list(AGENT_PRESETS.keys()))

    if selected_preset != "カスタム":
        preset = AGENT_PRESETS[selected_preset]
        agent_name = preset["name"]
        instructions = preset["instructions"]
        selected_model = preset["model"]
        st.sidebar.info(f"プリセット '{selected_preset}' を読み込みました")
        
    return agent_name, instructions, selected_model


def show_error_sidebar(error_message):
    """
    サイドバーにエラーメッセージを表示
    
    Args:
        error_message (str): 表示するエラーメッセージ
    """
    st.sidebar.error(error_message) 