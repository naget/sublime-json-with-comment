## json-with-comments (Sublime Text plugin)

**json-with-comments** 是一个 Sublime Text 插件，用来格式化“带注释的 JSON”（支持 `//` 和 `/* */` 注释），避免普通 JSON pretty 插件在遇到注释时报错。

### 功能特性

- **支持注释的 JSON 格式化**：先安全剥离注释，再用 Python 自带的 `json` 模块进行 `pretty` 格式化。
- **支持选择或全文件**：有选区时只格式化选中区域；无选区时格式化整个文件。
- **跨平台快捷键**：
  - macOS: `⌘ + ⌥ + J`
  - Windows/Linux: `Ctrl + Alt + J`
- **命令面板集成**：在 Command Palette 中搜索 “**Pretty JSON with Comments**” 即可执行。

> 注意：目前实现会在格式化时移除注释（即结果中不再包含注释），主要目标是解决“包含注释时无法格式化”的问题。如果你更希望保留注释，可以在后续版本中扩展为保留注释的格式化策略。

### 安装

#### 方式一：通过 Package Control（推荐）

1. 打开 Sublime Text
2. 按 `⌘+Shift+P`（macOS）或 `Ctrl+Shift+P`（Windows/Linux）打开命令面板
3. 输入 `Package Control: Install Package` 并回车
4. 搜索 `json-with-comments` 并安装
5. 安装完成后即可使用

#### 方式二：本地开发版

1. 将本仓库克隆或拷贝到 Sublime Text 的 `Packages` 目录下，例如：

   - macOS: `~/Library/Application Support/Sublime Text/Packages/json-with-comments`
   - Windows: `%APPDATA%/Sublime Text/Packages/json-with-comments`
   - Linux: `~/.config/sublime-text/Packages/json-with-comments`

2. 重新启动 Sublime Text；在 Command Palette 中输入 "**Pretty JSON with Comments**" 看到命令即表示加载成功。

### 使用方法

- **方式一：命令面板**
  1. 打开一个包含注释的 JSON 文件（例如 `.sublime-settings`、`.jsonc` 等）。
  2. 可选：选中需要格式化的部分；不选中则默认对整篇内容进行格式化。
  3. 打开 Command Palette（`⌘+Shift+P` 或 `Ctrl+Shift+P`），输入 “Pretty JSON with Comments”，回车执行。

- **方式二：快捷键**
  - macOS: `⌘ + ⌥ + J`
  - Windows/Linux: `Ctrl + Alt + J`

### 项目结构

本插件遵循 Package Control 标准结构：

- 插件主文件：`json_with_comments.py`（包含 `TextCommand` 实现）
- 命令面板：`json-with-comments.sublime-commands`
- 快捷键映射：`Default (OSX|Windows|Linux).sublime-keymap`
- 版本更新说明：`messages.json` 和 `messages/<version>.txt`
- 文档：`README.md`

### 兼容性

- **Sublime Text 3 / 4**：使用 Python 内置 `json` 和极少量标准库类型，不依赖第三方包，适合作为 Package Control 包分发。


