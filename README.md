# BiliScribe - Bilibili 字幕批量下载工具

基于 Chrome DevTools Protocol (CDP) 的 Bilibili 视频字幕下载器，支持多 P 视频自动遍历、AI 字幕识别与 SRT 格式转换。

## 功能特性

- 多 P 视频自动处理：自动识别并下载合集中所有分 P 的字幕
- 保留登录状态：复用已登录的 Chrome 用户数据，支持下载需登录观看的视频字幕
- 智能防检测：反爬虫伪装，降低被风控概率
- 批量重命名：提供配套脚本清理冗长文件名，提取规范命名（PXX_标题）
- 格式转换：自动将 B 站 JSON 字幕转为标准 SRT 格式

## 原理说明

1. **CDP 远程调试**：通过 Chrome 的 `--remote-debugging-port` 参数启动浏览器，使用 Playwright 连接现有 Chrome 实例而非新建浏览器，保留用户登录态和插件
2. **API 拦截**：利用页面注入的 JavaScript 调用 Bilibili 内部 API（`x/player/wbi/v2`）获取字幕元数据
3. **分 P 遍历**：通过 `x/web-interface/view` API 获取视频分 P 列表（CID），遍历每个分 P 独立请求字幕
4. **格式转换**：将 B 站的时间戳 JSON 数据转换为 SRT 标准格式

## 环境要求

- Python 3.8+
- Windows / Linux / macOS（脚本主要测试于 Windows）
- 已安装 Google Chrome 浏览器
- 依赖库：`playwright`

## 安装

```bash
# 克隆仓库
git clone <repository-url>
cd BiliScribe

# 安装依赖
pip install playwright
playwright install chromium
```

## 使用指南

### 1. 启动 Chrome 调试模式

在 PowerShell（管理员模式）或终端中运行：

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir="C:\chrome_debug_temp"
```

参数说明：

- `--remote-debugging-port=9222`：开启远程调试端口（脚本默认连接 9222 端口）
- `--user-data-dir`：**建议指定临时目录**，避免与日常使用的 Chrome 配置文件冲突

### 2. 配置下载脚本

编辑 `chrome_subtitle_cdp.py` 顶部的配置区域：

```python
# ==================== 配置区域 ====================
CDP_PORT = 9222  # 与 Chrome 启动参数保持一致
DOWNLOAD_DIR = Path("./download")  # 字幕保存目录（相对路径或绝对路径）
VIDEO_LIST = [
    "BV1884y1k7cv",  # 替换为目标 BV 号
    # 添加更多 BV 号
]
# =================================================
```

### 3. 运行字幕下载

```bash
python chrome_subtitle_cdp.py
```

脚本将自动：

- 连接到已启动的 Chrome 实例
- 遍历视频所有分 P
- 下载字幕并保存为 `标题_PXX_分P标题_BV号.srt`

### 4. 批量重命名（可选）

下载后的文件名可能较长，运行重命名脚本提取简洁格式：

编辑 `rename.py` 配置字幕所在目录：

```python
SUBTITLE_DIR = Path("./download/【课程名】")  # 修改为实际子目录
```

执行重命名：

```bash
python rename.py
```

重命名规则：

- 输入：`【课程名】完整标题_P01_第一讲_BVxxxxx.srt`
- 输出：`P01_第一讲.srt`

## 项目结构

```
BiliScribe/
├── chrome_subtitle_cdp.py    # 主下载脚本（CDP 连接、API 调用、SRT 转换）
├── rename.py                 # 批量重命名工具（文件名清理）
├── download/                 # 默认字幕输出目录（自动生成）
└── README.md                 # 本文件
```

## 配置参数详解

### chrome_subtitle_cdp.py


| 参数           | 说明                | 示例               |
| -------------- | ------------------- | ------------------ |
| `CDP_PORT`     | Chrome 远程调试端口 | `9222`             |
| `DOWNLOAD_DIR` | 字幕文件保存路径    | `./download`       |
| `VIDEO_LIST`   | 待下载 BV 号列表    | `["BV1xx411c7mD"]` |

### rename.py


| 参数           | 说明               | 示例                |
| -------------- | ------------------ | ------------------- |
| `SUBTITLE_DIR` | 需处理的字幕文件夹 | `./download/课程名` |

## 注意事项

1. **Chrome 启动**：确保先启动 Chrome 调试模式再运行脚本，否则会提示连接失败
2. **用户数据目录**：建议 `--user-data-dir` 指向临时目录，避免污染日常浏览器数据
3. **网络环境**：部分视频字幕需要登录后才能获取，请先在 Chrome 中登录 Bilibili 账号
4. **频率限制**：脚本已内置 2-4 秒随机延迟，频繁下载可能导致 IP 被临时限制，建议间隔使用
5. **路径问题**：开源仓库版本使用相对路径 `./download`，使用前请根据实际环境调整

## 免责声明

本工具仅供学习研究使用，请勿用于侵犯版权或违反 Bilibili 用户协议的场景。下载的字幕文件版权归原作者或上传者所有。
