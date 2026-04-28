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
git clone <repository-url>
cd BiliScribe
pip install playwright
playwright install chromium
```

## 使用指南

### 1. 配置

**编辑 `chrome_subtitle_cdp.py` 文件顶部**的 `用户配置区域`，修改以下必需项：

- `CHROME_EXE_PATH`：Chrome 浏览器路径
- `USER_DATA_DIR`：Chrome 用户数据目录
- `DOWNLOAD_DIR`：字幕保存目录
- `VIDEO_LIST`：待下载的视频 BV 号列表

脚本包含配置验证，未修改占位符会提示错误并退出。

### 2. 启动 Chrome 调试模式

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir="C:\chrome_debug_temp"
```

注意：`--user-data-dir` 建议指向临时目录，避免与日常使用冲突；如需登录态，请先在该 Chrome 中登录 Bilibili。

### 3. 运行下载

```bash
python chrome_subtitle_cdp.py
```

脚本自动连接 Chrome、遍历分 P、下载字幕并保存为 `标题_PXX_分P标题_BV号.srt`。

### 4. 批量重命名（可选）

编辑 `rename.py` 中的 `SUBTITLE_DIR` 为实际字幕目录，执行：

```bash
python rename.py
```

重命名规则：`【课程名】完整标题_P01_第一讲_BVxxxxx.srt` → `P01_第一讲.srt`

## 项目结构

```
BiliScribe/
├── chrome_subtitle_cdp.py    # 主下载脚本（CDP 连接、API 调用、SRT 转换）
├── rename.py                 # 批量重命名工具
├── download/                 # 默认字幕输出目录
└── README.md                 # 本文件
```

## 配置参数

| 参数              | 必填 | 说明                    | 示例                                                       |
| :---------------- | :--- | :---------------------- | :--------------------------------------------------------- |
| `CHROME_EXE_PATH` | 是   | Chrome 可执行文件路径   | `r"C:\Program Files\Google\Chrome\Application\chrome.exe"` |
| `DOWNLOAD_DIR`    | 是   | 字幕保存路径            | `r"D:\subtitles"` 或 `"./download"`                        |
| `VIDEO_LIST`      | 是   | 视频 BV 号列表          | `["BV1xx411c7mD"]`                                         |
| `USER_DATA_DIR`   | 建议 | Chrome 临时用户数据目录 | `r"C:\chrome_temp_data"`                                   |
| `CDP_PORT`        | 否   | 远程调试端口            | `9222`                                                     |
| `SUBTITLE_MODE`   | 否   | 字幕类型偏好            | `"AI"` 或 `"SRT"`                                          |

## 注意事项

1. **配置检查**：首次运行会验证 `CHROME_EXE_PATH`、`DOWNLOAD_DIR` 和 `VIDEO_LIST` 是否已修改，未修改会报错退出
2. **启动顺序**：必须先启动 Chrome 调试模式，再运行脚本
3. **登录状态**：部分字幕需登录获取，请在调试 Chrome 中提前登录 Bilibili
4. **频率限制**：内置 2-4 秒随机延迟，频繁下载可能导致 IP 被限，建议间隔使用

## 免责声明

本工具仅供学习研究使用，请勿用于侵犯版权或违反 Bilibili 用户协议的场景。下载的字幕文件版权归原作者或上传者所有。
