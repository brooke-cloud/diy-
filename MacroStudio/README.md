# 6-Key Macro Studio

一套面向 RP2040-Zero 六键宏键盘的配置工具。通过 Windows 图形界面，可以为六个实体按键设置单键、组合键或文本内容；配置保存后，设备会自动载入，无需按 RESET 或重新插拔 USB。

## 功能特点

- 支持 6 个独立机械按键。
- 支持单键，例如 `F5`、`ESC`、`ENTER`。
- 支持组合键，例如 `CTRL+C`、`ALT+TAB`、`WIN+SHIFT+S`。
- 支持英文、数字和常见 ASCII 符号组成的文本宏。
- 点击“录制”后，可直接按实体键盘录入单键或组合键。
- 编辑界面按照 PCB 的真实按键位置排列。
- 保存配置后约 0.5 秒自动生效，无需重启设备。
- 配置读取失败时保留上一份有效配置，避免按键立即失效。

## PCB 按键布局

配置界面与 PCB 的位置一致：

```text
┌─────────┬─────────┬─────────┐
│   SW2   │   SW3   │   SW1   │
│   GP3   │   GP8   │   GP2   │
├─────────┼─────────┼─────────┤
│   SW6   │   SW5   │   SW4   │
│   GP7   │   GP6   │   GP5   │
└─────────┴─────────┴─────────┘
```

## 项目文件

| 文件 | 用途 |
| --- | --- |
| `code.py` | 运行在 RP2040-Zero/CircuitPython 上的设备程序 |
| `macro_studio.py` | 运行在 Windows 电脑上的图形化配置工具 |
| `config.json` | 六个按键的当前配置 |

## 硬件与软件要求

### 硬件

- RP2040-Zero 或兼容的 CircuitPython 开发板
- 6 个按键
- USB 数据线

### 设备端软件

- CircuitPython
- Adafruit HID 库
- `adafruit_hid` 文件夹应位于设备的 `/lib` 目录中

### 电脑端软件

- Windows 10 或 Windows 11
- Python 3.9 或更高版本
- Python 自带的 Tkinter（标准 Windows Python 安装通常已经包含）

## GPIO 接线

| 按键 | GPIO |
| --- | --- |
| SW1 | GP2 |
| SW2 | GP3 |
| SW3 | GP8 |
| SW4 | GP5 |
| SW5 | GP6 |
| SW6 | GP7 |

程序使用内部上拉输入。按键按下时，应将对应 GPIO 与 GND 接通。

## 安装到设备

1. 为 RP2040-Zero 安装 CircuitPython。
2. 使用 USB 将设备连接到电脑。
3. 打开电脑中出现的 `CIRCUITPY` 磁盘。
4. 将 `code.py` 和 `config.json` 复制到 `CIRCUITPY` 根目录。
5. 将 Adafruit CircuitPython HID 库中的 `adafruit_hid` 文件夹复制到 `CIRCUITPY/lib/`。
6. 等待设备自动重载。

设备启动后会读取 `config.json`。如果配置不存在或格式无效，将使用 `code.py` 中的默认配置。

## 启动配置工具

在项目文件夹中打开 PowerShell，然后运行：

```powershell
python .\macro_studio.py
```

也可以直接双击 `macro_studio.py`。如果 `.py` 文件没有关联 Python，推荐使用上面的 PowerShell 命令。

## 使用方法

1. 使用 USB 连接宏键盘。
2. 启动 `macro_studio.py`。
3. 软件会尝试自动查找包含 `code.py` 和 `lib/adafruit_hid` 的设备盘。
4. 如果没有自动识别，点击“选择目录”，选择 `CIRCUITPY` 根目录。
5. 为每个按键选择“单键”“组合键”或“文本”。
6. 设置单键或组合键时，点击“录制”，然后按下电脑键盘上的目标按键。
7. 设置文本时，直接在内容框中输入文本。
8. 点击“保存到设备”。

保存成功后，设备会在约 0.5 秒内读取新配置，不需要按 RESET 或重新插拔 USB。

## 配置文件格式

`config.json` 必须包含 6 个按键动作，顺序对应 `SW1` 到 `SW6`：

```json
{
  "version": 1,
  "keys": [
    {"type": "hotkey", "value": "CTRL+C"},
    {"type": "hotkey", "value": "CTRL+V"},
    {"type": "hotkey", "value": "CTRL+Z"},
    {"type": "hotkey", "value": "ALT+TAB"},
    {"type": "hotkey", "value": "WIN+SHIFT+S"},
    {"type": "key", "value": "F5"}
  ]
}
```

动作类型：

- `key`：单键
- `hotkey`：组合键，使用 `+` 连接
- `text`：文本宏

## 默认按键

| 按键 | 默认动作 |
| --- | --- |
| SW1 | `CTRL+C` |
| SW2 | `CTRL+V` |
| SW3 | `CTRL+Z` |
| SW4 | `ALT+TAB` |
| SW5 | `WIN+SHIFT+S` |
| SW6 | `F5` |

## 注意事项

- 文本宏使用美式键盘布局发送，适合英文、数字和常见 ASCII 符号。
- 文本内容最多 500 个字符。
- 保存配置时不要断开 USB。
- `config.json` 必须保留 6 个按键动作。
- 不要把电脑上的 `.git`、`__pycache__` 或整个 GitHub 项目文件夹复制到 CIRCUITPY 设备盘。

## 常见问题

### 软件没有找到设备

点击“选择目录”，手动选择包含 `code.py` 的 `CIRCUITPY` 根目录，并确认 `/lib/adafruit_hid` 已安装。

### 保存后按键没有变化

先等待 1 秒后再次测试。如果仍未生效，请检查 `config.json` 是否已经写入设备根目录，并通过 CircuitPython 串口控制台查看错误信息。

### 中文文本无法正确输入

当前文本宏使用 `KeyboardLayoutUS`，不直接支持中文输入。中文内容可以通过复制英文快捷操作、剪贴板工具或输入法自动化实现，但不属于当前版本的直接功能。

### 组合键没有反应

确认组合键使用软件录制，或采用 `CTRL+C` 这样的格式；多个按键之间使用英文加号 `+`。

## 许可证

发布到 GitHub 前可以根据需要添加开源许可证，例如 MIT License。未添加许可证时，其他人通常无权复制、修改或分发项目代码。
