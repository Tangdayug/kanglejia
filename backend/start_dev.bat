@echo off
REM SecondNature 本地开发启动脚本
REM 使用方法：将此文件复制到 backend 目录，然后双击运行

echo ========================================
echo  SecondNature 本地开发环境启动
echo ========================================
echo.

REM 检查Python版本
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.11+
    pause
    exit /b 1
)

echo [1/5] 检查环境变量...

REM 检查 .env 文件
if not exist .env (
    echo [警告] 未找到 .env 文件
    echo.
    echo 请创建 .env 文件并添加以下内容：
    echo DEEPSEEK_API_KEY=your_deepseek_api_key_here
    echo JWT_SECRET_KEY=your-secret-key-must-be-at-least-32-characters-long
    echo.
    set /p CONTINUE="是否继续启动？(Y/N): "
    if /i not "%CONTINUE%"=="Y" (
        pause
        exit /b 1
    )
)

echo [2/5] 安装/检查依赖...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

echo [3/5] 检查向量数据库...

REM 检查是否需要初始化向量数据库
if not exist rag\indices\faiss (
    echo [信息] 向量数据库不存在，正在初始化...
    python -c "from rag.retriever_faiss import get_rag_retriever; result = get_rag_retriever().initialize_knowledge_base(); print(f'初始化状态: {result[\"status\"]}')"
    if errorlevel 1 (
        echo [错误] 向量数据库初始化失败
        pause
        exit /b 1
    )
) else (
    echo [信息] 向量数据库已存在，跳过初始化
    echo [提示] 如需重新初始化，请删除 rag\indices\faiss 目录后重启
)

echo [4/5] 启动后端服务...
echo.
echo ========================================
echo  后端服务启动成功！
echo ========================================
echo.
echo 访问地址:
echo   - 后端API: http://localhost:7861
echo   - API文档: http://localhost:7861/docs
echo   - 前端界面: http://localhost:7861/index.html
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

REM 启动后端
python main.py

pause
