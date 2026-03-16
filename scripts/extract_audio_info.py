#!/usr/bin/env python3
"""
通过浏览器批量提取微信文章音频信息
"""

import json
import time

# 文章列表
ARTICLES = [
    {"index":1,"title":"课本和朗读2024秋：P1外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247539989&idx=3&sn=c0e42ba3822c12f41b36b46b92482830&chksm=eb9c41e9dcebc8fff4c91ad6a8905e92fc4795bd35aed771ecbbae5c976cfbb4dd269cb0ef68#rd"},
    {"index":2,"title":"课本和朗读2024秋：P2外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247539989&idx=2&sn=203f63dba855b8bacf189b21e3b09273&chksm=eb9c41e9dcebc8ff9c2261f6529e73e9f9b6e8f16f471ed8fa3b7e13cd2c7df89ec1eddf8e9c#rd"},
    {"index":3,"title":"课本和朗读2024秋：P3外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247539989&idx=1&sn=0e7a887cd9ab540c42bfc822d3c1d513&chksm=eb9c41e9dcebc8ff440a7e53269f8cc0f669f8ad6d19d3b4b98fd41d7c8b27392bc5367e0fff#rd"},
    {"index":4,"title":"课本和朗读2024秋：P4外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540059&idx=4&sn=aba3d6ccd9f9789c6df745e06e2b9901&chksm=eb9c41a7dcebc8b176f9fa1a22e5f062f7085eb488fa253effe4beabfdb1869cca6d99f32072#rd"},
    {"index":5,"title":"课本和朗读2024秋：P5外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540059&idx=3&sn=0a09e213315f3ac83bf83114b10da870&chksm=eb9c41a7dcebc8b14236068d125469e56408944ef342a63110426e523f1dc71c20967e75068b#rd"},
    {"index":6,"title":"课本和朗读2024秋：P6外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540059&idx=2&sn=96e00be7677b71f20ddd4cc1aeca7cd7&chksm=eb9c41a7dcebc8b163bcb938f0fefe8f7e0c3783531d95d1131fad8f647545fbd624b58179ee#rd"},
    {"index":7,"title":"课本和朗读2024秋：P62Unit 1外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540059&idx=1&sn=0dafd721b74fbeef38888b6900e0d990&chksm=eb9c41a7dcebc8b10937ad46af92ceba6b80d524eda8fa8317bda5ead33d6fe3fc621b9ba58c#rd"},
    {"index":8,"title":"课本和朗读2024秋：P7外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540152&idx=7&sn=9c7eaab1b0c372a494952cf0421faebd&chksm=eb9c4144dcebc852811e1237dd59fa68e2685926d3ecbaa390a38630777e9bcd37f7564dc792#rd"},
    {"index":9,"title":"课本和朗读2024秋：P8外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540152&idx=6&sn=8ae2a0540ae14dd7c9cb2ad94807a79a&chksm=eb9c4144dcebc85233c0e88964d4cdc6ba0bd9c82135afc9bd073589de95a9a2f83aeb2658fb#rd"},
    {"index":10,"title":"课本和朗读2024秋：P9外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540152&idx=5&sn=da748575e95b87938075b888dd8d5637&chksm=eb9c4144dcebc8527bf1fb13bdd02fe04e5f542940fe0906f5607d88ffdaaab1bb05e9e5123f#rd"},
    {"index":11,"title":"课本和朗读2024秋：P10外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540152&idx=4&sn=80e4bf0abf81575e6485254b318f5b09&chksm=eb9c4144dcebc8528fc14966970517fa1e6f755f2ad4cd7802fab797cb183488c18b03fce9b8#rd"},
    {"index":12,"title":"课本和朗读2024秋：P11外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540152&idx=3&sn=b5a07fe12336abc6ec73d84737811f81&chksm=eb9c4144dcebc852ec389cc4f9e66c6f0b87357c6f4ec3b4e3fd03295e7b38b4320ccefd00d9#rd"},
    {"index":13,"title":"课本和朗读2024秋：P12外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540152&idx=2&sn=50a7e8e507ccd46d6e7359923db4a792&chksm=eb9c4144dcebc852dc0546f882b6d2eb7e385a8a8f205b31a186b0f420f8fdcc41846dc6ae3b#rd"},
    {"index":14,"title":"课本和朗读2024秋：P62Unit 2外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540152&idx=1&sn=2cdbdfa4eca8c308a0d2c8f4705a23a9&chksm=eb9c4144dcebc852a31a4fbe3e80d41f37c410f95d19bdd248259678bfe18346a3c6a7ab50eb#rd"},
    {"index":15,"title":"课本和朗读2024秋：P13外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540159&idx=7&sn=bb1e0b7768c64248d87fe1814f4c4cf8&chksm=eb9c4143dcebc855408874b1643c550aed30ffce804ad17ac5650eb63380933722542124df59#rd"},
    {"index":16,"title":"课本和朗读2024秋：P14外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540159&idx=6&sn=04b78f342e1e93fef7d4cecb39f06148&chksm=eb9c4143dcebc855fbed9cfa4afbf00892d499473c7b21b444b45a5736b1a8b5f4efa4f43ff9#rd"},
]

def main():
    """生成用于在浏览器控制台运行的JavaScript代码"""
    print("=" * 60)
    print("音频提取助手")
    print("=" * 60)
    print("\n请按以下步骤操作：")
    print("1. 在Chrome中打开每篇文章")
    print("2. 在控制台运行以下代码提取音频信息：")
    print("\n--- 复制以下代码到浏览器控制台 ---\n")
    print("""
// 提取音频信息
const audios = document.querySelectorAll('mp-common-mpaudio');
const audioData = [];
audios.forEach((audio, idx) => {
    audioData.push({
        index: idx + 1,
        name: audio.getAttribute('name'),
        fileId: audio.getAttribute('voice_encode_fileid'),
        playLength: audio.getAttribute('play_length'),
        author: audio.getAttribute('author'),
        downloadUrl: `https://res.wx.qq.com/voice/getvoice?mediaid=${audio.getAttribute('voice_encode_fileid')}`
    });
});
console.log(JSON.stringify(audioData, null, 2));
    """)
    print("\n--- 代码结束 ---\n")
    print("3. 将结果保存为JSON文件")
    print("4. 运行 download_audios.py 批量下载音频")

    # 保存文章列表
    with open('/Users/liuwenping/Documents/fliggy/study-class/data/english/downloaded/articles.json', 'w', encoding='utf-8') as f:
        json.dump(ARTICLES, f, ensure_ascii=False, indent=2)

    print(f"\n已保存文章列表到 articles.json")

if __name__ == "__main__":
    main()
