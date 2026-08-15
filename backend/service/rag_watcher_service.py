"""
RAG 知识库自动监听服务

定期扫描知识库目录，检测到 PDF/DOC/DOCX 文件新增、修改或删除后，
自动重建向量索引，无需手动调用接口或重启容器。
"""
import os
import threading
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

from common.constant import RAG_KNOWLEDGE_BASE_PATH
from rag.retriever_faiss import get_rag_retriever


class RAGWatcher:
    """后台线程，自动监听知识库文件变化并触发索引重建。"""

    SUPPORTED_PATTERNS = ("*.pdf", "*.doc", "*.docx")

    def __init__(self, interval_seconds: int = 30):
        self.interval_seconds = interval_seconds
        self._last_fingerprints: Dict[str, Tuple[float, int]] = {}
        self._scan_lock = threading.Lock()
        self._rebuild_lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _list_knowledge_files(self) -> Dict[str, Tuple[float, int]]:
        """获取知识库目录下所有支持文档的指纹（路径 -> (修改时间, 大小)）。"""
        base_path = Path(RAG_KNOWLEDGE_BASE_PATH)
        if not base_path.exists() or not base_path.is_dir():
            return {}

        fingerprints: Dict[str, Tuple[float, int]] = {}
        for pattern in self.SUPPORTED_PATTERNS:
            for file_path in base_path.glob(pattern):
                try:
                    stat = file_path.stat()
                    fingerprints[str(file_path)] = (stat.st_mtime, stat.st_size)
                except OSError:
                    continue
        return fingerprints

    def _run_rebuild(self) -> None:
        """执行一次向量索引重建。失败会打印日志，下次扫描会自动重试。"""
        if not self._rebuild_lock.acquire(blocking=False):
            print("[RAG Watcher] 已有重建任务在进行中，跳过本次")
            return

        try:
            print("[RAG Watcher] 检测到知识库变化，开始热更新...")
            retriever = get_rag_retriever()
            result = retriever.rebuild_knowledge_base()
            status = result.get("status")
            if status == "error":
                print(f"[RAG Watcher] 热更新失败: {result.get('message')}")
            else:
                vector_count = result.get("info", {}).get("count", 0)
                print(f"[RAG Watcher] 热更新成功，当前向量数: {vector_count}")
        except Exception as e:
            print(f"[RAG Watcher] 热更新异常: {e}")
        finally:
            self._rebuild_lock.release()

    def _scan_once(self) -> None:
        """扫描一次文件变化，如有变化则触发重建。"""
        current = self._list_knowledge_files()

        with self._scan_lock:
            if current == self._last_fingerprints:
                return
            self._last_fingerprints = current

        # 文件发生变化，且当前有文档时才重建；全部删除则清空索引
        if current:
            self._run_rebuild()
        else:
            # 知识库被清空：清空索引并更新指纹
            try:
                retriever = get_rag_retriever()
                if not retriever.vector_store.is_empty():
                    retriever.vector_store.clear_collection()
                    print("[RAG Watcher] 知识库已清空，向量索引已清空")
            except Exception as e:
                print(f"[RAG Watcher] 清空索引失败: {e}")

    def _run(self) -> None:
        while self._running:
            try:
                self._scan_once()
            except Exception as e:
                print(f"[RAG Watcher] 扫描异常: {e}")
            time.sleep(self.interval_seconds)

    def start(self) -> None:
        """启动监听线程。首次启动时若向量为空且有文档，会自动初始化。"""
        if self._running:
            return

        self._running = True
        self._last_fingerprints = self._list_knowledge_files()

        # 启动时：如果向量库为空但知识库有文档，先执行一次初始化
        if self._last_fingerprints:
            try:
                retriever = get_rag_retriever()
                if retriever.vector_store.is_empty():
                    print("[RAG Watcher] 启动时向量库为空，执行首次初始化...")
                    threading.Thread(target=self._run_rebuild, daemon=True).start()
            except Exception as e:
                print(f"[RAG Watcher] 启动初始化检查失败: {e}")

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print(f"[RAG Watcher] 已启动，扫描间隔 {self.interval_seconds}s，知识库: {RAG_KNOWLEDGE_BASE_PATH}")

    def stop(self) -> None:
        """停止监听线程。"""
        self._running = False


# 全局单例
_watcher = RAGWatcher(interval_seconds=int(os.getenv("RAG_WATCH_INTERVAL", "30")))


def start_rag_watcher() -> None:
    """外部调用入口。"""
    _watcher.start()
