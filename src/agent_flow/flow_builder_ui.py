import streamlit as st
import uuid
from typing import Dict, List, Optional, Tuple, Any
import json
import base64
from src.agent_builder.agent_types import AgentFlow, AgentConfig, AgentConnection, ConnectionType

def agent_flow_builder_ui():
    """
    エージェントフローを作成・編集するためのUIを表示
    
    Returns:
        AgentFlow or None: 作成・編集されたエージェントフロー、またはNone
    """
    st.header("エージェントフロービルダー")
    
    # セッション状態の初期化
    if "flows" not in st.session_state:
        st.session_state.flows = {}
    
    # 一時的な接続を保存するセッション状態キーを初期化
    if "temp_connections" not in st.session_state:
        st.session_state.temp_connections = {}
    
    if "agents" not in st.session_state or not st.session_state.agents:
        st.warning("エージェントが作成されていません。まず「エージェントビルダー」タブでエージェントを作成してください。")
        return None
    
    # 既存フローを選択するオプション
    flow_ids = list(st.session_state.flows.keys())
    flow_names = ["新規フロー作成"] + [flow.name for flow in st.session_state.flows.values()]
    
    selected_index = st.selectbox(
        "フローを選択または新規作成",
        range(len(flow_names)),
        format_func=lambda i: flow_names[i]
    )
    
    # 新規作成または既存フローの編集
    editing_new = selected_index == 0
    current_flow = None if editing_new else st.session_state.flows[flow_ids[selected_index - 1]]
    
    # フロー名と説明の入力
    col1, col2 = st.columns(2)
    with col1:
        flow_name = st.text_input(
            "フロー名", 
            value="" if editing_new else current_flow.name
        )
    
    with col2:
        flow_description = st.text_input(
            "フロー説明", 
            value="" if editing_new else current_flow.description
        )
    
    # フローに含めるエージェントの選択
    available_agents = list(st.session_state.agents.values())
    agent_options = {agent.id: f"{agent.name} ({agent.model})" for agent in available_agents}
    
    selected_agent_ids = []
    if not editing_new and current_flow and current_flow.agents:
        selected_agent_ids = [agent.id for agent in current_flow.agents]
    
    selected_agents = st.multiselect(
        "フローに含めるエージェント",
        options=list(agent_options.keys()),
        default=selected_agent_ids,
        format_func=lambda x: agent_options.get(x, x)
    )
    
    # 選択されたエージェントから実際のAgentConfigオブジェクトを取得
    flow_agents = [st.session_state.agents[agent_id] for agent_id in selected_agents if agent_id in st.session_state.agents]
    
    # エントリーポイントの選択
    if flow_agents:
        agent_map = {agent.id: agent.name for agent in flow_agents}
        
        default_entry_point = None
        if not editing_new and current_flow and current_flow.entry_point_id in agent_map:
            default_entry_point = current_flow.entry_point_id
        elif flow_agents:
            default_entry_point = flow_agents[0].id
        
        entry_point_id = st.selectbox(
            "エントリーポイント（最初に実行するエージェント）",
            options=list(agent_map.keys()),
            format_func=lambda x: agent_map.get(x, x),
            index=list(agent_map.keys()).index(default_entry_point) if default_entry_point else 0
        )
    else:
        entry_point_id = None
        st.warning("フローにエージェントを追加してください")
    
    # 接続の作成・編集
    if len(flow_agents) >= 2:
        st.subheader("エージェント間の接続を設定")
        
        # フロー固有の一時接続キーを作成
        temp_connection_key = f"temp_conn_{flow_id if not editing_new else 'new_flow'}"
        
        # 既存の接続を取得して明示的にコピー
        existing_connections = []
        
        # 一時保存された接続情報があれば、そちらを優先して使用
        if temp_connection_key in st.session_state.temp_connections:
            st.info(f"一時保存された接続情報を使用します（{len(st.session_state.temp_connections[temp_connection_key])}個）")
            existing_connections = st.session_state.temp_connections[temp_connection_key]
        # なければ既存のフローから読み込み
        elif not editing_new and current_flow and hasattr(current_flow, 'connections'):
            # 単なる参照ではなく、各接続を新しいオブジェクトとしてコピー
            for conn in current_flow.connections:
                existing_connections.append(
                    AgentConnection(
                        id=conn.id,
                        source_id=conn.source_id,
                        target_id=conn.target_id,
                        connection_type=conn.connection_type,
                        condition=conn.condition
                    )
                )
            
            # デバッグ情報
            st.info(f"既存のフローから {len(existing_connections)} 個の接続を読み込みました")
            
        # 新しい接続の作成フォーム
        with st.expander("新しい接続を追加", expanded=len(existing_connections) == 0):
            connection_ui(flow_agents, existing_connections, temp_connection_key)
        
        # 既存の接続を表示
        if existing_connections:
            st.write("既存の接続:")
            for i, conn in enumerate(existing_connections):
                source_name = next((a.name for a in flow_agents if a.id == conn.source_id), "不明")
                target_name = next((a.name for a in flow_agents if a.id == conn.target_id), "不明")
                conn_type_name = "ハンドオフ" if conn.connection_type == ConnectionType.HANDOFF else "順次実行" if conn.connection_type == ConnectionType.SEQUENTIAL else "条件分岐"
                
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.text(f"{source_name} → {target_name}")
                with col2:
                    st.text(f"接続タイプ: {conn_type_name}")
                with col3:
                    if st.button("削除", key=f"del_conn_{i}"):
                        # 削除した接続を除く新しい接続リストを作成
                        existing_connections = [c for c in existing_connections if c.id != conn.id]
                        
                        # 一時接続情報を更新
                        st.session_state.temp_connections[temp_connection_key] = existing_connections
                        
                        if not editing_new and current_flow:
                            # 現在のフローの接続を更新
                            current_flow.connections = existing_connections
                            st.session_state.flows[current_flow.id] = current_flow
                            
                        st.success("接続を削除しました")
                        # リロードはせず、明示的にセッション状態を更新
    
    # フロー可視化の表示
    if flow_agents and len(flow_agents) > 0:
        st.subheader("フロー可視化")
        flow_visualization(flow_agents, existing_connections if 'existing_connections' in locals() else [], show_code=True)
    
    # 保存ボタン
    col1, col2 = st.columns([1, 1])
    with col1:
        save_clicked = st.button("フローを保存", type="primary", disabled=not (flow_name and flow_description and flow_agents and entry_point_id))
    
    # 削除ボタン（既存フロー編集時のみ表示）
    if not editing_new:
        with col2:
            delete_clicked = st.button("フローを削除", type="secondary")
            if delete_clicked and current_flow:
                # フローの削除処理
                st.session_state.flows.pop(current_flow.id, None)
                st.success(f"フロー '{current_flow.name}' を削除しました")
                st.rerun()
    
    # フロー保存処理
    if save_clicked and flow_name and flow_description and flow_agents and entry_point_id:
        flow_id = str(uuid.uuid4()) if editing_new else current_flow.id
        
        # 接続情報を確保するために、明示的に既存の接続リストを新しいリストとしてコピー
        connections = []
        
        # 一時保存された接続情報があればそれを使用
        temp_connection_key = f"temp_conn_{flow_id if not editing_new else 'new_flow'}"
        if temp_connection_key in st.session_state.temp_connections:
            # 一時保存された接続情報を使用
            connection_source = st.session_state.temp_connections[temp_connection_key]
            st.info(f"一時保存された接続情報を使用します（{len(connection_source)}個）")
        # 既存の接続がある場合
        elif 'existing_connections' in locals() and existing_connections:
            connection_source = existing_connections
        else:
            connection_source = []
        
        # 接続情報を明示的にコピー
        for conn in connection_source:
            # 各接続を新しいオブジェクトとして明示的にコピー
            connections.append(
                AgentConnection(
                    id=conn.id,
                    source_id=conn.source_id,
                    target_id=conn.target_id,
                    connection_type=conn.connection_type,
                    condition=conn.condition
                )
            )
        
        # デバッグログ - 保存前の接続情報
        st.warning(f"保存するフロー内の接続数: {len(connections)}")
        for i, conn in enumerate(connections):
            source_name = next((a.name for a in flow_agents if a.id == conn.source_id), "不明")
            target_name = next((a.name for a in flow_agents if a.id == conn.target_id), "不明")
            st.warning(f"接続 {i+1}: {source_name}({conn.source_id}) → {target_name}({conn.target_id}) (タイプ: {conn.connection_type})")
        
        # 新しいフロー設定を作成
        flow_config = AgentFlow(
            id=flow_id,
            name=flow_name,
            description=flow_description,
            agents=flow_agents.copy(),  # リストをコピー
            connections=connections,    # 既にコピー済み
            entry_point_id=entry_point_id
        )
        
        # フローをセッション状態に保存
        st.session_state.flows[flow_id] = flow_config
        
        # 一時保存された接続情報をクリア
        if temp_connection_key in st.session_state.temp_connections:
            del st.session_state.temp_connections[temp_connection_key]
        
        if editing_new:
            st.success(f"新しいフロー '{flow_name}' を作成しました")
        else:
            st.success(f"フロー '{flow_name}' を更新しました")
        
        # 保存が完了したら画面を再読み込みして状態を反映
        st.rerun()
        
        return flow_config
    
    return None

def connection_ui(agents: List[AgentConfig], connections: List[AgentConnection], temp_connection_key: str):
    """
    エージェント間の新しい接続を作成するUI
    
    Args:
        agents: 接続可能なエージェントのリスト
        connections: 既存の接続のリスト
        temp_connection_key: 一時的な接続情報を保存するためのキー
    """
    if len(agents) < 2:
        st.info("接続を作成するには、少なくとも2つのエージェントが必要です。")
        return
    
    # 接続リストの確認
    st.write(f"現在の接続数: {len(connections)}")
    
    # キーを追加して各インスタンスで一意のウィジェットを作成
    form_key = "connection_form_" + str(hash("".join([a.id for a in agents])))
    
    # フォームを使って一度に送信するように変更
    with st.form(key=form_key):
        agent_map = {agent.id: agent.name for agent in agents}
        
        col1, col2 = st.columns(2)
        
        with col1:
            source_id = st.selectbox(
                "接続元エージェント",
                options=list(agent_map.keys()),
                format_func=lambda x: agent_map.get(x, x),
                key=f"{form_key}_source"
            )
        
        with col2:
            target_options = [aid for aid in list(agent_map.keys()) if aid != source_id]
            if target_options:
                target_id = st.selectbox(
                    "接続先エージェント",
                    options=target_options,
                    format_func=lambda x: agent_map.get(x, x),
                    key=f"{form_key}_target"
                )
            else:
                st.error("接続先エージェントがありません")
                target_id = None
        
        connection_type = st.selectbox(
            "接続タイプ",
            options=[ConnectionType.HANDOFF, ConnectionType.SEQUENTIAL, ConnectionType.CONDITIONAL],
            format_func=lambda x: "ハンドオフ" if x == ConnectionType.HANDOFF else "順次実行" if x == ConnectionType.SEQUENTIAL else "条件分岐",
            key=f"{form_key}_type"
        )
        
        condition = None
        if connection_type == ConnectionType.CONDITIONAL:
            condition = st.text_area(
                "条件式 (Python形式)",
                value="response.contains('注文') or category == 'order'",
                help="この条件が True の場合に接続先エージェントが実行されます。",
                key=f"{form_key}_condition"
            )
        
        # 追加ボタン
        submitted = st.form_submit_button("接続を追加")
    
    if submitted and target_id:
        # 既に同じ接続元と接続先の組み合わせが存在するかチェック
        existing = any(conn.source_id == source_id and conn.target_id == target_id for conn in connections)
        
        if existing:
            st.warning("同じエージェント間の接続が既に存在します。")
        elif source_id == target_id:
            st.warning("自己参照の接続はサポートされていません。")
        else:
            # 新しい接続を作成
            new_connection = AgentConnection(
                id=str(uuid.uuid4()),
                source_id=source_id,
                target_id=target_id,
                connection_type=connection_type,
                condition=condition
            )
            
            # ここがキーポイント：接続リストに追加する
            connections.append(new_connection)
            
            # 接続情報をセッション状態に保存して、リロード時も保持されるようにする
            st.session_state.temp_connections[temp_connection_key] = connections
            
            # デバッグ情報を追加
            source_name = agent_map.get(source_id, "不明")
            target_name = agent_map.get(target_id, "不明")
            st.success(f"新しい接続を追加しました: {source_name} → {target_name}")
            st.info(f"接続数: {len(connections)}")

def flow_visualization(agents: List[AgentConfig], connections: List[AgentConnection], show_code: bool = True):
    """
    エージェントフローを可視化して表示
    
    Args:
        agents: フロー内のエージェントリスト
        connections: エージェント間の接続リスト
        show_code: Mermaidコードを表示するかどうか（デフォルトはTrue）
    """
    if not agents:
        return
    
    # デバッグ情報
    if show_code:
        st.write(f"**エージェント数:** {len(agents)}")
        st.write(f"**接続数:** {len(connections)}")
        for conn in connections:
            source_name = next((a.name for a in agents if a.id == conn.source_id), "不明")
            target_name = next((a.name for a in agents if a.id == conn.target_id), "不明")
            st.write(f"- 接続: {source_name} → {target_name} ({conn.connection_type})")
    
    # Mermaid.jsを使ったフロー図の生成
    mermaid_code = "graph LR\n"
    
    # エージェントのノードを追加（短いID表現を使用）
    agent_short_ids = {}
    for i, agent in enumerate(agents):
        short_id = f"A{i+1}"
        agent_short_ids[agent.id] = short_id
        mermaid_code += f"    {short_id}[{agent.name}]\n"
    
    # 接続を追加（短いID表現を使用）
    for conn in connections:
        source_id = agent_short_ids.get(conn.source_id, conn.source_id)
        target_id = agent_short_ids.get(conn.target_id, conn.target_id)
        
        if conn.connection_type == ConnectionType.HANDOFF:
            mermaid_code += f"    {source_id} -->|ハンドオフ| {target_id}\n"
        elif conn.connection_type == ConnectionType.SEQUENTIAL:
            mermaid_code += f"    {source_id} -->|順次実行| {target_id}\n"
        elif conn.connection_type == ConnectionType.CONDITIONAL:
            mermaid_code += f"    {source_id} -->|条件分岐| {target_id}\n"
    
    # HTML埋め込みによるMermaid図の表示
    html = f"""
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <div class="mermaid">
    {mermaid_code}
    </div>
    <script>
        mermaid.initialize({{ startOnLoad: true }});
    </script>
    """
    
    # コード表示（デバッグ用）- list_flows_ui 内では使用しない
    if show_code:
        st.write("**フロー図コード (Mermaid):**")
        st.code(mermaid_code, language="markdown")
    
    # HTMLをiframeで埋め込み
    st.components.v1.html(html, height=300)

def list_flows_ui():
    """
    作成済みのフロー一覧を表示
    """
    st.subheader("作成済みフロー")
    
    if "flows" not in st.session_state or not st.session_state.flows:
        st.info("まだフローが作成されていません。上記のフロービルダーでフローを作成してください。")
        return
    
    for flow_id, flow in st.session_state.flows.items():
        with st.expander(f"{flow.name} - {flow.description}"):
            # エントリーポイントのエージェント名を取得
            entry_agent_name = "不明"
            for agent in flow.agents:
                if agent.id == flow.entry_point_id:
                    entry_agent_name = agent.name
                    break
            
            st.write(f"**エントリーポイント:** {entry_agent_name}")
            st.write(f"**エージェント数:** {len(flow.agents)}")
            st.write(f"**接続数:** {len(flow.connections)}")
            
            # フロー可視化
            flow_visualization(flow.agents, flow.connections, show_code=False) 