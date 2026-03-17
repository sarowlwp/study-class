const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:8000';

test.describe('字帖功能测试', () => {
  test.beforeEach(async ({ page }) => {
    // 清除 localStorage 以确保干净的测试环境
    await page.goto(BASE_URL + '/worksheet');
    await page.evaluate(() => localStorage.clear());
    await page.reload();

    // 等待页面加载完成
    await page.waitForSelector('#worksheet-container');
  });

  test.describe('字体大小调整', () => {
    test('字体大小滑块存在且有正确的默认值', async ({ page }) => {
      const slider = page.locator('#char-size-input');
      await expect(slider).toBeVisible();
      await expect(slider).toHaveAttribute('min', '24');
      await expect(slider).toHaveAttribute('max', '72');
      await expect(slider).toHaveAttribute('step', '4');
      await expect(slider).toHaveValue('48');

      // 检查显示值
      const valueDisplay = page.locator('#char-size-value');
      await expect(valueDisplay).toHaveText('48px');
    });

    test('拖动滑块改变字体大小', async ({ page }) => {
      // 首先生成一个预览
      await page.click('#preview-btn');
      await page.waitForTimeout(1000);

      // 获取初始字体大小
      const container = page.locator('#worksheet-container');
      const initialSize = await container.evaluate(el =>
        getComputedStyle(el).getPropertyValue('--char-size')
      );
      expect(initialSize.trim()).toBe('48px');

      // 拖动滑块到 60px
      const slider = page.locator('#char-size-input');
      await slider.fill('60');

      // 等待防抖
      await page.waitForTimeout(300);

      // 检查 CSS 变量已更新
      const newSize = await container.evaluate(el =>
        getComputedStyle(el).getPropertyValue('--char-size')
      );
      expect(newSize.trim()).toBe('60px');

      // 检查显示值
      await expect(page.locator('#char-size-value')).toHaveText('60px');
    });

    test('字体大小持久化到 localStorage', async ({ page }) => {
      // 改变字体大小
      const slider = page.locator('#char-size-input');
      await slider.fill('64');
      await page.waitForTimeout(300);

      // 刷新页面
      await page.reload();
      await page.waitForSelector('#char-size-input');

      // 检查值已恢复
      await expect(page.locator('#char-size-input')).toHaveValue('64');
      await expect(page.locator('#char-size-value')).toHaveText('64px');
    });
  });

  test.describe('自动触发预览', () => {
    test('修改网格类型自动触发预览', async ({ page }) => {
      // 先生成初始预览
      await page.click('#preview-btn');
      await page.waitForTimeout(1000);

      // 记录当前内容
      const initialContent = await page.locator('#worksheet-container').innerHTML();

      // 切换网格类型到"米字格"
      await page.click('input[name="grid-type"][value="mi"]');

      // 等待自动触发
      await page.waitForTimeout(300);

      // 检查内容已更新（应该有 mi 类）
      const gridBoxes = page.locator('.grid-box.mi');
      await expect(gridBoxes.first()).toBeVisible();
    });

    test('修改每行方格数自动触发预览', async ({ page }) => {
      // 先生成初始预览
      await page.click('#preview-btn');
      await page.waitForTimeout(1000);

      // 修改每行方格数
      const colsSlider = page.locator('#cols-input');
      await colsSlider.fill('7');

      // 等待防抖（200ms + buffer）
      await page.waitForTimeout(400);

      // 检查 CSS 变量已更新
      const container = page.locator('#worksheet-container');
      const cols = await container.evaluate(el =>
        getComputedStyle(el).getPropertyValue('--cols')
      );
      expect(cols.trim()).toBe('7');
    });

    test('修改显示拼音自动触发预览', async ({ page }) => {
      // 先生成初始预览
      await page.click('#preview-btn');
      await page.waitForTimeout(1000);

      // 取消显示拼音
      await page.click('#show-pinyin');

      // 等待自动触发
      await page.waitForTimeout(300);

      // 检查拼音已隐藏
      const pinyinElements = page.locator('.pinyin');
      const count = await pinyinElements.count();
      if (count > 0) {
        await expect(pinyinElements.first()).not.toBeVisible();
      }
    });

    test('首次加载自动生成预览（错字本）', async ({ page }) => {
      // 等待页面加载和自动预览生成
      await page.waitForTimeout(2000);

      // 检查预览已生成（非空状态）
      const emptyState = page.locator('.empty-state');
      await expect(emptyState).not.toBeVisible();

      // 检查有字符单元格
      const charCells = page.locator('.char-cell');
      await expect(charCells.first()).toBeVisible();
    });

    test('生成预览按钮仍然可用', async ({ page }) => {
      const previewBtn = page.locator('#preview-btn');
      await expect(previewBtn).toBeVisible();

      // 点击生成预览
      await previewBtn.click();
      await page.waitForTimeout(1000);

      // 检查预览已生成
      const charCells = page.locator('.char-cell');
      await expect(charCells.first()).toBeVisible();
    });
  });

  test.describe('打印一致性', () => {
    test('打印样式继承字体大小', async ({ page }) => {
      // 设置字体大小
      const slider = page.locator('#char-size-input');
      await slider.fill('56');
      await page.waitForTimeout(300);

      // 检查打印样式
      const printStyles = await page.evaluate(() => {
        const styleSheets = Array.from(document.styleSheets);
        for (const sheet of styleSheets) {
          try {
            const rules = Array.from(sheet.cssRules || sheet.rules || []);
            for (const rule of rules) {
              if (rule.cssText && rule.cssText.includes('@media print')) {
                return rule.cssText;
              }
            }
          } catch (e) {
            // 跨域样式表可能无法访问
          }
        }
        return null;
      });

      // 打印样式应该包含 --char-size
      if (printStyles) {
        expect(printStyles).toContain('--char-size');
      }
    });
  });
});
