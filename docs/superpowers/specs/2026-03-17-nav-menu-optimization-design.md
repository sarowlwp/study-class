# 顶部导航菜单优化 - 设计文档

**日期:** 2026-03-17
**类型:** UI 优化
**状态:** 待实现

## 背景与目标

优化站点顶部导航菜单，提升用户体验和导航效率。

## 需求清单

1. **增加可点击区域** - 导航项的点击区域从 `px-3 py-2` 增大到 `px-4 py-2.5`，方便用户点击
2. **新增教材预览到导航** - 将原先仅在首页快速链接中的"教材预览"提升到一级导航栏
3. **整站更名** - 站点名称从"汉字抽测卡"改为"语文学习小工具"
4. **移除打印导航项** - 从顶部导航移除"打印"入口，但保留 `/print` 路由的功能

## 当前状态

### 当前导航结构 (base.html)

```html
<nav class="bg-white shadow-md">
    <div class="max-w-4xl mx-auto px-4 py-3">
        <div class="flex items-center justify-between">
            <a href="/" class="flex items-center space-x-2">
                <span class="text-2xl">📚</span>
                <span class="text-xl font-bold text-green-600">汉字抽测卡</span>
            </a>
            <div class="flex space-x-4">
                <a href="/" class="text-gray-600 hover:text-green-600 px-3 py-2 rounded-lg hover:bg-green-50 transition">首页</a>
                <a href="/mistakes" class="text-gray-600 hover:text-red-600 px-3 py-2 rounded-lg hover:bg-red-50 transition">错字本</a>
                <a href="/print" class="text-gray-600 hover:text-blue-600 px-3 py-2 rounded-lg hover:bg-blue-50 transition">打印</a>
                <a href="/worksheet" class="text-gray-600 hover:text-purple-600 px-3 py-2 rounded-lg hover:bg-purple-50 transition">📄 字帖</a>
            </div>
        </div>
    </div>
</nav>
```

**当前导航项：**
- 首页
- 错字本
- 打印
- 📄 字帖

## 修改后设计

### 修改后导航结构

```html
<nav class="bg-white shadow-md">
    <div class="max-w-4xl mx-auto px-4 py-3">
        <div class="flex items-center justify-between">
            <a href="/" class="flex items-center space-x-2">
                <span class="text-2xl">📚</span>
                <span class="text-xl font-bold text-green-600">语文学习小工具</span>
            </a>
            <div class="flex space-x-4">
                <a href="/" class="text-gray-600 hover:text-green-600 px-4 py-2.5 rounded-lg hover:bg-green-50 transition">汉字抽测卡</a>
                <a href="/mistakes" class="text-gray-600 hover:text-red-600 px-4 py-2.5 rounded-lg hover:bg-red-50 transition">❌ 错字本</a>
                <a href="/worksheet" class="text-gray-600 hover:text-purple-600 px-4 py-2.5 rounded-lg hover:bg-purple-50 transition">📄 字帖</a>
                <a href="/pdfs" class="text-gray-600 hover:text-orange-600 px-4 py-2.5 rounded-lg hover:bg-orange-50 transition">📚 教材预览</a>
            </div>
        </div>
    </div>
</nav>
```

**修改后导航项：**
1. 汉字抽测卡（原"首页"更名）
2. ❌ 错字本（增加 emoji）
3. 📄 字帖
4. 📚 教材预览（新增）

### 修改点对比表

| 位置 | 当前 | 修改后 |
|------|------|--------|
| 站点标题 | 📚 汉字抽测卡 | 📚 语文学习小工具 |
| 导航项 1 | 首页 | 汉字抽测卡 |
| 导航项 2 | 错字本 | ❌ 错字本（增加 emoji）|
| 导航项 3 | 打印 | 📄 字帖 |
| 导航项 4 | 📄 字帖 | 📚 教材预览 |
| 点击区域 | px-3 py-2 | px-4 py-2.5（增大）|

## 影响范围

### 需要修改的文件

- `app/templates/base.html` - 修改导航菜单和站点标题

### 不需要修改的文件

- 其他页面模板（index.html、mistakes.html 等）继承 base.html，无需单独修改
- 后端路由（打印功能保留）
- CSS 样式（使用现有的 Tailwind 类）

## 兼容性说明

- **打印功能保留**: `/print` 路由仍然可用，用户可通过直接访问 URL 使用
- **首页快速链接不变**: index.html 中的快速链接卡片保持不变
- **Footer 站点名**: 同步更新为"语文学习小工具"

## 验收标准

1. [ ] 顶部导航显示"语文学习小工具"作为站点标题
2. [ ] 导航项顺序为：汉字抽测卡、❌ 错字本、📄 字帖、📚 教材预览
3. [ ] 导航项可点击区域明显增大（px-4 py-2.5）
4. [ ] 打印页面通过 `/print` 仍可正常访问
5. [ ] 所有页面显示一致的导航菜单
6. [ ] Footer 显示"语文学习小工具 - 每日进步一点点"
