"""
微信公众号专辑资源下载工具 - 智能版

从微信公众号专辑页面获取有价值的资源（试卷、课本、练习册等），
过滤掉图标等无用图片，保存到 data/english 中。

用法:
    python -m app.scripts.fetch_wechat_resources [album_url]
"""

import os
import re
import json
import asyncio
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urlparse

from playwright.async_api import async_playwright, Page, Browser

from app.config import DATA_DIR


@dataclass
class MediaResource:
    """媒体资源"""
    url: str
    type: str  # "image" or "audio"
    filename: str
    source_url: str
    title: str = ""
    size: int = 0  # 文件大小


class WeChatAlbumCrawler:
    """微信公众号专辑爬虫"""

    # 有价值内容的关键词
    VALUABLE_KEYWORDS = [
        "试卷", "测试", "练习", "课本", "教材", "教案", "课件",
        "单词", "默写", "描红", "听力", "音频", "视频", "连播",
        "培优", "金牌", "海定", "AB卷", "期末", "期中", "单元"
    ]

    # 排除的关键词（广告、二维码等）
    EXCLUDE_KEYWORDS = [
        "头像", "二维码", "关注", "公众号", "分享", "点赞",
        "在看", "广告", "推广", "赞赏", "打赏"
    ]

    def __init__(self, output_dir: Optional[Path] = None, auto_mode: bool = True):
        self.output_dir = output_dir or (DATA_DIR / "english")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.auto_mode = auto_mode  # 自动模式，无需人工确认

        # 创建子目录
        self.images_dir = self.output_dir / "images"
        self.audio_dir = self.output_dir / "audio"
        self.meta_dir = self.output_dir / "meta"

        for d in [self.images_dir, self.audio_dir, self.meta_dir]:
            d.mkdir(exist_ok=True)

        self.browser: Optional[Browser] = None
        self.stats = {
            "articles_checked": 0,
            "articles_valuable": 0,
            "images_found": 0,
            "images_downloaded": 0,
            "audios_found": 0,
            "audios_downloaded": 0,
            "skipped": []
        }

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        await self.playwright.stop()

    def is_valuable_article(self, title: str) -> bool:
        """判断文章是否有价值"""
        title_lower = title.lower()

        # 检查排除关键词
        for kw in self.EXCLUDE_KEYWORDS:
            if kw in title_lower:
                return False

        # 检查有价值关键词
        for kw in self.VALUABLE_KEYWORDS:
            if kw in title_lower:
                return True

        return False

    def is_valuable_image(self, img_url: str, width: int = 0, height: int = 0) -> bool:
        """判断图片是否有价值（排除小图标）"""
        # 排除已知的小图标/头像
        if any(x in img_url.lower() for x in [
            "mmhead", "emoji", "icon", "avatar", "logo",
            "qr_code", "qrcode", "follow", "like", "share"
        ]):
            return False

        # 从URL参数判断尺寸（微信公众号图片）
        # wx_fmt=png&tp=webp&wxfrom=5&wx_lazy=1&wx_co=1
        # 如果URL中有尺寸参数
        if "wx_lazy" in img_url or "mmbiz.qpic.cn" in img_url:
            # 检查是否是缩略图
            if img_url.count("/") > 5:
                return True

        return True

    async def fetch_album(self, album_url: str) -> List[Tuple[str, str]]:
        """
        获取专辑中的所有文章链接和标题

        Returns:
            [(url, title), ...]
        """
        print(f"正在获取专辑页面: {album_url}")

        page = await self.browser.new_page()
        articles = []

        try:
            await page.set_viewport_size({"width": 375, "height": 812})
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 "
                              "(KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.38(0x1800262a) "
                              "NetType/WIFI Language/zh_CN"
            })

            await page.goto(album_url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(2)

            html = await page.content()

            # 从 data-link 提取
            data_links = re.findall(r'data-link="([^"]+)"[^>]*data-title="([^"]*)"', html)

            for link, title in data_links:
                link = link.replace("&amp;", "&")
                if link.startswith("http"):
                    articles.append((link, title))

            # 如果没有 data-title，尝试只提取链接
            if not articles:
                links = re.findall(r'data-link="([^"]+)"', html)
                for link in links:
                    link = link.replace("&amp;", "&")
                    if link.startswith("http"):
                        articles.append((link, ""))

            # 去重
            seen = set()
            unique = []
            for url, title in articles:
                if url not in seen:
                    seen.add(url)
                    unique.append((url, title))

            print(f"  ✓ 找到 {len(unique)} 篇文章\n")
            return unique

        finally:
            await page.close()

    async def fetch_article_resources(self, url: str, expected_title: str = "") -> Optional[Dict]:
        """
        获取单篇文章的资源

        Returns:
            {
                "url": str,
                "title": str,
                "images": [(url, width, height), ...],
                "audios": [url, ...]
            }
        """
        page = await self.browser.new_page()

        try:
            await page.set_viewport_size({"width": 375, "height": 812})
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 "
                              "(KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.38(0x1800262a) "
                              "NetType/WIFI Language/zh_CN"
            })

            await page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(2)

            html = await page.content()
            title = await page.title()

            # 清理标题
            title = re.sub(r'[\s_]*$', '', title)
            if expected_title and not title:
                title = expected_title

            result = {
                "url": url,
                "title": title,
                "images": [],
                "audios": []
            }

            # 检查文章是否有价值
            if not self.is_valuable_article(title):
                print(f"    → 跳过（非目标内容）")
                return None

            # 提取图片 - 获取尺寸信息
            img_elements = await page.query_selector_all('img[data-src], img[src*="mmbiz.qpic.cn"]')

            for img in img_elements:
                try:
                    src = await img.get_attribute("data-src") or await img.get_attribute("src")
                    if not src:
                        continue

                    # 获取图片尺寸
                    width = await img.evaluate("el => el.naturalWidth || el.width || 0")
                    height = await img.evaluate("el => el.naturalHeight || el.height || 0")

                    # 排除小图标（小于 100x100）
                    if width > 0 and height > 0 and (width < 100 or height < 100):
                        continue

                    # 进一步过滤
                    if not self.is_valuable_image(src, width, height):
                        continue

                    result["images"].append((src, width, height))

                except Exception:
                    continue

            # 提取音频
            # 方法1: 查找语音消息
            voice_elements = await page.query_selector_all('[data-voice-id], [voice_encode_fileid]')
            for voice in voice_elements:
                voice_id = await voice.get_attribute("data-voice-id") or await voice.get_attribute("voice_encode_fileid")
                if voice_id:
                    audio_url = f"https://res.wx.qq.com/voice/getvoice?mediaid={voice_id}"
                    result["audios"].append(audio_url)

            # 方法2: 从HTML中查找音频链接
            audio_patterns = [
                r'voice_encode_fileid["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'https?://res\.wx\.qq\.com/voice/getvoice[^\s"\']+',
                r'https?://[^\s"\']+\.mp3',
            ]

            for pattern in audio_patterns:
                matches = re.findall(pattern, html)
                for match in matches:
                    if match not in result["audios"]:
                        result["audios"].append(match)

            # 去重
            result["images"] = list(set(result["images"]))
            result["audios"] = list(set(result["audios"]))

            return result

        except Exception as e:
            print(f"    ✗ 获取失败: {e}")
            return None

        finally:
            await page.close()

    async def download_file(self, url: str, output_path: Path, resource_type: str) -> bool:
        """下载单个文件"""
        if output_path.exists() and output_path.stat().st_size > 1024:
            return True

        page = await self.browser.new_page()
        try:
            response = await page.goto(url, wait_until="networkidle", timeout=30000)
            if response:
                buffer = await response.body()
                if len(buffer) > 1024:  # 至少1KB
                    with open(output_path, 'wb') as f:
                        f.write(buffer)
                    size = len(buffer)
                    size_str = self._format_size(size)
                    print(f"      ✓ {resource_type}: {output_path.name} ({size_str})")
                    return True
        except Exception as e:
            print(f"      ✗ 下载失败: {e}")
        finally:
            await page.close()

        return False

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名"""
        filename = re.sub(r'[\\/*?:"<>|]', '_', filename)
        filename = filename.strip('. ')
        if len(filename) > 60:
            filename = filename[:60]
        return filename

    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    async def process_album(self, album_url: str) -> Dict:
        """处理整个专辑"""
        print("=" * 70)
        print("微信公众号专辑资源下载工具（智能版）")
        print("=" * 70)
        print()

        # 获取文章列表
        articles = await self.fetch_album(album_url)

        if not articles:
            print("未找到文章")
            return self.stats

        all_resources: List[MediaResource] = []

        # 逐篇处理
        for idx, (url, preview_title) in enumerate(articles, 1):
            print(f"[{idx}/{len(articles)}] 正在处理...")

            # 获取文章资源
            article = await self.fetch_article_resources(url, preview_title)
            self.stats["articles_checked"] += 1

            if not article:
                continue

            self.stats["articles_valuable"] += 1
            title = article["title"]
            safe_title = self._sanitize_filename(title)

            img_count = len(article.get("images", []))
            audio_count = len(article.get("audios", []))

            print(f"    标题: {title[:50]}...")
            print(f"    发现: {img_count} 张图片, {audio_count} 个音频")

            if img_count == 0 and audio_count == 0:
                print(f"    → 无有效资源，跳过\n")
                continue

            # 下载图片
            downloaded_images = []
            for i, (img_url, width, height) in enumerate(article["images"]):
                ext = ".jpg"
                lower_url = img_url.lower()
                if ".png" in lower_url:
                    ext = ".png"
                elif ".gif" in lower_url:
                    ext = ".gif"

                filename = f"{safe_title}_{i+1:02d}{ext}"
                output_path = self.images_dir / filename

                success = await self.download_file(img_url, output_path, "图片")
                if success:
                    downloaded_images.append(MediaResource(
                        url=img_url,
                        type="image",
                        filename=filename,
                        source_url=url,
                        title=title
                    ))
                    self.stats["images_downloaded"] += 1

            self.stats["images_found"] += img_count

            # 下载音频
            downloaded_audios = []
            for i, audio_url in enumerate(article["audios"]):
                filename = f"{safe_title}_audio_{i+1:02d}.mp3"
                output_path = self.audio_dir / filename

                success = await self.download_file(audio_url, output_path, "音频")
                if success:
                    downloaded_audios.append(MediaResource(
                        url=audio_url,
                        type="audio",
                        filename=filename,
                        source_url=url,
                        title=title
                    ))
                    self.stats["audios_downloaded"] += 1

            self.stats["audios_found"] += audio_count

            all_resources.extend(downloaded_images)
            all_resources.extend(downloaded_audios)

            print(f"    ✓ 完成: {len(downloaded_images)} 图, {len(downloaded_audios)} 音\n")

            # 间隔一下，避免请求过快
            await asyncio.sleep(1)

        # 保存清单
        if all_resources:
            self._save_manifest(all_resources)

        return self.stats

    def _save_manifest(self, resources: List[MediaResource]):
        """保存资源清单"""
        manifest_path = self.meta_dir / "manifest.json"
        data = [asdict(r) for r in resources]

        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"资源清单已保存: {manifest_path}")


async def main():
    parser = argparse.ArgumentParser(
        description="下载微信公众号专辑中的有价值资源"
    )
    parser.add_argument(
        "url",
        nargs="?",
        default="https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzI4MjE1MjMzOQ==&action=getalbum&album_id=3816728266787913728&scene=21#wechat_redirect",
        help="微信专辑URL"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="输出目录 (默认: data/english)"
    )

    args = parser.parse_args()

    async with WeChatAlbumCrawler(output_dir=args.output) as crawler:
        stats = await crawler.process_album(args.url)

    print()
    print("=" * 70)
    print("下载完成")
    print("=" * 70)
    print(f"检查文章: {stats['articles_checked']}")
    print(f"有价值文章: {stats['articles_valuable']}")
    print(f"图片: {stats['images_downloaded']}/{stats['images_found']}")
    print(f"音频: {stats['audios_downloaded']}/{stats['audios_found']}")

    return 0


if __name__ == "__main__":
    asyncio.run(main())
