"""
阿里云百炼（DashScope）嵌入模型客户端
使用 text-embedding-v4 模型
"""
import os
from typing import List, Optional

try:
    import dashscope
except ImportError:
    dashscope = None
    print("Warning: dashscope not installed. Install with: pip install dashscope")


class AliyunEmbedding:
    """阿里云百炼嵌入模型客户端"""

    def __init__(self, api_key: str = None, model: str = "text-embedding-v4"):
        """
        初始化阿里云嵌入模型客户端

        Args:
            api_key: API密钥
            model: 模型名称，默认 text-embedding-v4
        """
        if dashscope is None:
            raise ImportError("dashscope 库未安装，请运行: pip install dashscope")

        if api_key is None:
            api_key = os.getenv("DASHSCOPE_API_KEY")

        if not api_key:
            raise ValueError("DASHSCOPE_API_KEY 环境变量未设置")

        dashscope.api_key = api_key
        self.model = model

    def embed_query(self, text: str) -> List[float]:
        """
        生成单个文本的嵌入向量

        Args:
            text: 输入文本

        Returns:
            嵌入向量（浮点数列表）
        """
        return self.embed_documents([text])[0]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成文本的嵌入向量

        Args:
            texts: 输入文本列表

        Returns:
            嵌入向量列表
        """
        from dashscope import TextEmbedding

        embeddings = []

        # text-embedding-v4 支持批量处理，最多10个文本（阿里云限制）
        batch_size = 10

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            try:
                resp = TextEmbedding.call(
                    model=self.model,
                    input=batch,
                    text_type="document"
                )

                if resp.status_code == 200:
                    for item in resp.output['embeddings']:
                        embeddings.append(item['embedding'])
                else:
                    print(f"API调用失败: {resp.message}")
                    # 抛出异常而不是返回零向量，避免破坏检索功能
                    raise RuntimeError(f"API call failed with status {resp.status_code}: {resp.message}")

            except Exception as e:
                print(f"嵌入向量生成出错: {e}")
                # 抛出异常而不是返回零向量，避免破坏检索功能
                raise RuntimeError(f"Failed to generate embeddings for batch: {e}")

        return embeddings

    def get_dimension(self) -> int:
        """
        获取嵌入向量维度

        Returns:
            向量维度
        """
        return 1024  # text-embedding-v4 输出1024维


# 单例实例
_embedding_instance: Optional[AliyunEmbedding] = None


def get_aliyun_embedding() -> AliyunEmbedding:
    """获取或创建阿里云嵌入模型客户端单例"""
    global _embedding_instance
    if _embedding_instance is None:
        _embedding_instance = AliyunEmbedding()
    return _embedding_instance
