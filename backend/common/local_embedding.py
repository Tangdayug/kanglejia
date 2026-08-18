"""本地 Sentence-Transformers 嵌入模型客户端

默认使用 BAAI/bge-small-en-v1.5：
- 针对英文优化（知识库约 80 % 英文），同时支持中文。
- 384 维向量，模型文件约 100 MB，CPU 可跑。
- 适合 4 核 / 8 GB 机器。
"""
import logging
import os
from typing import List, Optional

from common.constant import EMBEDDING_MODEL_NAME

logger = logging.getLogger(__name__)


class LocalEmbedding:
    """本地 sentence-transformers 嵌入模型封装。"""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or EMBEDDING_MODEL_NAME
        self._model = None

    def _load_model(self):
        """延迟加载模型，避免导入时触发下载。"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as e:
                raise ImportError(
                    "sentence-transformers 未安装，请运行: pip install sentence-transformers"
                ) from e

            logger.info(f"正在加载本地嵌入模型: {self.model_name}")
            # device="cpu" 明确使用 CPU，避免在无 GPU 环境尝试 cuda
            self._model = SentenceTransformer(self.model_name, device="cpu")
            logger.info(f"嵌入模型加载完成，维度: {self.get_dimension()}")
        return self._model

    def embed_query(self, text: str) -> List[float]:
        """生成单个查询文本的嵌入向量。"""
        return self.embed_documents([text])[0]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量生成文档块的嵌入向量。"""
        if not texts:
            return []

        model = self._load_model()
        # 空字符串传给 sentence-transformers 可能报警告，过滤掉
        embeddings = model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=False,
        )
        return embeddings.tolist()

    def get_dimension(self) -> int:
        """获取嵌入向量维度（延迟加载模型以读取）。"""
        model = self._load_model()
        return model.get_sentence_embedding_dimension()


# 单例实例，避免重复加载模型
_embedding_instance: Optional[LocalEmbedding] = None


def get_local_embedding(model_name: Optional[str] = None) -> LocalEmbedding:
    """获取或创建本地嵌入模型客户端单例。"""
    global _embedding_instance
    if _embedding_instance is None:
        _embedding_instance = LocalEmbedding(model_name=model_name)
    return _embedding_instance
