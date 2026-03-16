#!/bin/bash
# Docker 镜像构建脚本

set -e

# 配置
IMAGE_NAME="hanzi-quiz"
IMAGE_TAG=${1:-latest}
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

echo "========================================"
echo "  构建 Docker 镜像: ${FULL_IMAGE_NAME}"
echo "========================================"

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    exit 1
fi

# 显示构建信息
echo ""
echo "构建信息:"
echo "  - 镜像名称: ${IMAGE_NAME}"
echo "  - 镜像标签: ${IMAGE_TAG}"
echo "  - 完整名称: ${FULL_IMAGE_NAME}"
echo "  - 构建时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 构建镜像
echo "开始构建..."
docker build \
    --tag "${FULL_IMAGE_NAME}" \
    --tag "${IMAGE_NAME}:latest" \
    --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
    --build-arg VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown') \
    .

echo ""
echo "========================================"
echo "  构建成功!"
echo "========================================"
echo ""
echo "镜像信息:"
docker images "${FULL_IMAGE_NAME}" --format "  - 名称: {{.Repository}}:{{.Tag}}\n  - 大小: {{.Size}}\n  - 创建时间: {{.CreatedAt}}"
echo ""
echo "运行命令:"
echo "  ./docker-run.sh"
echo "  或"
echo "  docker run -d -p 8000:8000 --name hanzi-quiz ${FULL_IMAGE_NAME}"
