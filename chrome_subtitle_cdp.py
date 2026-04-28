# chrome_subtitle_cdp.py
import asyncio
import os
import re
import json
import time
import subprocess
from pathlib import Path
from playwright.async_api import async_playwright, Page

# ==================== 配置区域 ====================
# 使用说明：
# 1. 直接修改下方默认值，或
# 2. 设置环境变量（推荐）：PORT、DOWNLOAD_DIR、CHROME_PATH、CHROME_USER_DATA
# 3. Windows PowerShell 设置环境变量示例：
#    $env:DOWNLOAD_DIR = "D:\bilibili_subtitles"
#    $env:CHROME_PATH = "C:\Program Files\Google\Chrome\Application\chrome.exe"

# Chrome 远程调试端口（默认 9222）
CDP_PORT = 9222
DOWNLOAD_DIR = Path(r"E:\projects_2026\BiliScribe\download")
VIDEO_LIST = [
    "BV1884y1k7cv",
    # 添加更多 BV 号
]
SUBTITLE_MODE = "AI"  # "SRT" 或 "AI"
CHROME_EXE_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USER_DATA_DIR = r"C:\Users\21905\AppData\Local\Google\Chrome\User Data"
# =================================================

class BilibiliSubtitleDownloader:
    def __init__(self):
        self.browser = None
        self.context = None
        self.playwright = None
        self.download_dir = DOWNLOAD_DIR
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.cdp_url = f"http://localhost:{CDP_PORT}"
        
    async def connect_to_chrome(self):
        """通过 CDP 连接到已运行的 Chrome 实例"""
        self.playwright = await async_playwright().start()
        
        print(f"正在连接到 Chrome（{self.cdp_url}）...")
        print("提示：请确保 Chrome 已启动并开启了远程调试端口")
        
        try:
            # 通过 CDP 连接到已有 Chrome
            self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)
            
            # 获取现有上下文（通常是 Chrome 的默认上下文）
            if self.browser.contexts:
                self.context = self.browser.contexts[0]
                print(f"已连接到 Chrome（当前 {len(self.context.pages)} 个标签页）")
            else:
                # 如果没有现有上下文，创建一个新的（通常不会走到这里）
                self.context = await self.browser.new_context(
                    accept_downloads=True,
                    downloads_path=str(self.download_dir),
                )
                print("已创建新上下文")
            
            print("连接成功！现有插件和登录状态均已保留")
            
        except Exception as e:
            print(f"\n连接失败: {e}")
            print("\n请按以下步骤操作：")
            print("1. 关闭所有 Chrome 窗口")
            print(f"2. 在 PowerShell 中运行：")
            print(f'   & "{CHROME_EXE_PATH}" --remote-debugging-port={CDP_PORT} --user-data-dir="{USER_DATA_DIR}"')
            print("3. 等待 Chrome 启动后，重新运行此脚本")
            raise

    async def get_video_info(self, page: Page, bv_id: str) -> dict:
        """获取视频信息"""
        try:
            info = await page.evaluate("""() => {
                const state = window.__INITIAL_STATE__ || {};
                const videoData = state.videoData || {};
                return {
                    title: videoData.title || document.title,
                    bvid: videoData.bvid || '',
                    cid: videoData.cid || (window.__playinfo__?.data?.video?.cid) || ''
                };
            }""")
            
            title = info.get('title', bv_id)
            title = re.sub(r'[\\/:*?"<>|]', '', title).strip()
            
            return {
                'title': title[:80],
                'bvid': info.get('bvid', bv_id),
                'cid': info.get('cid', '')
            }
        except Exception as e:
            print(f"获取视频信息失败: {e}")
            return {'title': bv_id, 'bvid': bv_id, 'cid': ''}

    async def get_video_pages(self, page: Page, bv_id: str) -> list:
        """通过API获取视频所有分P信息"""
        try:
            api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bv_id}"
            resp = await page.evaluate(f"""() => fetch("{api_url}").then(r=>r.json())""")
            
            if resp.get('code') == 0:
                data = resp['data']
                pages = data.get('pages', [])
                if not pages:
                    # 单P视频，构造一个默认的P1信息
                    return [{
                        'cid': data.get('cid', ''),
                        'page': 1,
                        'part': 'P1'
                    }]
                return pages
            else:
                print(f"  获取分P信息失败: {resp.get('message', '未知错误')}")
                return []
        except Exception as e:
            print(f"  获取分P信息异常: {e}")
            return []

    async def download_via_api(self, page: Page, video_info: dict, cid: str, page_num: int, part_title: str) -> bool:
        """通过 B 站 API 下载字幕（支持指定CID和分P信息）"""
        bv_id = video_info['bvid']
        
        if not cid:
            print("  无效CID")
            return False
            
        try:
            # 获取字幕列表
            sub_url = f"https://api.bilibili.com/x/player/wbi/v2?cid={cid}&bvid={bv_id}"
            sub_data = await page.evaluate(f"""() => fetch("{sub_url}", {{
                credentials: 'include',
                headers: {{ 'Referer': 'https://www.bilibili.com' }}
            }}).then(r=>r.json())""")
            
            subtitles = sub_data.get('data', {}).get('subtitle', {})
            sub_list = subtitles.get('subtitles', []) or subtitles.get('ai_subtitles', [])
            
            if not sub_list:
                return False
            
            sub_type = "AI" if 'ai_subtitles' in str(sub_data) else "普通"
            print(f"    发现 {sub_type} 字幕")
            
            # 下载字幕内容
            sub_url = sub_list[0]['subtitle_url']
            if not sub_url.startswith('http'):
                sub_url = 'https:' + sub_url
            
            sub_json = await page.evaluate(f"""() => fetch("{sub_url}").then(r=>r.json())""")
            
            # 转换为 SRT
            srt_content = self.json_to_srt(sub_json)
            if not srt_content:
                return False
            
            # 构造文件名：标题_PXX_分P标题_BV号.srt
            safe_part = re.sub(r'[\\/:*?"<>|]', '', part_title).strip()[:30]
            if safe_part:
                filename = f"{video_info['title']}_P{page_num:02d}_{safe_part}_{bv_id}.srt"
            else:
                filename = f"{video_info['title']}_P{page_num:02d}_{bv_id}.srt"
            
            filepath = self.download_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(srt_content)
                
            print(f"    已保存: {filename}")
            return True
            
        except Exception as e:
            print(f"    下载失败: {e}")
            return False

    def json_to_srt(self, data: dict) -> str:
        """JSON 字幕转 SRT 格式"""
        if not data or 'body' not in data:
            return ""
        
        lines = []
        for i, item in enumerate(data['body'], 1):
            start = item['from']
            end = item['to']
            content = item['content']
            
            def fmt(t):
                h = int(t // 3600)
                m = int((t % 3600) // 60)
                s = int(t % 60)
                ms = int((t % 1) * 1000)
                return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
            
            lines.extend([str(i), f"{fmt(start)} --> {fmt(end)}", content, ""])
        
        return "\n".join(lines)

    async def process_video(self, bv_id: str) -> int:
        """处理视频的所有分P，返回成功下载的字幕数"""
        base_url = f"https://www.bilibili.com/video/{bv_id}"
        page = None
        success_count = 0
        
        try:
            # 创建新标签页
            page = await self.context.new_page()
            
            print(f"\n处理: {bv_id}")
            
            # 反爬伪装
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """)
            
            # 先访问视频主页获取基本信息和分P列表
            # 增加超时到60秒，并先用domcontentloaded避免资源加载卡住
            await page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
            
            # 等待关键元素出现（比networkidle更可靠）
            try:
                # 等待视频标题或播放器出现，最多等10秒
                await page.wait_for_selector("h1.video-title, .bpx-player-container, #bilibili-player", timeout=10000)
            except:
                print("  警告：等待页面元素超时，继续执行...")
            
            # 稍微等待确保JS执行完成
            await asyncio.sleep(3)
            
            # 获取视频基本信息
            video_info = await self.get_video_info(page, bv_id)
            print(f"  标题: {video_info['title'][:40]}...")
            
            # 获取所有分P信息
            pages_info = await self.get_video_pages(page, bv_id)
            if not pages_info:
                print("  未能获取分P信息，尝试仅下载P1")
                pages_info = [{'cid': video_info.get('cid', ''), 'page': 1, 'part': 'P1'}]
            
            total_pages = len(pages_info)
            print(f"  共 {total_pages} 个分P")
            
            # 遍历处理每一P
            for idx, page_info in enumerate(pages_info, 1):
                page_num = page_info['page']
                cid = str(page_info['cid'])
                part_title = page_info.get('part', f'P{page_num}')
                
                print(f"\n  [{idx}/{total_pages}] 处理第 {page_num} P: {part_title[:30]}")
                
                # 如果不是第一P，导航到对应分P
                if page_num > 1:
                    p_url = f"{base_url}?p={page_num}"
                    try:
                        await page.goto(p_url, wait_until="domcontentloaded", timeout=60000)
                        await asyncio.sleep(2)  # 简单等待替代networkidle
                    except Exception as e:
                        print(f"    页面加载失败: {e}")
                        continue
                
                # 下载当前P的字幕
                if await self.download_via_api(page, video_info, cid, page_num, part_title):
                    success_count += 1
                    print(f"    第 {page_num} P 完成")
                else:
                    print(f"    第 {page_num} P 无字幕或下载失败")
                
                # 防封间隔：每P之间等待2-4秒
                if idx < total_pages:
                    await asyncio.sleep(3)
            
            return success_count
            
        except Exception as e:
            print(f"  处理过程错误: {e}")
            import traceback
            traceback.print_exc()  # 打印详细错误栈
            return success_count
        finally:
            if page:
                await page.close()
            await asyncio.sleep(1)

    async def run(self):
        """主运行流程"""
        await self.connect_to_chrome()
        
        try:
            total_videos = len(VIDEO_LIST)
            total_subtitles = 0
            
            for idx, bv_id in enumerate(VIDEO_LIST, 1):
                print(f"[{idx}/{total_videos}] ", end="")
                count = await self.process_video(bv_id)
                total_subtitles += count
            
            # 统计结果
            print(f"\n{'='*50}")
            print(f"处理完成: {total_videos} 个视频")
            print(f"成功下载字幕: {total_subtitles} 个分P")
            print(f"保存位置: {self.download_dir}")
            print(f"{'='*50}")
            
        finally:
            # 关闭连接（不关闭 Chrome）
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            print("已断开连接（Chrome 仍在运行）")

def launch_chrome_helper():
    """辅助启动 Chrome（如果用户需要）"""
    print("是否现在启动 Chrome？")
    print("1. 是（自动启动带调试端口的 Chrome）")
    print("2. 否（我已手动启动 Chrome）")
    choice = input("选择 (1/2): ").strip()
    
    if choice == "1":
        # 先关闭现有 Chrome
        print("正在关闭现有 Chrome 进程...")
        subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
        time.sleep(2)
        
        # 启动 Chrome
        cmd = [
            CHROME_EXE_PATH,
            f"--remote-debugging-port={CDP_PORT}",
            f"--user-data-dir={USER_DATA_DIR}",
            "--no-first-run",
            "--disable-blink-features=AutomationControlled"
        ]
        
        print(f"正在启动 Chrome（端口 {CDP_PORT}）...")
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        print("Chrome 已启动，请等待 3 秒确保初始化完成...")
        time.sleep(3)

if __name__ == "__main__":
    # 检查是否需要辅助启动
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--launch":
        launch_chrome_helper()
    
    # 运行下载器
    downloader = BilibiliSubtitleDownloader()
    try:
        asyncio.run(downloader.run())
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n运行错误: {e}")