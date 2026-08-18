"""
Vector Store - FAISS wrapper for storing and retrieving document embeddings
使用本地 sentence-transformers 嵌入模型
"""
import os
import pickle
from typing import List, Dict, Any
from pathlib import Path

try:
    import faiss
except ImportError:
    faiss = None


class VectorStore:
    """向量数据库 - 使用 FAISS + 本地 sentence-transformers 嵌入模型"""

    def __init__(self, persist_directory: str, index_name: str = "health_knowledge"):
        """
        初始化向量数据库

        为加速启动，嵌入模型延迟加载：只有真正需要生成/查询向量时
        才会触发 sentence-transformers 模型下载与加载。

        Args:
            persist_directory: 向量数据库持久化目录
            index_name: 索引名称
        """
        if faiss is None:
            raise ImportError("faiss 未安装，请运行: pip install faiss-cpu")

        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.index_name = index_name
        self.index_path = self.persist_directory / f"{index_name}.faiss"
        self.metadata_path = self.persist_directory / f"{index_name}_metadata.pkl"

        # 延迟加载 embedding 模型，避免启动时阻塞 HuggingFace 下载
        self._embedding_model = None
        self.embedding_dimension = None

        # 加载或创建索引（优先从已有索引推断维度，避免启动时加载模型）
        self._load_or_create_index()

    @property
    def embedding_model(self):
        """懒加载本地嵌入模型。"""
        if self._embedding_model is None:
            from common.local_embedding import get_local_embedding
            self._embedding_model = get_local_embedding()
            if self.embedding_dimension is None:
                self.embedding_dimension = self._embedding_model.get_dimension()
        return self._embedding_model

    def _load_or_create_index(self):
        """加载或创建FAISS索引"""
        if self.index_path.exists() and self.metadata_path.exists():
            # 加载已有索引
            self.index = faiss.read_index(str(self.index_path))
            with open(self.metadata_path, 'rb') as f:
                self.metadatas = pickle.load(f)
            self.embedding_dimension = self.index.d
            print(f"✅ 已加载向量索引: {self.index.ntotal} 个向量，维度: {self.embedding_dimension}")
        else:
            # 创建新索引：此时还不需要知道维度，首次 add_documents 时创建
            self.index = None
            self.metadatas = []
            print("✅ 索引尚未创建，将在首次添加文档时初始化")

    def add_documents(self, chunks: List[Dict[str, Any]]):
        """
        添加文档块到向量数据库

        Args:
            chunks: 包含 'text' 和 'metadata' 的文档块列表
        """
        if not chunks:
            print("没有文档块可添加")
            return

        # 首次添加时创建索引（此时才会触发模型加载）
        if self.index is None:
            self.embedding_dimension = self.embedding_model.get_dimension()
            self.index = faiss.IndexFlatIP(self.embedding_dimension)
            print(f"✅ 创建新索引，维度: {self.embedding_dimension}")

        texts = [chunk['text'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]

        # 生成嵌入向量
        print(f"正在为 {len(texts)} 个文档块生成嵌入向量...")
        embeddings = self.embedding_model.embed_documents(texts)

        # 归一化向量（用于余弦相似度）
        import numpy as np
        embeddings_array = np.array(embeddings, dtype='float32')
        faiss.normalize_L2(embeddings_array)

        # 添加到索引
        start_idx = self.index.ntotal
        self.index.add(embeddings_array)

        # 保存元数据
        for i, metadata in enumerate(metadatas):
            metadata['idx'] = start_idx + i
            self.metadatas.append(metadata)

        # 保存到磁盘
        self._save()

        print(f"✅ 已添加 {len(texts)} 个文档，总数: {self.index.ntotal}")

    def _save(self):
        """保存索引到磁盘"""
        if self.index is None:
            return
        faiss.write_index(self.index, str(self.index_path))
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.metadatas, f)

    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Dict[str, Any] = None
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
        if self.index is None or self.index.ntotal == 0:
            return []

        # 生成查询嵌入向量
        import numpy as np
        query_embedding = self.embedding_model.embed_query(query)
        query_array = np.array([query_embedding], dtype='float32')
        faiss.normalize_L2(query_array)

        # 搜索
        distances, indices = self.index.search(query_array, n_results)

        # 格式化结果
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.metadatas):
                continue

            metadata = self.metadatas[idx]

            # 应用元数据过滤
            if filter_metadata:
                match = True
                for key, value in filter_metadata.items():
                    if metadata.get(key) != value:
                        match = False
                        break
                if not match:
                    continue

            results.append({
                'text': metadata.get('text', ''),
                'metadata': metadata,
                'distance': float(1 - distance),  # 转换为距离（余弦距离 = 1 - 余弦相似度）
                'score': float(distance)  # 相似度分数
            })

        return results

    def clear_collection(self):
        """清空索引中的所有文档"""
        # 重新创建空索引
        if self.embedding_dimension is None:
            self.embedding_dimension = self.embedding_model.get_dimension()
        self.index = faiss.IndexFlatIP(self.embedding_dimension)
        self.metadatas = []
        self._save()
        print(f"✅ 已清空索引: {self.index_name}")

    def get_collection_info(self) -> Dict[str, Any]:
        """获取索引信息"""
        return {
            'name': self.index_name,
            'count': int(self.index.ntotal) if self.index is not None else 0,
            'dimension': self.embedding_dimension,
            'persist_directory': str(self.persist_directory)
        }

    def is_empty(self) -> bool:
        """检查索引是否为空"""
        return self.index is None or self.index.ntotal == 0


# 单例模式：全局向量数据库实例
_vector_store_instance = None


def get_vector_store(
    persist_directory: str = None,
    index_name: str = "health_knowledge",
    auto_init: bool = True
) -> VectorStore:
    """
    获取或创建向量数据库单例

    使用单例模式确保向量数据库只加载一次到内存，避免重复加载导致的内存浪费。
    这对于资源受限的环境（如魔搭创空间）非常重要。

    Args:
        persist_directory: 向量数据库持久化目录
        index_name: 索引名称
        auto_init: 是否自动初始化空索引（默认True）

    Returns:
        VectorStore 单例实例
    """
    global _vector_store_instance

    if _vector_store_instance is None:
        from common.constant import RAG_VECTOR_DB_PATH, RAG_KNOWLEDGE_BASE_PATH

        if persist_directory is None:
            persist_directory = os.getenv("RAG_VECTOR_DB_PATH", RAG_VECTOR_DB_PATH)

        print("🔄 初始化向量数据库单例...")
        _vector_store_instance = VectorStore(persist_directory, index_name)
        print(f"✅ 向量数据库单例已创建: {_vector_store_instance.get_collection_info()['count']} 个向量")

        # 如果索引为空且启用自动初始化，加载知识库文档
        if auto_init and _vector_store_instance.is_empty():
            skip_init = os.getenv('SKIP_RAG_INIT', 'false').lower() == 'true'
            if skip_init:
                print("⏭️  SKIP_RAG_INIT=true，跳过空索引初始化，RAG 将返回空结果")
            else:
                print("📚 检测到空索引，开始初始化知识库...")
                _initialize_knowledge_base()

    return _vector_store_instance


def _initialize_knowledge_base():
    """初始化知识库，加载文档到向量数据库"""
    global _vector_store_instance

    if _vector_store_instance is None:
        print("⚠️  向量数据库未初始化")
        return

    try:
        from common.constant import RAG_KNOWLEDGE_BASE_PATH
        from rag.document_processor import DocumentProcessor
        import os

        # 获取知识库路径
        knowledge_base_path = os.getenv("RAG_KNOWLEDGE_BASE_PATH", RAG_KNOWLEDGE_BASE_PATH)

        # 检查知识库文件
        knowledge_dir = Path(knowledge_base_path)
        if not knowledge_dir.exists():
            print(f"⚠️  知识库目录不存在: {knowledge_base_path}")
            return

        # 查找 PDF 和 DOC 文件
        import glob
        pdf_files = list(knowledge_dir.glob("*.pdf"))
        doc_files = list(knowledge_dir.glob("*.doc")) + list(knowledge_dir.glob("*.docx"))

        if not pdf_files and not doc_files:
            print(f"⚠️  未找到知识库文档（.pdf, .doc, .docx）")
            print(f"   请将文档放到: {knowledge_base_path}")
            return

        print(f"📖 找到 {len(pdf_files)} 个 PDF 文件，{len(doc_files)} 个 DOC 文件")

        # 处理文档
        processor = DocumentProcessor(str(knowledge_base_path))
        chunks = processor.load_documents()

        if not chunks:
            print("⚠️  未能提取任何文档内容")
            return

        print(f"💾 正在添加 {len(chunks)} 个文档块到向量数据库...")
        _vector_store_instance.add_documents(chunks)

        info = _vector_store_instance.get_collection_info()
        print(f"✅ 知识库初始化完成！共 {info['count']} 个向量")

    except Exception as e:
        print(f"❌ 初始化知识库失败: {e}")
        import traceback
        traceback.print_exc()
