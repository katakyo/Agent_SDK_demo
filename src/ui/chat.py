import streamlit as st
from src.models.agent import AgentManager, RateLimitError, AgentError
from src.utils.async_helpers import run_async

def initialize_chat():
    """
    チャットインターフェースの初期化
    
    Returns:
        str or None: ユーザーの入力（入力がない場合はNone）
    """
    st.header("対話")

    # セッション状態の初期化
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 過去のメッセージを表示
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ユーザー入力
    return st.chat_input("メッセージを入力してください...")


def process_message(user_input, agent_name, instructions, selected_model):
    """
    ユーザーメッセージを処理し、AIの応答を取得する
    
    Args:
        user_input (str): ユーザーの入力メッセージ
        agent_name (str): エージェント名
        instructions (str): エージェントへの指示
        selected_model (str): 使用するモデル名
    """
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
        agent = AgentManager.create_agent(
            name=agent_name,
            instructions=instructions,
            model=selected_model
        )
        
        # 実行と結果の取得
        with st.spinner('レスポンスを生成中...'):
            # 非同期処理を実行
            response = run_async(AgentManager.run_agent(agent, user_input))
        
        # アシスタントメッセージをチャット履歴に追加
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # 応答を表示（処理中を上書き）
        message_placeholder.markdown(response)
        
        return None  # エラーなし
        
    except RateLimitError as e:
        message_placeholder.error(str(e))
        return "対処方法:\n1. OpenAIダッシュボードでクォータを確認\n2. 請求情報を更新\n3. 別のAPIキーを使用"
    except AgentError as e:
        message_placeholder.error(str(e))
        return f"詳細エラー: {str(e)}"
    except Exception as e:
        message_placeholder.error(f"予期しないエラーが発生しました: {e}")
        return f"予期しないエラー: {str(e)}" 