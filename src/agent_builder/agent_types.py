import uuid
from typing import List, Dict, Optional, Any, Callable
from pydantic import BaseModel, Field

class AgentConfig(BaseModel):
    """エージェント設定クラス"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    instructions: str
    model: str
    tools: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """エージェント設定を辞書形式で返す"""
        return {
            "id": self.id,
            "name": self.name,
            "instructions": self.instructions,
            "model": self.model,
            "tools": self.tools
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """辞書からエージェント設定を作成"""
        return cls(**data)

class ConnectionType:
    """エージェント接続タイプ"""
    HANDOFF = "handoff"         # エージェント間のハンドオフ
    SEQUENTIAL = "sequential"   # 順次実行
    CONDITIONAL = "conditional" # 条件分岐

class AgentConnection(BaseModel):
    """エージェント間の接続定義"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    target_id: str
    connection_type: str
    condition: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """接続情報を辞書形式で返す"""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "connection_type": self.connection_type,
            "condition": self.condition
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConnection':
        """辞書から接続情報を作成"""
        return cls(**data)

class AgentFlow(BaseModel):
    """エージェントフロー定義"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    agents: List[AgentConfig] = []
    connections: List[AgentConnection] = []
    entry_point_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """フロー情報を辞書形式で返す"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "agents": [agent.to_dict() for agent in self.agents],
            "connections": [conn.to_dict() for conn in self.connections],
            "entry_point_id": self.entry_point_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentFlow':
        """辞書からフロー情報を作成"""
        flow_data = {
            "id": data.get("id", str(uuid.uuid4())),
            "name": data["name"],
            "description": data["description"],
            "agents": [AgentConfig.from_dict(agent_data) for agent_data in data.get("agents", [])],
            "connections": [AgentConnection.from_dict(conn_data) for conn_data in data.get("connections", [])],
            "entry_point_id": data.get("entry_point_id")
        }
        return cls(**flow_data)

# 定義済みツール
AVAILABLE_TOOLS = {
    "web_search": "ウェブ検索を実行",
    "calculator": "計算を実行",
    "weather": "天気情報を取得",
    "calendar": "カレンダー情報を管理",
    "email": "メール操作",
    "document": "ドキュメント操作"
}

# 定義済みエージェントテンプレート
AGENT_TEMPLATES = {
    "assistant": {
        "name": "汎用アシスタント",
        "instructions": "あなたは役立つアシスタントです。ユーザーの質問に丁寧に回答してください。",
        "model": "gpt-3.5-turbo"
    },
    "researcher": {
        "name": "リサーチャー",
        "instructions": "あなたはリサーチの専門家です。情報を収集し、整理して提供してください。",
        "model": "gpt-4"
    },
    "translator": {
        "name": "翻訳者",
        "instructions": "あなたは翻訳の専門家です。テキストを指定された言語に翻訳してください。",
        "model": "gpt-3.5-turbo"
    },
    "programmer": {
        "name": "プログラマー",
        "instructions": "あなたはプログラミングの専門家です。コードの説明、作成、デバッグを行います。",
        "model": "gpt-4"
    }
} 