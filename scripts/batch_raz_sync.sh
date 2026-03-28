#!/bin/bash
# 批量生成 RAZ book.json - 每本书单独进程避免 PaddleOCR 内存泄漏

# 修复 OpenMP 冲突
export KMP_DUPLICATE_LIB_OK=TRUE

PYTHON=".venv/bin/python3.11"
SCRIPT="-m scripts.raz_sync_processor"
MODEL="${1:-base}"
FORCE="${2:-}"
LEVELS=("level-aa" "level-a" "level-b")
TOTAL=0
SUCCESS=0
FAILED=0

log() {
    echo "[$(date '+%H:%M:%S')] $1"
}

for level in "${LEVELS[@]}"; do
    log "=== 处理 $level ==="
    for book_dir in data/raz/$level/*/; do
        if [ -f "$book_dir/book.pdf" ] && [ -f "$book_dir/audio.mp3" ]; then
            book_name=$(basename "$book_dir")
            ((TOTAL++))

            if [ -f "$book_dir/book.json" ] && [ "$FORCE" != "--force" ]; then
                log "  ✓ $level/$book_name 已存在，跳过"
                ((SUCCESS++))
                continue
            fi

            log "  处理 $level/$book_name ..."
            # 每本书单独进程，避免 PaddleOCR 内存累积
            if $PYTHON $SCRIPT -i "$book_dir" --model "$MODEL" $FORCE; then
                log "  ✓ $level/$book_name 成功"
                ((SUCCESS++))
            else
                log "  ✗ $level/$book_name 失败"
                ((FAILED++))
            fi
            # 短暂延迟让内存完全释放
            sleep 1
        fi
    done
done

log "========================"
log "总计: $TOTAL"
log "成功: $SUCCESS"
log "失败: $FAILED"
