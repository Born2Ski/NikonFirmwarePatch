# Born2Ski 分支：Nikon Z8 的 RAW 预拍与照片功能 / Born2Ski fork: RAW pre-capture and photo tools for the Nikon Z8

[简体中文](#简体中文) · [English](#english)

## English

This fork of [NikonFirmwarePatch](https://github.com/XinmiaoZhao/NikonFirmwarePatch) adds photo features on top of upstream
v0.5.0, mostly for long RAW pre-capture bursts (wildlife). The work is on branch `feature/raw-extras-menu`, and every
version tested on the camera is tagged (`photo-tools-v11.0` to `photo-tools-v15.0`). Everything here was tested on one Z8
by the author. It is experimental firmware: the warnings of the upstream [README](../README.md#english) apply. Firmware
files are never distributed. You build them yourself from Nikon's own C3.11 package (see [Build](#build)).

### Features

| Feature | What it does | Upstream |
|---|---|---|
| Pre-capture NEF fixes | Six SubIFDs with the stock tags, NEF-typed burst-start ID, series symbol in playback, parts on 512-byte boundaries (faster writing), in-camera NEF (RAW) processing | Being integrated by the maintainer (#61) |
| C60 RAW | C60 records NEFs (DX area) like C15/C30, up to 60 pre-release frames | Being integrated by the maintainer (#61) |
| Turbo RAW | RAW-only bursts decode only some frames; the others get gray previews and skip development, so bursts last longer | Fork only (left out upstream for now) |
| Auto N (v14) | Turbo RAW chooses how many frames to skip from the writer's measured pace | Fork only |
| Turbo RAW review (v11, v14.5, v15) | A Series playback speed that plays a series in real time showing only the decoded frames, also after power off/on and with the "Start series playback" button (pause included) | Fork only |
| C20 | C15 takes 20 photos per second, shown as C20 | Fork only (FX cadence is 33/67 ms) |
| Release mode per photo shooting menu bank | With Extended menu banks On, each bank keeps its release mode, pre-release and post-release burst | PR #67 (release modes); pre-release part ready as a follow-up |
| FX image area with DX lenses | Choose FX with a DX lens attached | #49; the maintainer will port it as a Custom Settings option, off by default |
| Fast card writes (v13) | During pre-capture NEF writes: CFexpress slot rate limiter off, 512-byte packets, per-file flush deferred to the burst's last NEF | Fork only; proposed upstream |
| RAW extras menu (v12) | Photo shooting menu row 2: one switch for each feature above | Fork only |

Details: [RAW pre-capture](raw-precapture.md#english), [release mode per bank](release-mode-banks.md#english),
[FX image area with DX lenses](dx-lens-fx.md#english), [CHANGELOG](../CHANGELOG.md).

### Results

RAW only, ProGrade CFexpress 4.0 512 GB card unless noted. Each line compares two settings of the same firmware.

| Change | Mode | Before | After |
|---|---|---|---|
| NEF parts on 512-byte boundaries (03.12.f1) | C30 FX HE, slower card | 134 frames, 6.4 NEFs/s | 184 frames, 14.3 NEFs/s |
| Turbo RAW Off → On (03.12.t1) | C30 FX HE★ | 73 frames | 129 frames, 20.4 NEFs/s |
| Turbo RAW Off → On (03.12.t1) | C60 DX HE★ | 203 frames | 267 frames, 31.3 NEFs/s |
| Fast card writes Off → On (03.12.k2) | C30 FX HE★ | 21.0 NEFs/s (987 MB/s) | 238 frames, 24.2 NEFs/s (1,819 MB/s) |
| Fixed N → Auto N (03.12.a1/a2) | C30 FX HE★ | 238 frames | 462 frames, 30 NEFs/s until the card's own buffer is used up |
| Fixed N → Auto N | C30 FX HE | about 14 fps (every frame decoded) | 485 frames, keeps up at 30 fps |
| Fixed N → Auto N | C60 DX HE★ | 214–266 frames | 542 frames |
| Fixed N → Auto N | C60 DX HE | 394–519 frames | 664 frames |

#### Combined

The features remove one limit after another, so they pay off together (C30, FX, HE★, RAW only, same card):

| Build | Frames per burst | NEFs written per second | What limits it next |
|---|---|---|---|
| Every frame decoded (Turbo RAW Off) | 73 | ~8.6 | the decode, ~116 ms per frame |
| + Turbo RAW (every 5th frame decoded) | 129 | 20.4 | the card writes (987 MB/s cap, a flush per file) |
| + Fast card writes | 238 | 24.2 | the decoded frames: the writer waits ~70 ms before every 5th NEF |
| + Auto N (N picked from the writer's pace, 8 here) | 462 | 30 (= capture) until the card's own buffer is used up (~300 frames), then ~22 | the card's buffer, then the camera's frame buffer |

Fast card writes alone changes little on a build that decodes every frame, and Turbo RAW alone stops at the card. With all
three, C30 FX HE★ RAW runs about 15 s at 30 fps (462 frames including pre-release), 6× the burst with every frame decoded.
C60 DX HE★: 203 frames with every frame decoded, 267 with Turbo RAW, 542 with all three. C30 FX HE keeps up with 30 fps
throughout (485 frames in 16 s, ended by releasing the shutter).

### Versions

| Tag | Firmware | Commit | Adds |
|---|---|---|---|
| `photo-tools-v11.0` | 03.12.s7 | `86e9683` | Release-mode banks, C20, FX area with DX lenses, Turbo RAW review |
| `photo-tools-v12.0` | 03.12.m1 | `ca53e8b` | RAW extras menu |
| `photo-tools-v13.0` | 03.12.k2 | `0560218` | Fast card writes |
| `photo-tools-v14.0` | 03.12.a2 | `7735834` | Auto N |
| `photo-tools-v14.5` | 03.12.e1 | `30ecac5` | Turbo RAW review follows Auto N |
| `photo-tools-v15.0` | 03.12.e3 | `5d19d26` | Turbo RAW review after power off/on and with the button |

### Build

1. Get Nikon's Z8 C3.11 firmware package (`Z_8_0311.bin`) and the upstream
   [v0.5.0 toolkit](https://github.com/XinmiaoZhao/NikonFirmwarePatch/releases/tag/v0.5.0), and extract the toolkit.
2. Copy the files of branch `feature/raw-extras-menu` over the extracted toolkit.
3. `python tools/build_precapture_unit.py` compiles the pre-capture, RAW recording menu and `z8nvme` units, and checks each
   against the bytes pinned in `resources/compiled.json`. The pins come from Apple clang 21.0.0 (clang-2100.4.1.1); another
   compiler may produce different bytes, and the check then stops.
4. `python patch.py Z_8_0311.bin --features still-photo-tools raw-precapture --version 03.12 --tag e3 --output build/v15`
   gives v15: `Z_8_0312.bin` with SHA-256 `e4f82b73a54f833351e6d2cd23eb3358bb0ddb68c1cbd93a791ddfc8870cbaca`.
5. `python verify.py Z_8_0311.bin build/v15/Z_8_0312.bin --features still-photo-tools raw-precapture --version 03.12 --tag e3`

Version and tag are labels only (the camera shows them); the code is C3.11's.

### Known limitations

- **Turbo RAW:** frames that are not decoded have gray previews in the camera and in apps that show the embedded preview.
  The RAW data is complete, and in-camera NEF (RAW) processing renders them normally.
- **Turbo RAW review** uses `Z8REVIEW.BIN` in the card root. Frames shot with older firmware, or whose card lacks that
  file, are stepped through at fixed steps.
- **Fast card writes:** tested with one card (ProGrade CFexpress 4.0 512 GB). It applies only while pre-capture NEFs are
  written; a power loss in the middle of a burst can lose the NEFs written since the last flush. It and its menu row exist
  only in builds without the video groups.
- **C120 RAW is not supported.** An experiment recorded C120 NEFs in the camera, but common converters cannot open its
  4140 × 2756 HE RAW.
- The remaining-frames counter does not count down during C15/C30 RAW bursts (as upstream).

## 简体中文

（本节中文由 AI 根据英文原文翻译。）

本分支基于 [NikonFirmwarePatch](https://github.com/XinmiaoZhao/NikonFirmwarePatch) v0.5.0，增加了一些照片功能，主要用于长时间的
RAW 预拍连拍（野生动物摄影）。代码位于分支 `feature/raw-extras-menu`，每个在相机上测试过的版本都有标签（`photo-tools-v11.0` 至
`photo-tools-v15.0`）。所有内容都由作者在一台 Z8 上测试。这是实验固件，上游 [README](../README.md#简体中文) 中的风险说明同样适用。
不分发固件文件：请用尼康官方的 C3.11 固件包自行构建（见[构建](#构建)）。

### 功能

| 功能 | 作用 | 上游 |
|---|---|---|
| 预拍 NEF 修复 | 六个 SubIFD 与原厂标签、NEF 类型的连拍起始编号、回放中的连拍组图标、各部分按 512 字节对齐（写入更快）、机内 NEF（RAW）处理 | 维护者正在整合（#61） |
| C60 RAW | C60 像 C15／C30 一样记录 NEF（DX 区域），预拍最多 60 帧 | 维护者正在整合（#61） |
| Turbo RAW | 仅 RAW 连拍只解码部分帧；其余帧使用灰色预览并跳过显像，因此连拍更长 | 仅本分支（上游暂不收录） |
| 自动 N（v14） | Turbo RAW 根据写入器实测速度决定跳过多少帧 | 仅本分支 |
| Turbo RAW 回放（v11、v14.5、v15） | 一个连拍回放速度：按实际时间播放连拍组，只显示已解码的帧；关机重开后以及用“开始连拍回放”按钮（含暂停）时同样有效 | 仅本分支 |
| C20 | C15 改为每秒 20 张并显示为 C20 | 仅本分支（FX 节奏为 33／67 毫秒） |
| 释放模式随照片拍摄菜单库切换 | “扩展菜单库”开启时，每个菜单库保存自己的释放模式、预拍连拍与释放后连拍 | PR #67（释放模式）；预拍部分已准备好作为后续 PR |
| DX 镜头使用 FX 影像区域 | 安装 DX 镜头时可选择 FX | #49；维护者将以“自定义设定”选项（默认关闭）移植 |
| 存储卡快速写入（v13） | 预拍写入 NEF 期间：CFexpress 插槽限速关闭、512 字节数据包、每个文件的 Flush 推迟到连拍最后一个 NEF | 仅本分支；已向上游提议 |
| RAW 附加功能菜单（v12） | 照片拍摄菜单第 2 行：上述每个功能一个开关 | 仅本分支 |

详细说明：[RAW 预拍](raw-precapture.md)、[释放模式随菜单库切换](release-mode-banks.md)、[DX 镜头使用 FX 影像区域](dx-lens-fx.md)、
[更新日志](../CHANGELOG.md)。

### 结果

除注明外均为仅 RAW、ProGrade CFexpress 4.0 512 GB 存储卡。每一行比较同一固件的两种设置。

| 改动 | 模式 | 之前 | 之后 |
|---|---|---|---|
| NEF 各部分按 512 字节对齐（03.12.f1） | C30 FX HE，较慢的卡 | 134 张，每秒 6.4 个 NEF | 184 张，每秒 14.3 个 NEF |
| Turbo RAW 关 → 开（03.12.t1） | C30 FX HE★ | 73 张 | 129 张，每秒 20.4 个 NEF |
| Turbo RAW 关 → 开（03.12.t1） | C60 DX HE★ | 203 张 | 267 张，每秒 31.3 个 NEF |
| 存储卡快速写入 关 → 开（03.12.k2） | C30 FX HE★ | 每秒 21.0 个 NEF（987 MB/s） | 238 张，每秒 24.2 个 NEF（1,819 MB/s） |
| 固定 N → 自动 N（03.12.a1／a2） | C30 FX HE★ | 238 张 | 462 张，在存储卡自身缓存用尽前每秒 30 个 NEF |
| 固定 N → 自动 N | C30 FX HE | 约每秒 14 张（每帧都解码） | 485 张，跟上每秒 30 张 |
| 固定 N → 自动 N | C60 DX HE★ | 214–266 张 | 542 张 |
| 固定 N → 自动 N | C60 DX HE | 394–519 张 | 664 张 |

#### 组合效果

这些功能依次消除一个又一个瓶颈，因此组合起来才真正见效（C30、FX、HE★、仅 RAW、同一张存储卡）：

| 构建 | 每次连拍张数 | 每秒写入 NEF 数 | 下一个限制 |
|---|---|---|---|
| 每帧都解码（Turbo RAW 关） | 73 | 约 8.6 | 解码，每帧约 116 毫秒 |
| + Turbo RAW（每第 5 帧解码） | 129 | 20.4 | 存储卡写入（每秒 987 MB 的限速、每个文件一次 Flush） |
| + 存储卡快速写入 | 238 | 24.2 | 解码帧：写入器在每第 5 个 NEF 前约等待 70 毫秒 |
| + 自动 N（按写入器速度选择 N，此处为 8） | 462 | 在存储卡自身缓存用尽前为 30（= 拍摄速度，约 300 张），之后约 22 | 存储卡缓存，然后是相机的帧缓存 |

单独使用存储卡快速写入时，在每帧都解码的构建上几乎没有提升；单独使用 Turbo RAW 时则受限于存储卡。三者组合时，C30 FX HE★ RAW
以每秒 30 张连续拍摄约 15 秒（含预拍共 462 张），是每帧都解码时的 6 倍。C60 DX HE★：每帧都解码 203 张，Turbo RAW 267 张，
三者组合 542 张。C30 FX HE 全程跟上每秒 30 张（16 秒 485 张，松开快门结束）。

### 版本

| 标签 | 固件 | 提交 | 新增 |
|---|---|---|---|
| `photo-tools-v11.0` | 03.12.s7 | `86e9683` | 释放模式随菜单库切换、C20、DX 镜头使用 FX 区域、Turbo RAW 回放 |
| `photo-tools-v12.0` | 03.12.m1 | `ca53e8b` | RAW 附加功能菜单 |
| `photo-tools-v13.0` | 03.12.k2 | `0560218` | 存储卡快速写入 |
| `photo-tools-v14.0` | 03.12.a2 | `7735834` | 自动 N |
| `photo-tools-v14.5` | 03.12.e1 | `30ecac5` | Turbo RAW 回放跟随自动 N |
| `photo-tools-v15.0` | 03.12.e3 | `5d19d26` | Turbo RAW 回放在关机重开后及按钮回放时同样有效 |

### 构建

1. 获取尼康 Z8 C3.11 固件包（`Z_8_0311.bin`）和上游 [v0.5.0 工具包](https://github.com/XinmiaoZhao/NikonFirmwarePatch/releases/tag/v0.5.0)，
   并解压工具包。
2. 将分支 `feature/raw-extras-menu` 的文件覆盖到解压后的工具包。
3. `python tools/build_precapture_unit.py` 编译预拍、RAW 记录菜单与 `z8nvme` 三个单元，并逐一与 `resources/compiled.json` 中固定的
   字节核对。这些字节由 Apple clang 21.0.0（clang-2100.4.1.1）生成；其他编译器可能生成不同的字节，此时核对会停止。
4. `python patch.py Z_8_0311.bin --features still-photo-tools raw-precapture --version 03.12 --tag e3 --output build/v15`
   生成 v15：`Z_8_0312.bin`，SHA-256 为 `e4f82b73a54f833351e6d2cd23eb3358bb0ddb68c1cbd93a791ddfc8870cbaca`。
5. `python verify.py Z_8_0311.bin build/v15/Z_8_0312.bin --features still-photo-tools raw-precapture --version 03.12 --tag e3`

版本号与标签只是标识（相机会显示它们）；代码为 C3.11。

### 已知限制

- **Turbo RAW：** 未解码的帧在相机中以及显示内嵌预览的软件中为灰色预览。RAW 数据完整，机内 NEF（RAW）处理可正常显像。
- **Turbo RAW 回放**使用存储卡根目录的 `Z8REVIEW.BIN`。用旧固件拍摄的帧，或所在存储卡没有该文件时，按固定步长回放。
- **存储卡快速写入：** 只用一张卡测试过（ProGrade CFexpress 4.0 512 GB）。只在写入预拍 NEF 时生效；连拍中途断电可能丢失上次
  Flush 之后写入的 NEF。该功能及其菜单行只存在于不含视频功能组的构建中。
- **不支持 C120 RAW。** 一次实验已能在相机中记录 C120 NEF，但常用转换软件无法打开其 4140 × 2756 的 HE RAW。
- C15／C30 RAW 连拍期间剩余张数不倒数（与上游相同）。
