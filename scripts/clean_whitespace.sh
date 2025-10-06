#!/bin/bash
# 清理项目中所有代码文件的行尾空白

echo "🧹 开始清理行尾空白..."

# 清理后端 Python 文件
echo "  📁 清理后端 Python 文件..."
find backend/app -name "*.py" -type f -exec sed -i 's/[[:space:]]*$//' {} \;

# 清理前端 TypeScript 文件
echo "  📁 清理前端 TypeScript 文件..."
find frontend -name "*.ts" -o -name "*.tsx" | xargs sed -i 's/[[:space:]]*$//'

# 清理前端 JavaScript 文件
echo "  📁 清理前端 JavaScript 文件..."
find frontend -name "*.js" -o -name "*.jsx" | xargs sed -i 's/[[:space:]]*$//'

echo "✅ 清理完成！"

