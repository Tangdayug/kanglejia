"""
DeepSeek API Client - OpenAI Compatible API
"""
import os
import sys
from typing import Iterator, Optional, Dict, Any

# Disable proxy before importing OpenAI/httpx
for proxy_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
    if proxy_var in os.environ:
        del os.environ[proxy_var]

from common.constant import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

try:
    from openai import OpenAI
except ImportError as e:
    OpenAI = None


class DeepSeekClient:
    """DeepSeek API Client - Compatible with OpenAI API format"""

    def __init__(self):
        """Initialize DeepSeek client"""
        api_key = DEEPSEEK_API_KEY
        base_url = DEEPSEEK_BASE_URL or "https://api.deepseek.com"
        model = DEEPSEEK_MODEL or "deepseek-chat"

        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is not set")

        if OpenAI is None:
            raise ImportError("OpenAI is not available. Please install: pip install openai>=1.12.0")

        # Explicitly create httpx client (avoiding proxy issues)
        import httpx
        http_client = httpx.Client(timeout=60.0)

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            http_client=http_client
        )
        self.model = model

    def chat_completion(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> Any:
        """Create a chat completion."""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        return self.client.chat.completions.create(**kwargs)

    def stream_chat_completion(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Iterator[str]:
        """Stream chat completion."""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        stream = self.client.chat.completions.create(**kwargs)
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def generate_chat_response(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[list[Dict[str, str]]] = None,
        temperature: float = 0.7,
    ) -> str:
        """Generate a chat response with system prompt and context"""
        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": user_message})

        response = self.chat_completion(messages, temperature=temperature)
        return response.choices[0].message.content

    def generate_recommendations(
        self,
        user_profile: Dict[str, Any],
        conversation_history: Optional[list[Dict[str, str]]] = None,
        count: int = 3,
    ) -> list[str]:
        """Generate recommended questions"""
        system_prompt = """你是一个健康咨询助手，根据用户的健康档案和对话历史，生成3个相关的、有价值的健康问题建议。

要求：
1. 问题应该针对用户的健康状况或需求
2. 问题应该具体、实用、有价值
3. 每个问题一行，直接输出问题文本，不要编号
4. 不要包含任何其他解释或标注

示例输出：
如何改善睡眠质量？
老年人适合哪些运动？
怎样控制血压？"""

        user_context = f"用户健康信息：\n{str(user_profile)}\n"
        if conversation_history:
            user_context += f"\n最近的对话历史：\n{str(conversation_history[-3:])}\n"

        user_context += "\n请根据上述信息生成3个健康问题建议："

        try:
            response = self.generate_chat_response(
                system_prompt=system_prompt,
                user_message=user_context,
                temperature=0.8,
            )

            recommendations = [
                line.strip()
                for line in response.strip().split("\n")
                if line.strip() and not line.strip().startswith(("1.", "2.", "3.", "（", "1、", "2、", "3、"))
            ]

            cleaned = []
            for rec in recommendations:
                for prefix in ["1. ", "2. ", "3. ", "1、", "2、", "3、", "（1）", "（2）", "（3）"]:
                    if rec.startswith(prefix):
                        rec = rec[len(prefix):]
                if rec:
                    cleaned.append(rec[:100])

            return cleaned[:count] if len(cleaned) >= count else cleaned

        except Exception as e:
            return self._get_fallback_recommendations(user_profile)

    def _get_fallback_recommendations(self, user_profile: Dict[str, Any]) -> list[str]:
        """Get fallback rule-based recommendations"""
        recommendations = [
            "如何改善睡眠质量？",
            "老年人适合哪些运动？",
            "怎样保持健康饮食？",
        ]

        basic_info = user_profile.get("basicInfo", {})
        chronic_disease = user_profile.get("chronicDisease", {})

        if basic_info.get("age", 0) > 65:
            recommendations.insert(0, "老年人如何预防跌倒？")

        diseases = chronic_disease.get("diseases", [])
        if "hypertension" in diseases:
            recommendations.insert(0, "高血压患者需要注意什么？")
        elif "diabetes" in diseases:
            recommendations.insert(0, "糖尿病患者如何控制饮食？")

        return recommendations[:3]


# Singleton instance
_client_instance: Optional[DeepSeekClient] = None


def get_deepseek_client() -> DeepSeekClient:
    """Get or create DeepSeek client singleton"""
    global _client_instance
    if _client_instance is None:
        _client_instance = DeepSeekClient()
    return _client_instance
