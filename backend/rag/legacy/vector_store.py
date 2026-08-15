"""
Vector Store - ChromaDB wrapper for storing and retrieving document embeddings
使用阿里云百炼 text-embedding-v4 嵌入模型
"""
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None


class VectorStore:
    """向量数据库 - 使用阿里云百炼嵌入模型"""

    def __init__(self, persist_directory: str, collection_name: str = "health_knowledge"):
        """
        初始化向量数据库

        Args:
            persist_directory: 向量数据库持久化目录
            collection_name: 集合名称
        """
        if chromadb is None:
            raise ImportError("chromadb 未安装，请运行: pip install chromadb")

        # 版本检查和日志
        print(f"📦 ChromaDB version: {chromadb.__version__}")

        # 版本兼容性检查
        try:
            version_parts = chromadb.__version__.split('.')
            major, minor = int(version_parts[0]), int(version_parts[1])
            if major < 0 or (major == 0 and minor < 5):
                print("⚠️  Warning: ChromaDB version < 0.5.0 is not supported")
                print("   Please upgrade: pip install --upgrade chromadb")
        except (ValueError, IndexError) as e:
            print(f"⚠️  Warning: Could not parse ChromaDB version: {e}")

        from common.aliyun_embedding import get_aliyun_embedding

        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name

        # 初始化 ChromaDB 客户端（禁用遥测）
        import os
        os.environ['ANONYMIZED_TELEMETRY'] = 'false'

        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # 初始化阿里云嵌入模型
        print("初始化阿里云百炼嵌入模型: text-embedding-v4")
        self.embedding_model = get_aliyun_embedding()
        self.embedding_dimension = self.embedding_model.get_dimension()
        print(f"嵌入向量维度: {self.embedding_dimension}")

        # 获取或创建集合（优化HNSW参数以减少内存占用）
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "hnsw:space": "cosine",
                "hnsw:M": "12",              # 从默认16降到12，减少30-40%内存
                "hnsw:construction_ef": "150",  # 从默认200降到150
                "hnsw:search_ef": "40"         # 从默认50降到40
            }
        )

    def add_documents(self, chunks: List[Dict[str, Any]]):
        """
        添加文档块到向量数据库

        Args:
            chunks: 包含 'text' 和 'metadata' 的文档块列表
        """
        if not chunks:
            print("没有文档块可添加")
            return

        texts = [chunk['text'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]

        # 生成嵌入向量
        print(f"正在为 {len(texts)} 个文档块生成嵌入向量...")
        embeddings = self.embedding_model.embed_documents(texts)

        # 生成稳定的ID（使用 hashlib 而不是 hash()，因为 hash() 在每次运行时结果不同）
        import hashlib
        ids = [
            f"doc_{i}_{hashlib.md5(text.encode()).hexdigest()[:8]}"
            for i, text in enumerate(texts)
        ]

        # 添加到集合
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

        print(f"已添加 {len(ids)} 个文档到向量数据库")

    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相关文档

        Args:
            query: 搜索查询文本
            n_results: 返回结果数量
            filter_metadata: 可选的元数据过滤条件

        Returns:
            搜索结果列表，包含文本和元数据
        """
        # 生成查询嵌入向量
        query_embedding = self.embedding_model.embed_query(query)

        # 搜索
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata
        )

        # 格式化结果
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    'text': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else None
                })

        return formatted_results

    def clear_collection(self):
        """清空集合中的所有文档"""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={
                "hnsw:space": "cosine",
                "hnsw:M": "12",
                "hnsw:construction_ef": "150",
                "hnsw:search_ef": "40"
            }
        )
        print(f"已清空集合: {self.collection_name}")

    def get_collection_info(self) -> Dict[str, Any]:
        """获取集合信息"""
        count = self.collection.count()
        return {
            'name': self.collection_name,
            'count': count,
            'dimension': self.embedding_dimension,
            'persist_directory': str(self.persist_directory)
        }

    def is_empty(self) -> bool:
        """检查集合是否为空"""
        return self.collection.count() == 0


# 单例模式：全局向量数据库实例
_vector_store_instance: Optional[VectorStore] = None


def get_vector_store(
    persist_directory: str = None,
    collection_name: str = "health_knowledge"
) -> VectorStore:
    """
    获取或创建向量数据库单例

    使用单例模式确保向量数据库只加载一次到内存，避免重复加载导致的内存浪费。
    这对于资源受限的环境（如魔搭创空间）非常重要。

    Args:
        persist_directory: 向量数据库持久化目录
        collection_name: 集合名称

    Returns:
        VectorStore 单例实例
    """
    global _vector_store_instance

    if _vector_store_instance is None:
        from common.constant import RAG_VECTOR_DB_PATH

        if persist_directory is None:
            persist_directory = RAG_VECTOR_DB_PATH or './rag/data/chroma'

        print("🔄 初始化向量数据库单例...")
        _vector_store_instance = VectorStore(persist_directory, collection_name)
        print(f"✅ 向量数据库单例已创建: {_vector_store_instance.get_collection_info()['count']} 个向量")

    return _vector_store_instance
