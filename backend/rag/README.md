# RAG 知识库目录说明

本目录用于存放 SecondNature 的健康知识库与向量索引。**所有数据均位于本项目内**，不需要引用 `/opt/xiaozhi-server` 等外部目录。

## 目录结构

```text
backend/rag/
├── data/                   # 原始知识库文档（PDF / DOC / DOCX）
│   └── *.pdf / *.docx
├── indices/
│   └── faiss/              # 生成的 FAISS 向量索引（运行时自动生成）
│       ├── health_knowledge.faiss
│       └── health_knowledge_metadata.pkl
├── legacy/                 # 旧版 ChromaDB 脚本，已停止维护，仅供参考
│   ├── init_rag.py
│   ├── rebuild_vectordb.py
│   ├── build_vector_db_locally.py
│   ├── auto_fix.py
│   ├── vector_store.py
│   └── retriever.py
├── document_processor.py   # 文档解析与分块
├── retriever_faiss.py      # 当前使用的 FAISS 检索器
├── vector_store_faiss.py   # 当前使用的 FAISS 向量存储
└── README.md               # 本文件
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `RAG_KNOWLEDGE_BASE_PATH` | `./rag/data` | 原始知识库文档目录 |
| `RAG_VECTOR_DB_PATH` | `./rag/indices/faiss` | 生成的 FAISS 索引目录 |
| `SKIP_RAG_INIT` | `false` | 若设为 `true`，空索引时不会自动初始化 |

## 自动热更新

应用启动后，`service/rag_watcher_service.py` 会每 30 秒扫描 `RAG_KNOWLEDGE_BASE_PATH`：

- 检测到新增/修改/删除 PDF、DOC、DOCX 文件时，自动重建 FAISS 索引；
- 所有文档被删除时，自动清空索引。

## 手动重建

如需立即强制重建向量索引，可调用后端 API：

```bash
curl -X POST http://localhost:7861/api/rag/rebuild
```

或在后端目录下执行：

```bash
python -c "from rag.retriever_faiss import get_rag_retriever; get_rag_retriever().rebuild_knowledge_base()"
```

## 注意事项

- `legacy/` 中的 ChromaDB 代码不再使用，保留仅作历史参考。
- FAISS 索引是构建产物，通常不需要提交到 Git；已在 `.gitignore` 中排除。
