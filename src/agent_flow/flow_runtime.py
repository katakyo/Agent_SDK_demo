import asyncio
import streamlit as st
from typing import Dict, List, Optional, Any
import json
import time
from datetime import datetime

from agents import Agent, Runner
from src.agent_builder.agent_types import AgentConfig, AgentFlow, AgentConnection, ConnectionType
from src.utils.async_helpers import run_async

class FlowRuntime:
    """
    エージェントフローを実行するためのランタイムエンジン
    """
    
    def __init__(self, flow: AgentFlow):
        """
        FlowRuntimeの初期化
        
        Args:
            flow: 実行するエージェントフロー
        """
        self.flow = flow
        self.agents_map = {}  # エージェントID -> Agent オブジェクトのマップ
        self.chat_history = []
        self.logs = []
        self.current_agent_id = flow.entry_point_id
    
    def log(self, message: str, level: str = "INFO"):
        """ログメッセージを記録"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append({"timestamp": timestamp, "level": level, "message": message})
    
    def initialize_agents(self):
        """
        フロー内のすべてのエージェントを初期化する
        """
        for agent_config in self.flow.agents:
            # OpenAI Agents SDKのAgentオブジェクトを作成
            agent = Agent(
                name=agent_config.name,
                instructions=agent_config.instructions,
                model=agent_config.model,
                # tools=agent_config.tools  # これでは動作しない
                # 実際はツールの実装が必要だが、簡易化のため今回は空のツールリストを渡す
                tools=[]  # 必要に応じてツールを設定
            )
            self.agents_map[agent_config.id] = agent
            self.log(f"エージェント '{agent_config.name}' を初期化しました")
    
    def get_next_agent_id(self, current_agent_id: str, response: str) -> Optional[str]:
        """
        次に実行するエージェントのIDを決定
        
        Args:
            current_agent_id: 現在のエージェントID
            response: 現在のエージェントの応答
            
        Returns:
            Optional[str]: 次のエージェントID、またはNone（終了時）
        """
        # 現在のエージェントから出る接続を取得
        outgoing_connections = [
            conn for conn in self.flow.connections if conn.source_id == current_agent_id
        ]
        
        self.log(f"出力接続数: {len(outgoing_connections)}")
        
        if not outgoing_connections:
            self.log("次の接続が見つかりませんでした")
            return None  # 接続がない場合は終了
        
        for conn in outgoing_connections:
            target_name = next((a.name for a in self.flow.agents if a.id == conn.target_id), "不明")
            self.log(f"接続を評価中: {conn.source_id} -> {conn.target_id} ({target_name}), タイプ: {conn.connection_type}")
            
            if conn.connection_type == ConnectionType.HANDOFF:
                # ハンドオフの場合は常に次のエージェントに移動
                self.log(f"ハンドオフ接続: 次のエージェント = {conn.target_id}")
                return conn.target_id
            elif conn.connection_type == ConnectionType.SEQUENTIAL:
                # 順次実行の場合も常に次のエージェントに移動
                self.log(f"順次実行接続: 次のエージェント = {conn.target_id}")
                return conn.target_id
            elif conn.connection_type == ConnectionType.CONDITIONAL:
                # 条件分岐の場合は条件を評価
                if conn.condition:
                    try:
                        self.log(f"条件分岐を評価中: {conn.condition}")
                        # 単純化のため、ここでは応答のテキストに特定の単語が含まれるかで判断
                        # より複雑な条件判断が必要な場合は、プロパーなeval環境を構築する必要がある
                        context = {
                            "response": response,
                            "contains": lambda x: x.lower() in response.lower()
                        }
                        result = eval(conn.condition, {"__builtins__": {}}, context)
                        self.log(f"条件評価結果: {result}")
                        if result:
                            self.log(f"条件が真: 次のエージェント = {conn.target_id}")
                            return conn.target_id
                        else:
                            self.log("条件が偽: スキップします")
                    except Exception as e:
                        self.log(f"条件評価エラー: {str(e)}", "ERROR")
                else:
                    self.log("条件が指定されていません", "WARNING")
        
        self.log("適切な次のエージェントが見つかりませんでした")
        return None  # 適切な次のエージェントがない場合は終了
    
    async def execute_agent(self, agent_id: str, user_input: str) -> str:
        """
        エージェントを実行して応答を取得
        
        Args:
            agent_id: 実行するエージェントのID
            user_input: ユーザー入力
            
        Returns:
            str: エージェントの応答
        """
        agent = self.agents_map.get(agent_id)
        if not agent:
            self.log(f"エージェントID '{agent_id}' が見つかりません", "ERROR")
            return "エラー: エージェントが見つかりません"
        
        try:
            # エージェント名を取得
            agent_name = next((a.name for a in self.flow.agents if a.id == agent_id), "不明")
            self.log(f"エージェント '{agent_name}' を実行中...")
            self.log(f"入力: {user_input[:50]}...")
            
            # エージェントの実行
            self.log("Runner.run を呼び出し中...")
            result = await Runner.run(agent, user_input)
            self.log("Runner.run の実行が完了")
            
            if hasattr(result, 'final_output'):
                response = result.final_output
                self.log(f"エージェント '{agent_name}' からの応答: {response[:50]}...")
                return response
            else:
                self.log(f"エージェント結果に final_output がありません: {str(result)}", "WARNING")
                return f"応答を取得できませんでした: {str(result)}"
        except Exception as e:
            import traceback
            self.log(f"エージェント実行エラー: {str(e)}", "ERROR")
            self.log(f"詳細なエラー: {traceback.format_exc()}", "ERROR")
            return f"エラー: {str(e)}"
    
    async def run_flow(self, user_input: str, chat_placeholder=None, log_placeholder=None):
        """
        フロー全体を実行
        
        Args:
            user_input: ユーザー入力
            chat_placeholder: チャット表示用のPlaceholderオブジェクト
            log_placeholder: ログ表示用のPlaceholderオブジェクト
        
        Returns:
            Dict: 実行結果
        """
        self.initialize_agents()
        
        # デバッグ: 初期化されたエージェントの確認
        self.log(f"初期化されたエージェント数: {len(self.agents_map)}")
        for agent_id, agent in self.agents_map.items():
            agent_name = next((a.name for a in self.flow.agents if a.id == agent_id), "不明")
            self.log(f"初期化済みエージェント: ID={agent_id}, 名前={agent_name}, モデル={agent.model}")
        
        # デバッグ: 接続情報の確認
        self.log(f"接続数: {len(self.flow.connections)}")
        for conn in self.flow.connections:
            source_name = next((a.name for a in self.flow.agents if a.id == conn.source_id), "不明")
            target_name = next((a.name for a in self.flow.agents if a.id == conn.target_id), "不明")
            self.log(f"接続: {source_name} -> {target_name} (タイプ: {conn.connection_type})")
        
        # ユーザーメッセージをチャット履歴に追加
        self.chat_history.append({"role": "user", "content": user_input})
        
        # チャット表示を更新
        if chat_placeholder:
            chat_placeholder.markdown(self._format_chat_history())
        
        # 現在の入力
        current_input = user_input
        current_agent_id = self.flow.entry_point_id
        self.log(f"フローの開始: エントリーポイント '{current_agent_id}'")
        
        # 実行カウンター (無限ループ防止)
        execution_count = 0
        max_executions = 10  # 安全のため最大実行回数を制限
        
        while current_agent_id and execution_count < max_executions:
            execution_count += 1
            self.log(f"実行回数: {execution_count}/{max_executions}")
            
            # エージェントの実行
            self.log(f"エージェント '{current_agent_id}' を実行します")
            response = await self.execute_agent(current_agent_id, current_input)
            
            # 応答をチャット履歴に追加
            agent_name = next((a.name for a in self.flow.agents if a.id == current_agent_id), "Agent")
            self.chat_history.append({"role": "assistant", "content": response, "name": agent_name})
            
            # チャット表示を更新
            if chat_placeholder:
                chat_placeholder.markdown(self._format_chat_history())
            
            # ログ表示を更新
            if log_placeholder:
                log_placeholder.markdown(self._format_logs())
            
            # 次のエージェントの決定
            self.log("次のエージェントを決定中...")
            next_agent_id = self.get_next_agent_id(current_agent_id, response)
            
            if next_agent_id:
                # 次のエージェントがある場合
                agent_name = next((a.name for a in self.flow.agents if a.id == next_agent_id), "不明")
                self.log(f"次のエージェント: '{agent_name}' (ID: {next_agent_id}) に移行します")
                
                # 次のエージェントへの入力は現在のエージェントの応答
                current_input = response
                current_agent_id = next_agent_id
            else:
                # 次のエージェントがない場合はフロー終了
                self.log(f"フローを完了しました (次のエージェントはありません)")
                current_agent_id = None
        
        if execution_count >= max_executions:
            self.log(f"最大実行回数 ({max_executions}) に達したため、フローを終了します", "WARNING")
        
        return {
            "chat_history": self.chat_history,
            "logs": self.logs,
            "final_response": self.chat_history[-1]["content"] if self.chat_history else ""
        }
    
    def _format_chat_history(self) -> str:
        """チャット履歴を整形して表示用の文字列を返す"""
        formatted = ""
        for msg in self.chat_history:
            if msg["role"] == "user":
                formatted += f"**ユーザー:**\n{msg['content']}\n\n"
            else:
                name = msg.get("name", "Assistant")
                formatted += f"**{name}:**\n{msg['content']}\n\n"
        return formatted
    
    def _format_logs(self) -> str:
        """ログを整形して表示用の文字列を返す"""
        formatted = "### 実行ログ\n\n"
        for log in self.logs:
            timestamp = log["timestamp"]
            level = log["level"]
            message = log["message"]
            formatted += f"**{timestamp}** [{level}] {message}\n\n"
        return formatted

def run_flow_ui(flow: AgentFlow):
    """
    フロー実行のUIを表示
    
    Args:
        flow: 実行するエージェントフロー
    """
    st.header(f"フロー実行: {flow.name}")
    st.write(flow.description)
    
    # デバッグ情報 - フロー実行前の接続情報の確認
    st.subheader("フロー構成情報")
    st.write(f"**エージェント数:** {len(flow.agents)}")
    st.write(f"**接続数:** {len(flow.connections)}")
    
    # 接続情報の表示
    if flow.connections:
        st.write("**接続詳細:**")
        for i, conn in enumerate(flow.connections):
            source_name = next((a.name for a in flow.agents if a.id == conn.source_id), "不明")
            target_name = next((a.name for a in flow.agents if a.id == conn.target_id), "不明")
            conn_type = "ハンドオフ" if conn.connection_type == ConnectionType.HANDOFF else "順次実行" if conn.connection_type == ConnectionType.SEQUENTIAL else "条件分岐"
            st.write(f"{i+1}. {source_name} → {target_name} (タイプ: {conn_type})")
    else:
        st.warning("⚠️ 接続が設定されていません。フロービルダーで接続を追加してください。")
    
    # フロー可視化
    from src.agent_flow.flow_builder_ui import flow_visualization
    flow_visualization(flow.agents, flow.connections, show_code=True)
    
    # 実行セクション
    st.subheader("フロー実行")
    
    user_input = st.text_area("メッセージを入力してください", height=100)
    run_button = st.button("フローを実行", type="primary", disabled=not user_input)
    
    # チャット表示用のプレースホルダー
    chat_placeholder = st.empty()
    
    # ログ表示用のプレースホルダー
    log_container = st.expander("実行ログ", expanded=True)
    log_placeholder = log_container.empty()
    
    if run_button and user_input:
        with st.spinner("フローを実行中..."):
            # フローランタイムの初期化と実行
            runtime = FlowRuntime(flow)
            
            # ログ表示の初期化
            log_placeholder.markdown("### 実行ログ\n\n実行を開始しています...")
            
            # 非同期処理を実行
            result = run_async(runtime.run_flow(user_input, chat_placeholder, log_placeholder))
            
            st.success("フローの実行が完了しました")
            
            # 結果表示
            if "final_response" in result:
                pass  # 既にチャット履歴に表示されているため何もしない 