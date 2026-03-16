from PyPDF2 import PdfReader
import re

reader = PdfReader('/Users/liuwenping/Documents/fliggy/study-class/data/pdfs/义务教育教科书·语文二年级下册.pdf')
titles = {}
total_pages = len(reader.pages)

for i in range(min(120, total_pages)):
    page = reader.pages[i]
    text = page.extract_text() or ''
    lines = text.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 模式1: 从'本文作者'行提取，取"改动。"后面的内容
        # 如 "本文作者经绍珍，选作课文时有改动。找春天2"
        if '本文' in line and '改动' in line:
            match = re.search(r'改动[。，]([^\d]{2,12})(\d+)\s*$', line)
            if match:
                num = match.group(2)
                title = match.group(1).strip('"').strip('，').strip('。').strip()
                if len(title) >= 3:
                    lesson_key = f'课文 {num}'
                    if lesson_key not in titles or len(title) > len(titles.get(lesson_key, '')):
                        titles[lesson_key] = title
            continue

        # 模式2: 普通行尾匹配（取最长匹配，但过滤无效关键词）
        # 先尝试匹配较长的标题（6-15个字符），如果无效再尝试短的
        found = False
        for length in range(15, 5, -1):  # 从长到短：15到6个字符
            pattern = r'([\u4e00-\u9fa5]{' + str(length) + r'})(\d+)\s*$'
            match = re.search(pattern, line)
            if match:
                num = match.group(2)
                title = match.group(1).strip()
                lesson_num = int(num)

                # 过滤掉包含无效关键词的标题
                invalid_keywords = ['本文', '作者', '朗读', '按照', '可以', '然后', '也是', '就是', '炒饭']
                if any(kw in title for kw in invalid_keywords):
                    continue

                lesson_key = f'课文 {lesson_num}'
                titles[lesson_key] = title
                found = True
                break

        if found:
            continue

        # 模式3: 如果长匹配没找到，尝试4-6个字符的短匹配
        for length in range(6, 3, -1):
            pattern = r'([\u4e00-\u9fa5]{' + str(length) + r'})(\d+)\s*$'
            match = re.search(pattern, line)
            if match:
                num = match.group(2)
                title = match.group(1).strip()
                lesson_num = int(num)

                invalid_keywords = ['本文', '作者', '朗读', '按照', '可以', '然后', '也是', '就是', '炒饭', '你的', '一只']
                if any(kw in title for kw in invalid_keywords):
                    continue

                lesson_key = f'课文 {lesson_num}'
                if lesson_key not in titles:
                    titles[lesson_key] = title
                break

print('找到的标题:')
for k in sorted(titles.keys(), key=lambda x: (x.split()[0], int(x.split()[1]))):
    print(f'  {k}: {titles[k]}')
