"""
RAG Retriever - Combine knowledge base search with user profile for context-aware retrieval
支持 FAISS 和 ChromaDB 两种向量数据库
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class RetrievalResult:
    """Result from RAG retrieval"""
    content: str
    source: str
    metadata: Dict[str, Any]
    relevance_score: float


class RAGRetriever:
    """Retrieval-Augmented Generation retriever with context awareness"""

    def __init__(self, vector_store, document_processor=None):
        """
        Initialize RAG retriever

        Args:
            vector_store: VectorStore instance for knowledge base search
            document_processor: DocumentProcessor instance (optional)
        """
        self.vector_store = vector_store
        self.document_processor = document_processor

    def retrieve(
        self,
        query: str,
        user_profile: Optional[Dict[str, Any]] = None,
        health_record: Optional[Dict[str, Any]] = None,
        health_test: Optional[Dict[str, Any]] = None,
        n_results: int = 5
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant context with user profile awareness

        Args:
            query: User query
            user_profile: Basic user information
            health_record: User health record data
            health_test: User health test results
            n_results: Number of results to retrieve

        Returns:
            List of retrieval results
        """
        # Build context-aware query
        enhanced_query = self._build_enhanced_query(
            query, user_profile, health_record, health_test
        )

        # Search vector store
        search_results = self.vector_store.search(enhanced_query, n_results=n_results)

        # Convert to RetrievalResult objects
        results = []
        for result in search_results:
            # FAISS 使用 score（相似度），范围 [0, 1]
            # ChromaDB 使用 distance（距离），范围 [0, 2]
            if 'score' in result:
                # FAISS: 直接使用相似度分数
                relevance_score = result['score']
            else:
                # ChromaDB: 需要转换距离为相似度
                distance = result.get('distance', 0)
                relevance_score = max(0.0, 1.0 - (distance / 2))

            results.append(RetrievalResult(
                content=result['text'],
                source=result['metadata'].get('source', '知识库'),
                metadata=result['metadata'],
                relevance_score=relevance_score
            ))

        return results

    def _build_enhanced_query(
        self,
        query: str,
        user_profile: Optional[Dict[str, Any]] = None,
        health_record: Optional[Dict[str, Any]] = None,
        health_test: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build enhanced query with context"""
        context_parts = []

        # Add user profile context
        if user_profile:
            basic_info = user_profile.get('basicInfo', {})
            if basic_info.get('age'):
                context_parts.append(f"用户年龄: {basic_info['age']}岁")
            if basic_info.get('gender'):
                context_parts.append(f"性别: {basic_info['gender']}")

        # Add health conditions context
        if health_record:
            chronic_disease = health_record.get('chronicDisease', {})
            diseases = chronic_disease.get('diseases', [])
            if diseases and 'none' not in diseases:
                # Translate disease codes to Chinese
                disease_names = self._translate_diseases(diseases)
                context_parts.append(f"健康状况: {', '.join(disease_names)}")

        # Build enhanced query
        if context_parts:
            context_str = ' | '.join(context_parts)
            return f"{query} (context: {context_str})"

        return query

    def _translate_diseases(self, diseases: List[str]) -> List[str]:
        """Translate disease codes to Chinese names"""
        disease_map = {
            'hypertension': '高血压',
            'diabetes': '糖尿病',
            'dyslipidemia': '血脂异常',
            'coronary_heart_disease': '冠心病',
            'angina': '心绞痛',
            'myocardial_infarction': '心肌梗死',
            'stroke': '脑卒中',
            'copd': '慢阻肺',
            'gout': '痛风',
            'chronic_kidney_disease': '慢性肾病',
            'hypothyroidism': '甲减',
            'hyperthyroidism': '甲亢',
            'osteoporosis': '骨质疏松',
            'parkinsons': '帕金森',
            'alzheimers': '阿尔茨海默',
            'tumor_history': '肿瘤病史',
        }
        return [disease_map.get(d, d) for d in diseases if d != 'none']

    def format_context_for_llm(self, results: List[RetrievalResult]) -> str:
        """
        Format retrieval results as context for LLM

        Args:
            results: List of retrieval results

        Returns:
            Formatted context string
        """
        if not results:
            return "无相关知识库信息"

        context_parts = []
        for i, result in enumerate(results, 1):
            source = result.metadata.get('filename', result.source)
            context_parts.append(
                f"[来源 {i}: {source}]\n{result.content}\n"
            )

        return "\n".join(context_parts)

    def _load_and_index_documents(self) -> Dict[str, Any]:
        """加载知识库文档并写入向量索引（内部复用）。"""
        if self.document_processor is None:
            from rag.document_processor import get_document_processor
            self.document_processor = get_document_processor()

        chunks = self.document_processor.load_documents()
        if not chunks:
            return {
                'status': 'error',
                'message': '未能从知识库提取任何文档内容'
            }

        self.vector_store.add_documents(chunks)
        return {
            'status': 'initialized',
            'chunks_processed': len(chunks),
            'info': self.vector_store.get_collection_info()
        }

    def initialize_knowledge_base(self) -> Dict[str, Any]:
        """
        Initialize knowledge base from documents

        支持通过环境变量 SKIP_RAG_INIT 控制是否跳过初始化，
        这在部署环境中可以避免重新生成向量库导致的内存问题。

        Returns:
            Status information
        """
        import os

        # 检查是否跳过初始化（用于生产环境）
        skip_init = os.getenv('SKIP_RAG_INIT', 'false').lower() == 'true'

        if skip_init:
            if not self.vector_store.is_empty():
                return {
                    'status': 'skipped',
                    'message': '跳过初始化，使用已有向量库',
                    'info': self.vector_store.get_collection_info()
                }
            else:
                return {
                    'status': 'error',
                    'message': '向量库为空且 SKIP_RAG_INIT=true，无法继续'
                }

        # Check if vector store is already populated
        if not self.vector_store.is_empty():
            return {
                'status': 'already_initialized',
                'info': self.vector_store.get_collection_info()
            }

        # Load and process documents
        return self._load_and_index_documents()

    def rebuild_knowledge_base(self) -> Dict[str, Any]:
        """
        重新加载知识库文档并重建向量索引（热更新，无需重启容器）。

        Returns:
            Status information
        """
        print("🔄 收到热更新请求，开始重建知识库...")

        if self.document_processor is None:
            from rag.document_processor import get_document_processor
            self.document_processor = get_document_processor()

        # 清空现有索引
        self.vector_store.clear_collection()
        print("✅ 已清空旧向量索引")

        result = self._load_and_index_documents()
        if result.get('status') == 'initialized':
            result['status'] = 'rebuilt'
            result['message'] = '知识库热更新成功'
        print(f"🔄 热更新完成: {result}")
        return result


class NoOpRetriever(RAGRetriever):
    """当向量检索不可用时的降级检索器（不依赖外部 embedding API）"""

    class _DummyVectorStore:
        """兼容 RAGWatcher 的占位向量库。"""
        def is_empty(self) -> bool:
            return True
        def clear_collection(self) -> None:
            pass

    def __init__(self):
        # 不需要真实的 vector_store/document_processor
        self.vector_store = self._DummyVectorStore()

    def retrieve(
        self,
        query: str,
        user_profile: Optional[Dict[str, Any]] = None,
        health_record: Optional[Dict[str, Any]] = None,
        health_test: Optional[Dict[str, Any]] = None,
        n_results: int = 5
    ) -> List[RetrievalResult]:
        return []

    def format_context_for_llm(self, results: List[RetrievalResult]) -> str:
        return "无相关知识库信息"

    def initialize_knowledge_base(self) -> Dict[str, Any]:
        return {
            'status': 'disabled',
            'message': '向量检索未启用（本地嵌入模型加载失败或向量库初始化失败）'
        }

    def rebuild_knowledge_base(self) -> Dict[str, Any]:
        return {
            'status': 'disabled',
            'message': '向量检索未启用，无法重建知识库'
        }


# 全局单例，避免重复初始化失败
_rag_retriever_instance: Optional[RAGRetriever] = None
_rag_retriever_initialized: bool = False


def get_rag_retriever() -> RAGRetriever:
    """Get or create RAG retriever instance

    当本地嵌入模型加载失败或向量库初始化失败时，返回 NoOpRetriever，
    让聊天功能仍能基于大模型继续工作。
    """
    global _rag_retriever_instance, _rag_retriever_initialized

    if _rag_retriever_initialized:
        return _rag_retriever_instance

    try:
        from rag.vector_store_faiss import get_vector_store
        from rag.document_processor import get_document_processor

        vector_store = get_vector_store()
        document_processor = get_document_processor()

        _rag_retriever_instance = RAGRetriever(vector_store, document_processor)
        _rag_retriever_initialized = True
        return _rag_retriever_instance
    except Exception as e:
        print(f"⚠️  RAG 检索器初始化失败，将降级为无检索模式: {e}")
        _rag_retriever_instance = NoOpRetriever()
        _rag_retriever_initialized = True
        return _rag_retriever_instance
