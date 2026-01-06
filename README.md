## json-with-comments (Sublime Text plugin)

Language / 语言: **English** | [中文](#zh)

<a id="en"></a>
## English

**json-with-comments** is a Sublime Text plugin that formats **JSON with comments** (supports `//` comments). It helps avoid errors from regular JSON pretty formatters when comments are present.

### Features

- **Format commented JSON safely**: strips comments first, then pretty-prints via Python’s built-in `json` module.
- **Selection or whole file**: formats the selection if there is one; otherwise formats the entire file.
- **Cross-platform key bindings**:
  - macOS: `⌘ + ⌥ + J`
  - Windows/Linux: `Ctrl + Alt + J`
- **Command Palette integration**: search for “**Pretty JSON with Comments**”.

> Note: the current implementation removes comments during formatting (comments will not be preserved in the output). The main goal is to make “commented JSON” formatable. If you prefer to preserve comments, this can be extended in a future version.

### Installation

#### Option 1: Package Control (recommended)

1. Open Sublime Text
2. Open the Command Palette: `⌘+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
3. Run `Package Control: Install Package`
4. Search for `json-with-comments` and install
5. Done

#### Option 2: Local/development install

1. Clone/copy this repository into Sublime Text’s `Packages` directory, e.g.:

   - macOS: `~/Library/Application Support/Sublime Text/Packages/json-with-comments`
   - Windows: `%APPDATA%/Sublime Text/Packages/json-with-comments`
   - Linux: `~/.config/sublime-text/Packages/json-with-comments`

2. Restart Sublime Text. If you can find “**Pretty JSON with Comments**” in the Command Palette, it’s loaded successfully.

### Usage

- **Command Palette**
  1. Open a commented JSON file (e.g. `.sublime-settings`, `.jsonc`, etc.).
  2. Optional: select the part you want to format. If nothing is selected, the whole file will be formatted.
  3. Open the Command Palette (`⌘+Shift+P` / `Ctrl+Shift+P`), search “Pretty JSON with Comments”, and run it.

- **Key binding**
  - macOS: `⌘ + ⌥ + J`
  - Windows/Linux: `Ctrl + Alt + J`

### Project structure

This package follows the Package Control convention:

- Main plugin: `json_with_comments.py` (contains the `TextCommand` implementation)
- Command Palette: `json-with-comments.sublime-commands`
- Key bindings: `Default (OSX|Windows|Linux).sublime-keymap`
- Changelog: `messages.json` and `messages/<version>.txt`
- Docs: `README.md`

### Compatibility

- **Sublime Text 3 / 4**: uses Python’s built-in `json` and minimal standard library utilities, with no third-party dependencies—suitable for Package Control distribution.

---

Language / 语言: [English](#en) | **中文**

<a id="zh"></a>
## 中文

**json-with-comments** 是一个 Sublime Text 插件，用来格式化“带注释的 JSON”（支持 `//` 注释），避免普通 JSON pretty 插件在遇到注释时报错。

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


