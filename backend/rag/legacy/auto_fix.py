"""
ChromaDB 数据库自动修复脚本
在创空间终端运行此脚本来彻底重建向量数据库
"""
import os
import shutil
from pathlib import Path


def fix_chromadb():
    """修复 ChromaDB 数据库"""

    print("=" * 70)
    print(" " * 20 + "ChromaDB 数据库修复工具")
    print("=" * 70)

    # 获取路径
    backend_dir = Path(__file__).parent
    chroma_dir = backend_dir / "rag" / "data" / "chroma"
    chroma_backup = backend_dir / "rag" / "data" / "chroma_backup_fix"

    print(f"\n📁 当前工作目录: {backend_dir}")
    print(f"🗄️  ChromaDB 目录: {chroma_dir}")

    # 检查是否存在
    if not chroma_dir.exists():
        print(f"\n✅ ChromaDB 目录不存在，无需修复")
        return False

    print(f"\n⚠️  检测到 ChromaDB 数据库")
    print(f"   问题: schema 不兼容 (no such column: collections.topic)")
    print(f"   解决方案: 删除并重建\n")

    # 备份
    if chroma_backup.exists():
        shutil.rmtree(chroma_backup)

    print(f"📦 备份旧数据库...")
    shutil.copytree(chroma_dir, chroma_backup)
    print(f"   备份位置: {chroma_backup}")

    # 删除旧数据库
    print(f"\n🗑️  删除旧的 ChromaDB 数据库...")
    shutil.rmtree(chroma_dir)
    print(f"   已删除: {chroma_dir}")

    # 检查知识库文件
    data_dir = backend_dir / "rag" / "data"
    doc_files = []
    for ext in ['*.pdf', '*.doc', '*.docx']:
        doc_files.extend(data_dir.glob(ext))

    if not doc_files:
        print(f"\n⚠️  警告: 未找到知识库文档")
        print(f"   请将 .pdf, .doc, .docx 文件放到: {data_dir}")
        print(f"\n💡 数据库已删除，但无法初始化（缺少文档）")
        return False

    print(f"\n📚 找到 {len(doc_files)} 个知识库文档:")
    for doc in doc_files:
        print(f"   - {doc.name}")

    print(f"\n✅ 修复完成！")
    print(f"\n💡 下一步:")
    print(f"   1. 重启应用，首次查询时会自动初始化向量数据库")
    print(f"   2. 初始化可能需要几分钟，请耐心等待")
    print(f"   3. 确保 DASHSCOPE_API_KEY 环境变量已配置")

    print(f"\n📊 备份信息:")
    print(f"   如果需要恢复，备份位置: {chroma_backup}")

    print("\n" + "=" * 70 + "\n")
    return True


if __name__ == "__main__":
    fix_chromadb()
