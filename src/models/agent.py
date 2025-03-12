from agents import Agent, Runner
import openai
from src.utils.async_helpers import run_async

class AgentManager:
    """
    OpenAI Agent管理クラス
    エージェントの作成と実行を管理する
    """
    
    @staticmethod
    def create_agent(name, instructions, model):
        """
        エージェントを作成する
        
        Args:
            name (str): エージェント名
            instructions (str): エージェントへの指示
            model (str): 使用するモデル名
            
        Returns:
            Agent: 作成されたエージェントオブジェクト
        """
        return Agent(
            name=name,
            instructions=instructions,
            model=model
        )
    
    @staticmethod
    async def run_agent(agent, user_input):
        """
        エージェントを実行してレスポンスを取得する
        
        Args:
            agent (Agent): 実行するエージェント
            user_input (str): ユーザーの入力メッセージ
            
        Returns:
            str: エージェントの応答
        """
        try:
            result = await Runner.run(agent, user_input)
            return result.final_output
        except openai.RateLimitError as e:
            raise RateLimitError(f"OpenAI APIのクォータエラーが発生しました。\nエラー詳細: {e}")
        except Exception as e:
            raise AgentError(f"エラーが発生しました: {e}")


class AgentError(Exception):
    """エージェント実行時のエラー"""
    pass


class RateLimitError(AgentError):
    """APIレート制限エラー"""
    pass 