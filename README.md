# 星际公民玩家自己的闹钟生成器

将《星际公民》游戏内的**导弹来袭告警音效**提取、拼接，生成属于你自己的"导弹来袭闹钟"铃声。支持 15+ 家船厂的原版告警音（锁定告警 → 远距离告警 → 近距离告警），完全离线运行。

> 本项目从游戏 `Data.p4k`（只读）中提取 Wwise 音频素材，依据 soundbank 真实事件链拼接。素材版权归 Cloud Imperium Games 所有，本项目仅供个人娱乐使用。

## 特性

- 🚀 **15 家船厂**：圣盾动力 / 铁砧航天 / 南船座宇航 / 巴努 / 联合外域 / 十字军工业 / 德雷克行星际 / 埃斯佩里亚 / 灰猫工业 / 克鲁格星际 / 武藏工业与星航株式会社 / 起源跃动 / 剜度 / 希安 / 罗伯茨太空工业
- 🔒 **锁定告警固定 1 遍**（敌方锁定你时的 0.8s 告警音，不可配置，忠于游戏）
- ⏱ **远/近告警次数可调**：远距离告警循环 N 次、近距离告警循环 M 次，间隔可滑杆调节
- 🎧 **实时预览**：一键试听合成结果（Windows 原生播放，零依赖）
- 💾 **导出 WAV**：保存为 48kHz / 16bit / 立体声
- ⚡ **纯离线**：素材全部内置，无需游戏客户端、无需联网
- 🎨 **DeepSeek Harness 黑白极简风格** UI

## 快速开始（Windows）

### 方式一：直接使用已编译 exe

从 [Releases](https://github.com/Walkersifolia/SC-Missile-Alarm/releases) 下载最新 `SC-Missile-Alarm-vX.X.X-win64.zip`，解压后双击 `MissileAlert.exe`。

### 方式二：从源码运行

需要 Python 3.10+：

```bash
pip install customtkinter
python app.py
```

## 使用说明

1. 左侧选择船厂（如"罗伯茨太空工业 (RSI)"）
2. 右侧设置参数：
   - **远告警次数**：远距离阶段循环播放次数（默认 12）
   - **远告警间隔 (秒)**：远距离阶段每次告警的间隔（默认 0.16s）
   - **近告警次数**：近距离阶段循环播放次数（默认 8）
   - **近告警间隔 (秒)**：近距离阶段间隔（默认 0.28s）
3. 点击 **▶ 预览合成** 试听
4. 点击 **导出 WAV** 保存为闹钟铃声

> 提示：合成逻辑严格还原游戏事件链——锁定音播放 1 遍 → 远距离告警循环 → 近距离告警循环。

## 构建 exe（PyInstaller）

```bash
pip install pyinstaller customtkinter
pyinstaller MissileAlert.spec
```

产物在 `dist/MissileAlert/`。

## 项目结构

```
├── app.py              # GUI 主程序（customtkinter）
├── synth_core.py       # 音频拼接核心引擎（纯标准库）
├── MissileAlert.spec   # PyInstaller 构建配置
├── materials/          # 内置音频素材（16 家船厂 × 锁定/远/近）
│   └── <厂商>/         #   每家 3 个 wav（48kHz）
├── assets/
│   └── app_icon.ico    # 应用图标（星际公民 logo）
└── start_windows.bat   # Windows 一键启动脚本
```

## 素材说明

- 素材来源：`StarCitizen/LIVE/Data.p4k` → `Data/Sounds/wwise/UI_SSCS_<厂商>.bnk`
- 事件：`Play_UI_SSCS_<厂商>_Missile_Enemy_b_Locked`（锁定）、`Play_UI_SSCS_<厂商>_Missile_Enemy_c_Incoming`（来袭）
- 远/近素材按 SwitchID 匹配：`1455575902`（远）、`1374595281`（近）
- 转码工具链：StarBreaker（解包）→ ww2ogg（wem→ogg）→ ffmpeg（ogg→wav）
- **已知**：所有船厂的告警音实际是同一套模板（内容几乎相同），仅个别厂有音高差异——这是游戏本身的行为

## 免责声明

本项目与 Cloud Imperium Games 无关，未获其官方认可。所有音频素材版权归 Cloud Imperium Games 所有，仅用于个人学习与娱乐，请勿用于商业用途。
