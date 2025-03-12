import streamlit as st
import uuid
from typing import Dict, List, Any
from src.agent_builder.agent_types import AgentConfig, AGENT_TEMPLATES, AVAILABLE_TOOLS
from src.config.settings import AVAILABLE_MODELS

def agent_builder_ui():
    """
    エージェントを作成・編集するためのUIを表示
    
    Returns:
        AgentConfig or None: 作成・編集されたエージェント設定、またはNone
    """
    st.header("エージェントビルダー")
    
    # セッション状態の初期化
    if "agents" not in st.session_state:
        st.session_state.agents = {}
    
    # 既存エージェントを選択するオプション
    agent_ids = list(st.session_state.agents.keys())
    agent_names = ["新規エージェント作成"] + [agent.name for agent in st.session_state.agents.values()]
    
    selected_index = st.selectbox(
        "エージェントを選択または新規作成",
        range(len(agent_names)),
        format_func=lambda i: agent_names[i]
    )
    
    # 新規作成または既存エージェントの編集
    editing_new = selected_index == 0
    current_agent = None if editing_new else st.session_state.agents[agent_ids[selected_index - 1]]
    
    # エージェントテンプレートの選択
    template_options = ["カスタム"] + list(AGENT_TEMPLATES.keys())
    template_index = st.selectbox(
        "テンプレートを選択",
        range(len(template_options)),
        format_func=lambda i: template_options[i],
        help="事前定義されたエージェントテンプレートを選択すると、設定が自動入力されます。"
    )
    
    selected_template = None if template_index == 0 else AGENT_TEMPLATES[template_options[template_index]]
    
    # エージェント名の入力
    default_name = "" if editing_new else current_agent.name
    if selected_template:
        default_name = selected_template["name"]
    
    agent_name = st.text_input("エージェント名", value=default_name)
    
    # エージェントの指示の入力
    default_instructions = "" if editing_new else current_agent.instructions
    if selected_template:
        default_instructions = selected_template["instructions"]
    
    agent_instructions = st.text_area(
        "エージェント指示", 
        value=default_instructions,
        height=150,
        help="エージェントへの詳細な指示を入力します。エージェントの役割、対応方法、制約などを指定できます。"
    )
    
    # モデルの選択
    default_model = AVAILABLE_MODELS[0] if editing_new else current_agent.model
    if selected_template:
        default_model = selected_template["model"]
    
    selected_model = st.selectbox(
        "モデル",
        AVAILABLE_MODELS,
        index=AVAILABLE_MODELS.index(default_model) if default_model in AVAILABLE_MODELS else 0
    )
    
    # ツールの選択
    default_tools = [] if editing_new else current_agent.tools
    selected_tools = st.multiselect(
        "利用可能なツール",
        options=list(AVAILABLE_TOOLS.keys()),
        default=default_tools,
        format_func=lambda x: f"{x} - {AVAILABLE_TOOLS[x]}"
    )
    
    # 保存ボタン
    col1, col2 = st.columns([1, 1])
    with col1:
        save_clicked = st.button("エージェントを保存", type="primary")
    
    # 削除ボタン（既存エージェント編集時のみ表示）
    if not editing_new:
        with col2:
            delete_clicked = st.button("エージェントを削除", type="secondary")
            if delete_clicked and current_agent:
                # エージェントの削除処理
                st.session_state.agents.pop(current_agent.id, None)
                st.success(f"エージェント '{current_agent.name}' を削除しました")
                st.rerun()
    
    # エージェント保存処理
    if save_clicked and agent_name and agent_instructions:
        agent_id = str(uuid.uuid4()) if editing_new else current_agent.id
        
        # 新しいエージェント設定を作成
        agent_config = AgentConfig(
            id=agent_id,
            name=agent_name,
            instructions=agent_instructions,
            model=selected_model,
            tools=selected_tools
        )
        
        # エージェントをセッション状態に保存
        st.session_state.agents[agent_id] = agent_config
        
        if editing_new:
            st.success(f"新しいエージェント '{agent_name}' を作成しました")
        else:
            st.success(f"エージェント '{agent_name}' を更新しました")
        
        return agent_config
    
    return None

def list_agents_ui():
    """
    作成済みのエージェント一覧を表示
    """
    st.subheader("作成済みエージェント")
    
    if "agents" not in st.session_state or not st.session_state.agents:
        st.info("まだエージェントが作成されていません。上記のエージェントビルダーでエージェントを作成してください。")
        return
    
    for agent_id, agent in st.session_state.agents.items():
        with st.expander(f"{agent.name} ({agent.model})"):
            st.write(f"**指示:** {agent.instructions}")
            if agent.tools:
                st.write(f"**ツール:** {', '.join(agent.tools)}")
            else:
                st.write("**ツール:** なし") 