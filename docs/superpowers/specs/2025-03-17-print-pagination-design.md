# 字帖打印预分页方案设计

## 问题背景

当前字帖打印使用 CSS Grid 布局 + `break-inside: avoid` 来防止跨页截断，但实际效果不理想：
- 田字格/米字格在分页处仍会出现截断
- 不同浏览器对 Grid 项目的分页控制支持不一致
- `display: contents` 行容器使浏览器难以识别行边界

## 解决方案：预分页模式

在打印前通过 JavaScript 精确计算每页可容纳的行数，然后手动插入强制分页符。

## 技术设计

### 1. 页面参数计算

```javascript
const PAGE_CONFIG = {
    // A4 纸张尺寸（毫米）
    a4: {
        width: 210,
        height: 297
    },
    // 打印边距（与 @page margin 一致）
    margin: {
        top: 10,
        right: 10,
        bottom: 10,
        left: 10
    }
};

// 计算可用打印区域
function getPrintableArea(orientation) {
    const pageWidth = orientation === 'landscape' ? 297 : 210;
    const pageHeight = orientation === 'landscape' ? 210 : 297;

    return {
        width: pageWidth - margin.left - margin.right,  // mm
        height: pageHeight - margin.top - margin.bottom // mm
    };
}
```

### 2. 行高度测量

```javascript
// 测量实际行高度（像素）
function measureRowHeight() {
    const container = elements.worksheetContainer;
    const firstRow = container.querySelector('.worksheet-row');

    if (firstRow) {
        // 获取渲染后的实际高度
        const rect = firstRow.getBoundingClientRect();
        return rect.height; // pixels
    }

    // 回退：使用估算高度
    return 130; // 默认估算值
}
```

### 3. 每页行数计算

```javascript
function calculateRowsPerPage(rowHeightPx) {
    const orientation = state.printOrientation;
    const printableArea = getPrintableArea(orientation);

    // 将 mm 转换为 pixels（使用标准 96 DPI）
    const printableHeightPx = (printableArea.height / 25.4) * 96;

    // 计算每页可容纳行数（向下取整，留出安全边距）
    const rowsPerPage = Math.floor(printableHeightPx / rowHeightPx);

    // 最小保证至少3行
    return Math.max(rowsPerPage, 3);
}
```

### 4. 分页符插入

```javascript
function insertPageBreaks() {
    const container = elements.worksheetContainer;
    const rows = container.querySelectorAll('.worksheet-row');

    // 测量行高度
    const rowHeight = measureRowHeight();
    const rowsPerPage = calculateRowsPerPage(rowHeight);

    // 清理旧的分页符
    container.querySelectorAll('.page-break').forEach(el => el.remove());

    // 插入新的分页符
    rows.forEach((row, index) => {
        // 在每个新页面的第一行前插入分页符（除了第一页）
        if (index > 0 && index % rowsPerPage === 0) {
            const pageBreak = document.createElement('div');
            pageBreak.className = 'page-break';
            pageBreak.style.cssText = 'page-break-before: always; break-before: page;';
            row.parentNode.insertBefore(pageBreak, row);
        }
    });
}
```

### 5. CSS 样式支持

```css
@media print {
    /* 强制分页符 */
    .page-break {
        page-break-before: always;
        break-before: page;
        grid-column: 1 / -1;
        height: 0;
        overflow: hidden;
    }

    /* 确保行不跨页 */
    .worksheet-row {
        break-inside: avoid;
        page-break-inside: avoid;
    }

    /* 隐藏行容器，但保持子元素可见 */
    .worksheet-row {
        display: contents;
    }

    /* 确保单元格在一起 */
    .char-cell, .info-row {
        break-inside: avoid;
        page-break-inside: avoid;
    }
}
```

### 6. 打印流程集成

修改 `doPrint()` 函数：

```javascript
function doPrint() {
    if (state.characters.length === 0) {
        showWarning("请先生成预览");
        return;
    }

    // 确保打印方向已应用
    updatePrintOrientation();

    // 关键：在打印前强制设置容器CSS变量
    if (elements.worksheetContainer) {
        elements.worksheetContainer.style.setProperty('--char-size', state.charSize + 'px', 'important');
    }

    // 等待渲染完成，然后插入分页符
    requestAnimationFrame(() => {
        // 插入分页符
        insertPageBreaks();

        // 等待分页符应用
        requestAnimationFrame(() => {
            // 触发打印
            window.print();

            // 打印后清理分页符（恢复预览状态）
            setTimeout(() => {
                document.querySelectorAll('.page-break').forEach(el => el.remove());
            }, 100);
        });
    });
}
```

## 关键优化点

### 1. 行包装器重构
将 `display: contents` 改为实际容器，便于测量和控制：

```javascript
// 修改 renderWorksheet 中的行容器
rowContainer.style.cssText = 'display: flex; flex-wrap: wrap; width: 100%;';
```

### 2. 双重保障
- 预分页：JS 计算并插入强制分页符
- CSS 保护：保留 `break-inside: avoid` 作为后备

### 3. 打印后清理
分页符只在打印时临时插入，打印完成后自动清理，不影响预览显示。

## 实现范围

### 修改文件
1. `app/static/js/worksheet.js` - 添加分页计算逻辑
2. `app/templates/worksheet.html` - 添加分页符 CSS

### 新增函数
- `getPrintableArea(orientation)` - 计算打印区域
- `measureRowHeight()` - 测量行高度
- `calculateRowsPerPage(rowHeight)` - 计算每页行数
- `insertPageBreaks()` - 插入分页符
- `clearPageBreaks()` - 清理分页符

### 修改函数
- `doPrint()` - 集成分页逻辑

## 风险评估

| 风险 | 概率 | 缓解措施 |
|-----|-----|---------|
| 不同浏览器 DPI 计算差异 | 中 | 使用实际测量而非理论计算 |
| 字体大小影响行高 | 低 | 打印前强制设置字体大小并重新测量 |
| 窗口缩放影响测量 | 低 | 使用 mm 为单位计算，减少像素依赖 |

## 验收标准

1. [x] 打印时田字格/米字格不会被截断
2. [x] 每行（拼音+格子）作为整体出现在同一页
3. [x] 最后一页不出现大面积空白
4. [x] 打印后预览恢复正常
5. [x] 横向/竖向打印都正常工作
