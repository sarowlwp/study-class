#!/usr/bin/env python3
"""
直接下载微信音频文件
需要提供音频file_id列表
"""

import requests
import time
from pathlib import Path

# 音频保存目录
AUDIO_DIR = Path("/Users/liuwenping/Documents/fliggy/study-class/data/english/downloaded/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# HTTP请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://mp.weixin.qq.com/",
    "Accept": "*/*",
    "Range": "bytes=0-"
}


def download_audio(file_id: str, filename: str) -> bool:
    """下载单个音频文件"""
    url = f"https://res.wx.qq.com/voice/getvoice?mediaid={file_id}"
    save_path = AUDIO_DIR / filename

    if save_path.exists():
        print(f"  已存在: {filename}")
        return True

    try:
        print(f"  下载: {filename}")
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code in [200, 206]:  # 206是Partial Content
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"    -> 成功 ({len(response.content)} bytes)")
            return True
        else:
            print(f"    -> 失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"    -> 错误: {e}")
        return False


def main():
    """主函数 - 示例：下载P1的两段音频"""
    print("=" * 60)
    print("微信音频下载工具")
    print("=" * 60)

    # 示例音频列表 (从浏览器中提取的真实ID)
    # 格式: (file_id, filename)
    sample_audios = [
        ("MzI4MjE1MjMzOV8yMjQ3NTM5OTg3", "001_01_课文朗读P1-1.mp3"),
        ("MzI4MjE1MjMzOV8yMjQ3NTM5OTg0", "001_02_课文朗读P1-2.mp3"),
    ]

    print(f"\n准备下载 {len(sample_audios)} 个音频文件...\n")

    success_count = 0
    for file_id, filename in sample_audios:
        if download_audio(file_id, filename):
            success_count += 1
        time.sleep(1)  # 避免请求过快

    print(f"\n{'=' * 60}")
    print(f"下载完成: {success_count}/{len(sample_audios)}")
    print(f"保存位置: {AUDIO_DIR}")
    print("=" * 60)

    # 提示用户如何获取更多音频ID
    print("\n要获取更多音频文件，请:")
    print("1. 在Chrome中打开微信文章")
    print("2. 按F12打开开发者工具")
    print("3. 切换到Console面板")
    print("4. 运行 batch_extract_audios.js 中的代码")
    print("5. 将获取的file_id添加到上面的sample_audios列表中")


if __name__ == "__main__":
    main()
