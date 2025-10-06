#!/bin/bash

# 创建Agent项目目录结构
# 此脚本根据项目结构文档自动生成所有目录和文件

# 设置颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}开始创建Agent项目目录结构...${NC}"

# 创建后端目录结构
echo -e "${GREEN}创建后端目录结构...${NC}"

# 后端主目录
mkdir -p backend/app/{api/{endpoints},core,db,models,schemas,services,ai/{clients,tools/general},websocket}
mkdir -p backend/{alembic/versions,tests/{test_api,test_services,test_tools}}

# 创建必要的Python文件
# API层
touch backend/app/api/__init__.py
touch backend/app/api/router.py
touch backend/app/api/endpoints/__init__.py
touch backend/app/api/endpoints/chat.py
touch backend/app/api/endpoints/session.py
touch backend/app/api/endpoints/user.py

# 核心配置
touch backend/app/core/__init__.py
touch backend/app/core/config.py
touch backend/app/core/security.py

# 数据库
touch backend/app/db/__init__.py
touch backend/app/db/base.py
touch backend/app/db/session.py

# 数据模型
touch backend/app/models/__init__.py
touch backend/app/models/chat.py
touch backend/app/models/session.py
touch backend/app/models/user.py

# Pydantic模式
touch backend/app/schemas/__init__.py
touch backend/app/schemas/chat.py
touch backend/app/schemas/session.py
touch backend/app/schemas/user.py

# 服务层
touch backend/app/services/__init__.py
touch backend/app/services/chat_service.py
touch backend/app/services/history_service.py
touch backend/app/services/session_service.py

# AI服务层
touch backend/app/ai/__init__.py
touch backend/app/ai/factory.py
touch backend/app/ai/function_calling.py

# AI客户端
touch backend/app/ai/clients/__init__.py
touch backend/app/ai/clients/base.py
touch backend/app/ai/clients/qwen_client.py

# 工具
touch backend/app/ai/tools/__init__.py
touch backend/app/ai/tools/registry.py
touch backend/app/ai/tools/executor.py
touch backend/app/ai/tools/base.py

# 通用工具
touch backend/app/ai/tools/general/__init__.py
touch backend/app/ai/tools/general/search.py
touch backend/app/ai/tools/general/calculator.py
touch backend/app/ai/tools/general/weather.py

# WebSocket
touch backend/app/websocket/__init__.py
touch backend/app/websocket/connection.py
touch backend/app/websocket/handler.py
touch backend/app/websocket/session.py

# 应用入口
touch backend/app/__init__.py
touch backend/app/main.py

# 数据库迁移
touch backend/alembic/env.py
touch backend/alembic/script.py.mako

# 测试
touch backend/tests/__init__.py
touch backend/tests/conftest.py

# 配置文件
touch backend/.env
touch backend/.env.example
touch backend/alembic.ini
touch backend/pyproject.toml
touch backend/Dockerfile
touch backend/requirements.txt

# 创建前端目录结构
echo -e "${GREEN}创建前端目录结构...${NC}"

# 前端主目录
mkdir -p frontend/app/{chat/\[session_id\],login,register}
mkdir -p frontend/components/{chat,ui,layout}
mkdir -p frontend/hooks
mkdir -p frontend/lib
mkdir -p frontend/store
mkdir -p frontend/types
mkdir -p frontend/public
mkdir -p frontend/styles

# 创建必要的前端文件
# 页面
touch frontend/app/layout.tsx
touch frontend/app/page.tsx
touch frontend/app/chat/page.tsx
touch frontend/app/chat/\[session_id\]/page.tsx
touch frontend/app/login/page.tsx
touch frontend/app/register/page.tsx

# 组件
touch frontend/components/chat/ChatWindow.tsx
touch frontend/components/chat/ChatInput.tsx
touch frontend/components/chat/MessageList.tsx
touch frontend/components/chat/Message.tsx
touch frontend/components/ui/Button.tsx
touch frontend/components/ui/Input.tsx
touch frontend/components/ui/Modal.tsx
touch frontend/components/layout/Header.tsx
touch frontend/components/layout/Sidebar.tsx
touch frontend/components/layout/Footer.tsx

# Hooks
touch frontend/hooks/useChat.ts
touch frontend/hooks/useWebSocket.ts
touch frontend/hooks/useAuth.ts

# 工具库
touch frontend/lib/api.ts
touch frontend/lib/websocket.ts
touch frontend/lib/utils.ts

# 状态管理
touch frontend/store/chatStore.ts
touch frontend/store/sessionStore.ts
touch frontend/store/userStore.ts

# TypeScript类型
touch frontend/types/chat.ts
touch frontend/types/session.ts
touch frontend/types/user.ts

# 样式
touch frontend/styles/globals.css

# 配置文件
touch frontend/.env.local
touch frontend/.env.example
touch frontend/next.config.js
touch frontend/tailwind.config.js
touch frontend/tsconfig.json
touch frontend/package.json
touch frontend/Dockerfile

# 创建项目根目录文件
echo -e "${GREEN}创建项目根目录文件...${NC}"
touch docker-compose.yml
touch .gitignore
touch README.md

echo -e "${YELLOW}项目目录结构创建完成!${NC}"
echo -e "项目位于: $(pwd)"

# 显示目录树
if command -v tree &> /dev/null; then
    echo -e "${GREEN}项目目录树:${NC}"
    tree -L 3
else
    echo -e "${YELLOW}提示: 安装tree命令可以查看完整的目录树结构${NC}"
    echo -e "${YELLOW}可以使用 'sudo apt-get install tree' 或 'brew install tree' 安装${NC}"
fi 