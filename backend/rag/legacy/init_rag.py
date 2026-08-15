"""
RAG 系统初始化和健康检查
在应用启动时自动检测并修复向量数据库问题
"""
import os
import shutil
from pathlib import Path


def check_and_fix_vector_db():
    """检查并修复向量数据库"""

    rag_data_dir = Path(__file__).parent / "data"
    chroma_dir = rag_data_dir / "chroma"
    chroma_backup_dir = rag_data_dir / "chroma_backup_auto"

    # 检查是否需要重建
    needs_rebuild = False

    if chroma_dir.exists():
        # 检查是否有损坏的数据库文件
        sqlite_file = chroma_dir / "chroma.sqlite3"

        if sqlite_file.exists():
            try:
                # 尝试导入并测试
                import chromadb
                from chromadb.config import Settings

                test_client = chromadb.PersistentClient(
                    path=str(chroma_dir),
                    settings=Settings(anonymized_telemetry=False, allow_reset=True)
                )

                # 尝试获取集合，触发错误检测
                try:
                    test_client.get_or_create_collection("health_knowledge")
                except Exception as e:
                    if "no such column" in str(e).lower() or "database is locked" in str(e).lower():
                        print(f"⚠️  检测到数据库不兼容: {e}")
                        needs_rebuild = True

            except Exception as e:
                print(f"⚠️  ChromaDB 检查失败: {e}")
                needs_rebuild = True

    if needs_rebuild:
        print(f"\n🔧 检测到向量数据库问题，准备修复...")

        # 备份
        if chroma_dir.exists():
            if chroma_backup_dir.exists():
                shutil.rmtree(chroma_backup_dir)
            shutil.copytree(chroma_dir, chroma_backup_dir)
            print(f"📦 已备份旧数据库到: {chroma_backup_dir}")

        # 删除旧数据库
        if chroma_dir.exists():
            shutil.rmtree(chroma_dir)
            print(f"🗑️  已删除旧的数据库")

        # 检查是否有知识库文档
        knowledge_base_files = []
        for ext in ['*.pdf', '*.doc', '*.docx']:
            knowledge_base_files.extend(rag_data_dir.glob(ext))

        if not knowledge_base_files:
            print(f"\n⚠️  警告: 未找到知识库文档")
            print(f"   请将 .pdf, .doc, .docx 文档放到: {rag_data_dir}")
            return False

        print(f"✅ 数据库清理完成，将在首次访问时自动初始化")
        return True

    return False


def initialize_if_needed():
    """如果需要，初始化向量数据库"""

    rag_data_dir = Path(__file__).parent / "data"
    chroma_dir = rag_data_dir / "chroma"

    # 如果数据库不存在或被清理，需要初始化
    if not chroma_dir.exists() or not list(chroma_dir.iterdir()):
        print(f"\n📚 向量数据库不存在，开始初始化...")

        try:
            from rag.document_processor import get_document_processor
            from rag.legacy.vector_store import get_vector_store
            from common.constant import RAG_KNOWLEDGE_BASE_PATH
            import os

            # 获取知识库路径
            knowledge_base_path = os.getenv(RAG_KNOWLEDGE_BASE_PATH, str(rag_data_dir))

            # 初始化向量数据库
            vector_store = get_vector_store()

            # 如果为空，添加文档
            if vector_store.is_empty():
                print(f"📖 处理知识库文档...")

                processor = get_document_processor(knowledge_base_path)
                chunks = processor.load_documents()

                if chunks:
                    print(f"💾 添加 {len(chunks)} 个文档块到向量数据库...")
                    vector_store.add_documents(chunks)

                    info = vector_store.get_collection_info()
                    print(f"✅ 初始化完成！共 {info['count']} 个文档")
                else:
                    print(f"⚠️  警告: 未能提取任何文档内容")

        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            import traceback
            traceback.print_exc()


def auto_fix_on_error():
    """当查询出错时自动修复"""
    print(f"\n🔧 向量数据库出错，尝试自动修复...")

    # 直接删除重建
    rag_data_dir = Path(__file__).parent / "data"
    chroma_dir = rag_data_dir / "chroma"

    if chroma_dir.exists():
        shutil.rmtree(chroma_dir)
        print(f"🗑️  已删除损坏的数据库")

    print(f"✅ 修复完成，将在下次查询时自动重建")
    print(f"💡 请重启应用或重试查询")


if __name__ == "__main__":
    print("=" * 60)
    print("RAG 系统健康检查")
    print("=" * 60)

    if check_and_fix_vector_db():
        print("\n✅ 检测到问题并已修复")
        initialize_if_needed()
    else:
        print("\n✅ 数据库状态正常")
        initialize_if_needed()
