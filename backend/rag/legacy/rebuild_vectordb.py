"""
重建向量数据库脚本
解决 ChromaDB 版本不兼容问题
"""
import os
import shutil
from pathlib import Path

def rebuild_vector_database():
    """重建向量数据库"""

    print("=" * 60)
    print("开始重建向量数据库...")
    print("=" * 60)

    # 获取路径
    rag_data_dir = Path(__file__).parent / "rag" / "data"
    chroma_dir = rag_data_dir / "chroma"
    chroma_backup_dir = rag_data_dir / "chroma_backup_old"

    print(f"\n当前 RAG 数据目录: {rag_data_dir}")
    print(f"ChromaDB 目录: {chroma_dir}")

    # 检查 chroma 目录是否存在
    if not chroma_dir.exists():
        print(f"\n✅ ChromaDB 目录不存在，将创建新的数据库")
    else:
        print(f"\n⚠️  检测到旧的 ChromaDB 数据库")
        print(f"   问题: 数据库 schema 版本不兼容")
        print(f"   解决方案: 删除旧数据库并重建\n")

        # 备份旧数据库
        if chroma_backup_dir.exists():
            shutil.rmtree(chroma_backup_dir)

        print(f"📦 备份旧数据库到: {chroma_backup_dir}")
        shutil.copytree(chroma_dir, chroma_backup_dir)

        print(f"🗑️  删除旧的 ChromaDB 数据库...")
        shutil.rmtree(chroma_dir)

    print(f"\n✅ 清理完成！\n")

    # 导入 RAG 模块
    print("=" * 60)
    print("开始初始化向量数据库...")
    print("=" * 60)

    try:
        from rag.document_processor import get_document_processor
        from rag.legacy.vector_store import get_vector_store
        from common.constant import RAG_KNOWLEDGE_BASE_PATH

        # 获取知识库路径
        knowledge_base_path = os.getenv(RAG_KNOWLEDGE_BASE_PATH, str(rag_data_dir))
        print(f"\n📚 知识库路径: {knowledge_base_path}")

        # 检查知识库文件
        knowledge_path = Path(knowledge_base_path)
        doc_files = list(knowledge_path.glob("*.pdf")) + list(knowledge_path.glob("*.doc")) + list(knowledge_path.glob("*.docx"))

        if not doc_files:
            print(f"\n⚠️  警告: 在 {knowledge_base_path} 中未找到知识库文档")
            print(f"   支持的格式: .pdf, .doc, .docx")
            print(f"\n请将知识库文档放到该目录后重新运行此脚本")
            return False

        print(f"\n📄 找到 {len(doc_files)} 个文档:")
        for doc in doc_files:
            print(f"   - {doc.name}")

        # 初始化向量数据库
        print(f"\n🔧 初始化向量数据库...")
        vector_store = get_vector_store()

        # 检查是否为空
        if vector_store.is_empty():
            print(f"\n📖 向量数据库为空，开始处理文档...")

            # 处理文档
            print(f"\n📄 加载并处理知识库文档...")
            processor = get_document_processor(knowledge_base_path)
            chunks = processor.load_documents()

            if not chunks:
                print(f"\n⚠️  警告: 未能从文档中提取任何文本块")
                return False

            print(f"\n✅ 成功提取 {len(chunks)} 个文本块")

            # 添加到向量数据库
            print(f"\n💾 将文本块添加到向量数据库...")
            print(f"   (这可能需要几分钟，请耐心等待...)")
            vector_store.add_documents(chunks)

            # 显示统计信息
            info = vector_store.get_collection_info()
            print(f"\n✅ 向量数据库构建完成！")
            print(f"\n📊 数据库统计:")
            print(f"   - 集合名称: {info['name']}")
            print(f"   - 文档数量: {info['count']}")
            print(f"   - 向量维度: {info['dimension']}")
            print(f"   - 存储路径: {info['persist_directory']}")
        else:
            print(f"\n✅ 向量数据库已存在，包含 {vector_store.collection.count()} 个文档")

            # 显示统计信息
            info = vector_store.get_collection_info()
            print(f"\n📊 数据库统计:")
            print(f"   - 集合名称: {info['name']}")
            print(f"   - 文档数量: {info['count']}")
            print(f"   - 向量维度: {info['dimension']}")

        print(f"\n✅ 向量数据库重建成功！")
        print(f"\n💡 提示:")
        print(f"   1. 如果在魔搭创空间，请重启应用")
        print(f"   2. 本地开发请重启后端服务")
        print(f"   3. 备份的旧数据库在: {chroma_backup_dir}")

        return True

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

        print(f"\n💡 故障排除建议:")
        print(f"   1. 检查是否安装了所有依赖: pip install -r requirements.txt")
        print(f"   2. 检查 API Key 是否正确配置")
        print(f"   3. 检查知识库文档是否存在且格式正确")
        print(f"   4. 查看上方详细错误信息")

        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(" " * 15 + "向量数据库重建工具")
    print("=" * 60)

    success = rebuild_vector_database()

    print("\n" + "=" * 60)
    if success:
        print("✅ 重建完成！")
    else:
        print("❌ 重建失败，请查看上方错误信息")
    print("=" * 60 + "\n")
