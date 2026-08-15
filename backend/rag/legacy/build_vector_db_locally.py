"""
本地生成向量数据库脚本
在本地运行此脚本，生成完整的ChromaDB向量数据库，然后上传到服务器

优点：
1. 本地性能更好，生成速度快
2. 不受服务器资源限制
3. 可以多次运行调试
"""
import os
import sys
import time
from datetime import timedelta
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.legacy.vector_store import VectorStore
from rag.document_processor import DocumentProcessor
from common.constant import RAG_KNOWLEDGE_BASE_PATH, RAG_VECTOR_DB_PATH


def build_vector_db():
    """本地构建向量数据库"""
    print("=" * 60)
    print("本地生成向量数据库")
    print("=" * 60)

    # 知识库路径（使用本地路径）
    knowledge_base_path = Path(__file__).parent.parent / "rag" / "data"
    print(f"\n📂 知识库路径: {knowledge_base_path}")
    print(f"📂 路径是否存在: {knowledge_base_path.exists()}")

    if not knowledge_base_path.exists():
        print(f"❌ 知识库路径不存在: {knowledge_base_path}")
        return False

    # 向量数据库保存路径（本地）
    vector_db_path = Path(__file__).parent.parent / "rag" / "data" / "chroma"
    print(f"\n💾 向量数据库保存路径: {vector_db_path}")

    # 检查并清理旧的向量数据库（确保干净重建）
    if vector_db_path.exists():
        chroma_sqlite = vector_db_path / "chroma.sqlite3"
        if chroma_sqlite.exists():
            size_mb = chroma_sqlite.stat().st_size / (1024 * 1024)
            print(f"\n⚠️  检测到旧的向量数据库 ({size_mb:.2f} MB)")

        # 方法1：尝试使用 ChromaDB 的 reset() 方法
        try:
            import chromadb
            from chromadb.config import Settings
            os.environ['ANONYMIZED_TELEMETRY'] = 'false'

            print(f"🔧 尝试重置向量数据库...")
            temp_client = chromadb.PersistentClient(
                path=str(vector_db_path),
                settings=Settings(anonymized_telemetry=False, allow_reset=True)
            )
            temp_client.reset()
            print(f"✅ 已通过 ChromaDB reset() 清空数据库")
        except Exception as reset_error:
            print(f"⚠️  reset() 失败: {reset_error}")

            # 方法2：强制删除旧数据库
            import shutil
            print(f"🗑️  尝试删除旧数据库目录...")
            try:
                shutil.rmtree(vector_db_path)
                print(f"✅ 已删除，准备重新生成")
            except Exception as e:
                print(f"❌ 删除失败: {e}")
                print(f"\n提示: 数据库文件可能被其他进程占用")
                print(f"解决方法:")
                print(f"  1. 关闭所有 Python 进程")
                print(f"  2. 手动删除目录: {vector_db_path}")
                print(f"  3. 重新运行此脚本")
                return False

    # 创建向量数据库（先初始化）
    print(f"\n🔧 初始化向量数据库...")
    vector_store = VectorStore(
        persist_directory=str(vector_db_path),
        collection_name="health_knowledge"
    )

    # 创建文档处理器
    print(f"\n📄 初始化文档处理器...")
    processor = DocumentProcessor(str(knowledge_base_path))
    print(f"⚙️  使用默认配置: chunk_size={processor.chunk_size}, overlap={processor.chunk_overlap}")

    # 分批加载和处理文档（避免内存不足）
    print(f"\n📚 开始加载文档（分批处理）...")

    batch_size = 10  # 每批处理10个文档块（阿里云API限制：每批最多10个）
    total_chunks = 0
    start_time = time.time()  # 记录开始时间
    batch_times = []  # 记录每批处理时间，用于计算平均速度

    # 手动遍历PDF文件并分批处理
    pdf_files = list(knowledge_base_path.glob("*.pdf"))
    print(f"找到 {len(pdf_files)} 个PDF文件")

    import gc

    for pdf_file in pdf_files:
        file_start_time = time.time()
        print(f"\n处理文件: {pdf_file.name}")

        # 提取文本
        text = processor.extract_text_from_pdf(str(pdf_file))
        if not text:
            print(f"  ⚠️  无法提取文本，跳过")
            continue

        print(f"  提取了 {len(text)} 个字符")

        # 分块
        metadata = {
            'source': pdf_file.name,
            'filename': pdf_file.name,
            'file_type': '.pdf'
        }

        # 使用流式分块处理（避免一次性创建所有块导致内存溢出）
        print(f"  开始流式分块和向量化（文本长度: {len(text)}）...")

        # 流式分块：边分块边添加到向量库
        chunk_index = 0
        batch_buffer = []
        text_length = len(text)
        start_pos = 0

        # 估算总块数（用于进度显示）
        estimated_file_chunks = max(1, (text_length // processor.chunk_size) * len(pdf_files))

        while start_pos < text_length:
            # 提取一个块
            end_pos = start_pos + processor.chunk_size

            # 尝试在句子边界断开
            if end_pos < text_length:
                for delimiter in ['。', '！', '？', '. ', '! ', '? ', '\n\n']:
                    last_pos = text.rfind(delimiter, start_pos, end_pos)
                    if last_pos != -1:
                        end_pos = last_pos + len(delimiter)
                        break

            chunk_text = text[start_pos:end_pos].strip()
            if chunk_text:
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk_index'] = chunk_index
                chunk_metadata['text_length'] = len(chunk_text)
                batch_buffer.append({
                    'text': chunk_text,
                    'metadata': chunk_metadata
                })

                # 当缓冲区满时，添加到向量库
                if len(batch_buffer) >= batch_size:
                    batch_start = time.time()

                    vector_store.add_documents(batch_buffer)
                    total_chunks += len(batch_buffer)

                    # 计算批次耗时
                    batch_elapsed = time.time() - batch_start
                    batch_times.append(batch_elapsed)

                    # 计算总体进度
                    total_elapsed = time.time() - start_time
                    avg_speed = total_chunks / total_elapsed if total_elapsed > 0 else 0

                    # 估算总块数
                    estimated_total = max(1400, total_chunks + (estimated_file_chunks - chunk_index) * len(pdf_files) // 2)

                    # 计算预计剩余时间
                    if avg_speed > 0:
                        remaining_chunks = estimated_total - total_chunks
                        eta_seconds = remaining_chunks / avg_speed
                        eta = str(timedelta(seconds=int(eta_seconds)))
                    else:
                        eta = "计算中..."

                    # 进度条
                    progress_pct = min(100, (total_chunks / estimated_total) * 100)
                    bar_length = 30
                    filled = int(bar_length * progress_pct / 100)
                    bar = "█" * filled + "░" * (bar_length - filled)

                    # 清除当前行并输出进度信息
                    print(f"\r  {bar} {progress_pct:.1f}% | {total_chunks}/{int(estimated_total)} 块 | {avg_speed:.1f} 块/秒 | ETA {eta}", end="", flush=True)

                    # 清空缓冲区并垃圾回收
                    batch_buffer.clear()
                    gc.collect()

                chunk_index += 1

            start_pos = end_pos - processor.chunk_overlap if end_pos < text_length else end_pos

        # 处理剩余的块
        if batch_buffer:
            vector_store.add_documents(batch_buffer)
            total_chunks += len(batch_buffer)
            batch_buffer.clear()
            gc.collect()

        # 换行（因为进度条使用了 \r）
        print()  # 换行

        # 显示文件处理完成信息
        file_elapsed = time.time() - file_start_time
        file_time_str = str(timedelta(seconds=int(file_elapsed)))
        print(f"  ✅ 文件处理完成 ({chunk_index} 个块)，耗时: {file_time_str}")

        # 清理文本数据
        del text
        gc.collect()

    if total_chunks == 0:
        print(f"❌ 未找到文档")
        return False

    # 计算总耗时
    total_elapsed = time.time() - start_time
    total_time_str = str(timedelta(seconds=int(total_elapsed)))

    print(f"\n✅ 共处理 {total_chunks} 个文档块")
    print(f"⏱️  总耗时: {total_time_str}")
    if total_elapsed > 0:
        print(f"⚡ 平均速度: {total_chunks / total_elapsed:.1f} 块/秒")

    # 获取数据库信息
    info = vector_store.get_collection_info()
    print(f"\n" + "=" * 60)
    print(f"✅ 向量数据库生成完成！")
    print(f"=" * 60)
    print(f"\n数据库信息:")
    print(f"  集合名称: {info['name']}")
    print(f"  文档数量: {info['count']}")
    print(f"  向量维度: {info['dimension']}")
    print(f"  保存路径: {info['persist_directory']}")
    print(f"\n文件大小:")

    # 计算文件大小
    chroma_sqlite = vector_db_path / "chroma.sqlite3"
    if chroma_sqlite.exists():
        size_mb = chroma_sqlite.stat().st_size / (1024 * 1024)
        print(f"  chroma.sqlite3: {size_mb:.2f} MB")

    print(f"\n下一步:")
    print(f"  1. 压缩向量数据库目录:")
    print(f"     cd backend/rag/data")
    print(f"     tar -czf chroma.tar.gz chroma/")
    print(f"\n  2. 上传到服务器的 /mnt/workspace/backend/rag/data/")
    print(f"  3. 在服务器上解压:")
    print(f"     cd /mnt/workspace/backend/rag/data")
    print(f"     tar -xzf chroma.tar.gz")
    print(f"     rm chroma.tar.gz")
    print(f"\n" + "=" * 60)

    return True


if __name__ == "__main__":
    try:
        success = build_vector_db()
        if success:
            print("\n✅ 成功！")
            sys.exit(0)
        else:
            print("\n❌ 失败")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
