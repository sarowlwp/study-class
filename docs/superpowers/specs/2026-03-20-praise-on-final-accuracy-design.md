# 设计文档：正确率超过 80% 才显示夸赞

**日期**: 2026-03-20
**状态**: 已批准

## 背景

当前汉字抽测功能（`quiz.html`）在用户每次点击"掌握"时都会弹出夸赞 toast 并播放语音。需求变更为：只在整轮测试结束后，最终正确率超过 80% 时才显示夸赞。

## 目标

- 移除测试过程中的逐题夸赞
- 在结果页（`result.html`）根据最终正确率判断是否显示夸赞
- 正确率 > 80% 时触发一次夸赞（toast + 语音）

## 不在范围内

- 后端逻辑无需修改
- 英语测验（`english/` 目录）不涉及

## 方案

方案 A（已选定）：将 praise 逻辑从 `quiz.html` 迁移至 `result.html`，在结果加载后按正确率条件触发。

## 详细设计

### quiz.html 变更（删除）

删除以下内容：
1. praise toast HTML（`#praise-toast` 整个 `<div>`）
2. JS 变量：`PRAISE_TEXTS`、`_praiseTimer`
3. JS 函数：`praise()`、`showPraiseToast()`
4. `submitResult` 中的条件调用：`if (result === 'mastered') { praise(); }`

### result.html 变更（新增）

1. 在页面顶部新增 praise toast HTML（与 quiz.html 现有结构一致）：
   ```html
   <div id="praise-toast" ...>
     <img src="yoshi.png" ...>
     <div id="praise-text" ...></div>
   </div>
   ```

2. 在 `<script>` 中新增：
   - `PRAISE_TEXTS`、`_praiseTimer`
   - `praise()` 函数
   - `showPraiseToast()` 函数

3. 在 `loadResults()` 计算 accuracy 后添加：
   ```js
   if (accuracy > 80) {
       praise();
   }
   ```

## 正确率计算

沿用现有逻辑：`accuracy = Math.round((todayStats.mastered / todayStats.total) * 100)`

触发条件：`accuracy > 80`（严格大于，即 81% 及以上触发）

## 测试要点

- 正确率 = 80%：不触发夸赞
- 正确率 = 81%：触发夸赞
- 正确率 = 100%：触发夸赞
- 正确率 < 80%：不触发夸赞
