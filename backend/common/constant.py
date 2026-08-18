from common.config import config

HOST = config.env.get('HOST')
PORT = config.env.get('PORT')

MYSQL_DIALECT = config.env.get("MYSQL_DIALECT")
MYSQL_HOST = config.env.get("MYSQL_HOST")
MYSQL_PORT = config.env.get("MYSQL_PORT")
MYSQL_USER = config.env.get("MYSQL_USER")
MYSQL_PASSWORD = config.env.get("MYSQL_PASSWORD")
MYSQL_DATABASE = config.env.get("MYSQL_DATABASE")

TOKEN_EXPIRE_DAYS = 7
TOKEN_EXPIRE_MINUTES = 0
TOKEN_EXPIRE_SECONDS = 0

# DeepSeek API Configuration
DEEPSEEK_API_KEY = config.env.get("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = config.env.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = config.env.get("DEEPSEEK_MODEL", "deepseek-chat")

# Local Embedding Configuration
EMBEDDING_MODEL_NAME = config.env.get("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5")

# RAG Configuration
RAG_KNOWLEDGE_BASE_PATH = config.env.get("RAG_KNOWLEDGE_BASE_PATH", "./rag/data")
RAG_VECTOR_DB_PATH = config.env.get("RAG_VECTOR_DB_PATH", "./rag/indices/faiss")

# Chat Configuration
CHAT_MAX_HISTORY_ROUNDS = int(config.env.get("CHAT_MAX_HISTORY_ROUNDS", "12"))

# XiaoZhi Hardware Bridge Configuration
XIAOZHI_SYSTEM_TOKEN = config.env.get('XIAOZHI_SYSTEM_TOKEN')
XIAOZHI_DEVICE_WHITELIST_ENABLED = config.env.get('XIAOZHI_DEVICE_WHITELIST_ENABLED', 'false').lower() == 'true'
XIAOZHI_AGENT_NAME = config.env.get('XIAOZHI_AGENT_NAME', 'second-nature')

# JWT Configuration
JWT_SECRET_KEY = config.env.get("JWT_SECRET_KEY")
# 禁用认证（用于魔搭创空间演示）
DISABLE_AUTH = config.env.get("DISABLE_AUTH", "false").lower() == "true"

# Baidu OCR Configuration
BAIDU_OCR_APP_ID = config.env.get("BAIDU_OCR_APP_ID")
BAIDU_OCR_API_KEY = config.env.get("BAIDU_OCR_API_KEY")
BAIDU_OCR_SECRET_KEY = config.env.get("BAIDU_OCR_SECRET_KEY")
