#!/bin/bash
# Docker 容器运行脚本

set -e

# 配置
IMAGE_NAME="hanzi-quiz"
CONTAINER_NAME="hanzi-quiz"
HOST_PORT=${1:-8000}
CONTAINER_PORT=8000

echo "========================================"
echo "  启动汉字抽测卡服务"
echo "========================================"
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    exit 1
fi

# 检查镜像是否存在
if ! docker images "${IMAGE_NAME}" | grep -q "${IMAGE_NAME}"; then
    echo "错误: 镜像 ${IMAGE_NAME} 不存在"
    echo "请先运行: ./docker-build.sh"
    exit 1
fi

# 停止并删除已存在的容器
if docker ps -a | grep -q "${CONTAINER_NAME}"; then
    echo "停止已存在的容器..."
    docker stop "${CONTAINER_NAME}" >/dev/null 2>&1 || true
    docker rm "${CONTAINER_NAME}" >/dev/null 2>&1 || true
fi

echo "启动容器..."
echo "  - 容器名称: ${CONTAINER_NAME}"
echo "  - 主机端口: ${HOST_PORT}"
echo "  - 容器端口: ${CONTAINER_PORT}"
echo ""

# 运行容器
docker run -d \
    --name "${CONTAINER_NAME}" \
    -p "${HOST_PORT}:${CONTAINER_PORT}" \
    --restart unless-stopped \
    -e PYTHONUNBUFFERED=1 \
    "${IMAGE_NAME}:latest"

echo "========================================"
echo "  服务启动成功!"
echo "========================================"
echo ""
echo "访问地址:"
echo "  - 首页:       http://localhost:${HOST_PORT}/"
echo "  - API 文档:   http://localhost:${HOST_PORT}/docs"
echo "  - 健康检查:   http://localhost:${HOST_PORT}/api/characters"
echo ""
echo "常用命令:"
echo "  - 查看日志:   docker logs -f ${CONTAINER_NAME}"
echo "  - 停止服务:   docker stop ${CONTAINER_NAME}"
echo "  - 重启服务:   docker restart ${CONTAINER_NAME}"
echo "  - 进入容器:   docker exec -it ${CONTAINER_NAME} /bin/bash"
echo ""

# 等待服务启动
echo "等待服务启动..."
sleep 3

# 检查服务是否健康
if curl -s "http://localhost:${HOST_PORT}/api/characters" >/dev/null 2>&1; then
    echo "✅ 服务运行正常!"
else
    echo "⚠️  服务可能还在启动中，请稍后访问"
    echo "   查看日志: docker logs -f ${CONTAINER_NAME}"
fi
