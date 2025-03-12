import os
import streamlit as st
import sys
import json
import pickle
from pathlib import Path

# スタイルとタイトル設定
st.set_page_config(page_title="OpenAI Multi-Agent Builder", layout="wide")
st.title("OpenAI マルチエージェントビルダー")
st.markdown("複数のAIエージェントを組み合わせたワークフローを構築・実行できます")

# モジュールからインポート
from src.config.settings import load_config
from src.agent_builder import agent_builder_ui, list_agents_ui
from src.agent_flow import agent_flow_builder_ui, list_flows_ui, run_flow_ui

# セッションデータの保存先
DATA_DIR = Path("data")
AGENTS_FILE = DATA_DIR / "agents.pickle"
FLOWS_FILE = DATA_DIR / "flows.pickle"

# データディレクトリが存在しない場合は作成
DATA_DIR.mkdir(exist_ok=True)

# 保存されたデータの読み込み
def load_saved_data():
    try:
        if AGENTS_FILE.exists():
            with open(AGENTS_FILE, "rb") as f:
                st.session_state.agents = pickle.load(f)
        
        if FLOWS_FILE.exists():
            with open(FLOWS_FILE, "rb") as f:
                st.session_state.flows = pickle.load(f)
                
        st.sidebar.success("保存されたデータを読み込みました")
    except Exception as e:
        st.sidebar.warning(f"データの読み込みに失敗しました: {str(e)}")

# データの保存
def save_data():
    try:
        with open(AGENTS_FILE, "wb") as f:
            pickle.dump(st.session_state.agents, f)
        
        with open(FLOWS_FILE, "wb") as f:
            pickle.dump(st.session_state.flows, f)
            
        return True
    except Exception as e:
        st.sidebar.error(f"データの保存に失敗しました: {str(e)}")
        return False

# 設定の読み込み
api_key = load_config()
if api_key is None:
    st.error("APIキーが見つかりません。'.env'ファイルを確認してください。")
    st.stop()
else:
    # 環境変数を設定
    os.environ["OPENAI_API_KEY"] = api_key

# 既存データの読み込み
load_saved_data()

# サイドバー
st.sidebar.title("ナビゲーション")
page = st.sidebar.radio(
    "ページを選択",
    ["エージェントビルダー", "フロービルダー", "フロー実行"]
)

# 保存ボタン
if st.sidebar.button("データを保存", type="primary"):
    if save_data():
        st.sidebar.success("データを保存しました")

# ページ分岐
if page == "エージェントビルダー":
    # エージェントビルダー画面
    agent_builder_ui()
    st.markdown("---")
    list_agents_ui()

elif page == "フロービルダー":
    # フロービルダー画面
    agent_flow_builder_ui()
    st.markdown("---")
    list_flows_ui()

elif page == "フロー実行":
    # フロー実行画面
    st.header("フロー実行")
    
    if "flows" not in st.session_state or not st.session_state.flows:
        st.warning("実行可能なフローがありません。まず「フロービルダー」タブでフローを作成してください。")
    else:
        # フロー選択
        flow_ids = list(st.session_state.flows.keys())
        flow_names = [flow.name for flow in st.session_state.flows.values()]
        
        selected_index = st.selectbox(
            "実行するフローを選択",
            range(len(flow_names)),
            format_func=lambda i: flow_names[i]
        )
        
        # 選択されたフローを実行
        selected_flow = st.session_state.flows[flow_ids[selected_index]]
        run_flow_ui(selected_flow) 