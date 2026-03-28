# RAZ 静态资源路由改造设计

## 概述

将 RAZ 静态资源路由从 `/raz/media/{level}/...` 统一改为 `/raz/level-{level}/...`，让 URL 路径与实际文件夹结构一致。

## 动机

- **路径一致性**: 实际文件夹命名为 `level-a`、`level-b`，URL 路径 `/raz/media/a/` 与文件系统不匹配
- **直观性**: `/raz/level-a/book/file.pdf` 更直观，一看就知道对应哪个文件夹
- **简化逻辑**: 减少 URL 与实际路径之间的转换层级

## 变更内容

### 1. 后端路由

**位置**: `app/routers/raz.py:273-288`

- 将路由 `@router.get("/raz/media/{level}/{book_dir}/{filename}")` 改为 `@router.get("/raz/level-{level}/{book_dir}/{filename}")`
- 内部文件查找逻辑保持不变（仍为 `RAZ_DIR / f"level-{level}" / book_dir / filename`）

### 2. API 接口

**位置**: `app/routers/raz.py:158-177`

修改 `/api/raz/book-detail/{level}/{book_dir}` 返回的 URL 格式：

```python
# 修改前
"pdf": f"/raz/media/{book.level}/{book_dir}/{book.pdf}"
"audio": f"/raz/media/{book.level}/{book_dir}/{book.audio}"

# 修改后
"pdf": f"/raz/{book.level}/{book_dir}/{book.pdf}"
"audio": f"/raz/{book.level}/{book_dir}/{book.audio}"
```

### 3. 前端模板

#### reader.html

**位置**: `app/templates/raz/reader.html:432-433`

更新 `bookData` 的 PDF 和音频 URL 构造：

```javascript
// 修改前
pdf: buildResourceUrl("/raz/media/{{ book.level }}/{{ book_dir }}/{{ book.pdf or 'book.pdf' }}"),
audio: {% if book.audio %}buildResourceUrl("/raz/media/{{ book.level }}/{{ book_dir }}/{{ book.audio }}"){% else %}null{% endif %},

// 修改后
pdf: buildResourceUrl("/raz/{{ book.level }}/{{ book_dir }}/{{ book.pdf or 'book.pdf' }}"),
audio: {% if book.audio %}buildResourceUrl("/raz/{{ book.level }}/{{ book_dir }}/{{ book.audio }}"){% else %}null{% endif %},
```

#### practice.html / book.html / index.html

检查这些模板是否包含硬编码的 `/raz/media/` 路径，如有则一并更新。

### 4. 静态资源服务器配置

静态资源服务器（通过 `StaticServer` 环境变量配置）也需要支持新路径格式 `/raz/level-a/...`。

例如 Nginx 配置：

```nginx
location ~ ^/raz/(level-[a-z]+)/(.+)$ {
    alias /path/to/data/raz/$1/$2;
}
```

## 测试计划

1. **路由测试**: 验证 `/raz/level-a/mybook/book.pdf` 能正常返回文件
2. **API 测试**: 验证 `/api/raz/book-detail/a/mybook` 返回的 URL 格式正确
3. **页面测试**: 验证 reader 页面能正常加载 PDF 和音频
4. **静态服务器测试**: 验证配置 StaticServer 后，新路径格式能正常工作

## 兼容性说明

这是一次破坏性变更：
- 所有使用 `/raz/media/` 的 URL 将失效
- 需要确保一次性更新所有相关代码
- 如有外部系统依赖此 URL，需要同步更新

## 回滚方案

如需回滚，恢复 `raz.py` 中的路由定义和 API 返回的 URL 格式即可。

## 相关文件

- `app/routers/raz.py`
- `app/templates/raz/reader.html`
- `app/templates/raz/practice.html`
- `app/templates/raz/book.html`
- `app/templates/raz/index.html`
