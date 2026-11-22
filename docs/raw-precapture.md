# RAW 连拍与预拍摄 / RAW capture and pre-capture

[简体中文](#简体中文) · [English](#english)

## 简体中文

### 功能

`--features raw-precapture` 让 C20（原 C15）／C30／C60 的预拍历史帧和正式帧按普通“画质”设置输出 RAW／RAW+JPEG／JPEG，使用“RAW 记录”选择 HE／HE★。QUAL／f2、i 菜单和取景画质标识使用相同的普通画质设置。预拍不支持无损压缩：C20／C30／C60 中无损选项禁用，普通拍照保存的无损按高效率★记录。在 C20／C30／C60 中按分配了“图像品质/尺寸”的按键时，尺寸固定为 L，M／S 灰显。

### 支持范围

支持**照片模式、FX/DX、全尺寸 L、C20／C30／C60、HE 或 HE★**，C60 始终记录 DX 区域。原 C15 现在每秒拍摄 20 张，菜单中显示为 C20：FX 下传感器仍以每秒 30 帧运行，每 3 帧取 2 帧（间隔交替为 33 与 67 毫秒）；DX 下传感器以每秒 60 帧运行，每第 3 帧为照片（间隔 50 毫秒）。取景与对焦保持原厂 C15 的帧率。JPEG 支持精细／标准／基本及 ★。不支持真正无损 RAW、C120 RAW、HLG/HEIF 或副卡独立 JPEG 尺寸计划。

缓存完整时，预拍 0.3／1 秒在 C20 最多保存 6／20 帧，在 C30 最多保存 9／30 帧，在 C60 最多保存 18／60 帧。30 帧（C60 为 60 帧）是历史窗口上限，不是整次连拍上限；关闭预拍时，正式帧仍使用所选格式。

### 使用步骤

1. 选择 FX/L 或 DX/L 和 C20、C30 或 C60（C60 始终记录 DX）。
2. 在普通“画质”中选择文件类型、JPEG 档位和 ★；在“RAW 记录”中选择 HE／HE★。
3. 设置预拍时长、后拍上限、主卡槽及副卡槽功能。无需 `Z8PRE.CFG`，旧配置文件不再读取。
4. 半按填充预拍缓存，再全按拍摄。等写入结束后再更换卡或调整文件格式。

### 输出与显示

NEF 使用原厂照片数据库与写入器，写完可直接回放，FX 输出通常带 **8256×5504** 整幅预览。RAW+JPEG Basic（不带 ★）复用主 JPEG 作为整幅预览，其余配对档位单独编码预览；独立 JPEG 使用所选品质。公开构建不附加诊断尾标。

主卡槽和副卡槽功能在每帧提交时记下，已排队帧继续使用提交时的设置：

| 副卡槽功能 | RAW | RAW+JPEG |
|---|---|---|
| 额外空间／单一目标卡 | 原厂选择的目标卡写 NEF | 同一目标卡写 NEF＋JPEG |
| 备份 | 两卡各写 NEF | 两卡各写 NEF＋JPEG |
| RAW 主卡－JPEG 副卡 | 两卡各写 NEF | 主卡 NEF，副卡 JPEG |
| JPEG 主卡－JPEG 副卡（单 JPEG 帧计划） | 两卡各写 NEF | 两卡各写 NEF＋JPEG |

剩余张数计入 NEF 大小，并随文件类型、RAW 压缩、JPEG 档位和 ★ 刷新。JPEG-only 保持原厂文件路径。

### 已知问题

- C15/C30 中无损选项禁用，普通拍照保存的无损按高效率★记录，退出后恢复该库的无损偏好。实拍 SD 文件确认 DX 预拍使用 5392×3592 有效区。
- 实际拍摄准入、空间预留、自动溢出和 r／缓冲显示仍按高速 JPEG 计划。数据库拒绝登记或锁失败时尝试 JPEG 回退，包括 RAW-only；该拒绝不创建停止文件。
- RAW 帧保留到 NEF 写完，缓存写满时连拍结束；预拍帧同样占用缓存。Z8 机身配 CFexpress 卡、仅 RAW 实测（03.12.f1）：C30 HE 约 184 张，C30 HE★ 约 74 张，C15 HE★ 约 130 张，C15 HE 接近跟上拍摄速度（每秒写入 14.4 个 NEF，拍摄 15 张／秒）。C60（03.12.q1，高速卡，每秒 60 帧）：HE★ 214–266 张，HE 394–519 张。需要更长连拍时请选择 HE。每张目标卡应保留充足空间。（本条中文由 AI 根据英文原文翻译。）
- C15／C30 下，相机把每帧以 HE／HE★ 压缩 RAW 保存在缓存中，之后再解码一次以生成 NEF 内的预览 JPEG（JPEG 模式下也用于生成 JPEG 本身）。该解码每秒约处理 245 MB 压缩 RAW，因此无论存储卡多快，HE（17 MB）每秒最多约处理并写入 14 帧，HE★（29 MB）约 8.6 帧；原厂 C30 JPEG 使用 HE，受同样的限制。更快的存储卡不能延长 C15／C30 RAW 连拍。C20 不经过这一解码（同一张卡上每秒写入 12 个 HE★ NEF），其速度由存储卡决定。（本条中文由 AI 根据英文原文翻译。）
- 仅 RAW 的 HE★ 连拍只为部分帧生成预览图像：第一帧、FX 每第 5 帧、DX 每第 3 帧，以及最后一帧（相机有余力时 DX 常会解码更多帧）。其余 NEF 带有常规尺寸的均匀灰色预览，包括整幅灰色 JpgFromRaw，因此相机回放和放大时显示为灰色；RAW 数据完整，RAW 转换软件可正常显示。Z8 机身配高速 CFexpress 卡实测：FX HE★ 每秒约 20 个 NEF（C30 每次连拍约 130 张），受写卡速度限制；DX HE★ 可保持每秒 30 帧（17 秒 510 张）。C60 下，仅 RAW 连拍解码第一帧、HE★ 每第 4 帧或 HE 每第 3 帧以及最后一帧；拍摄每秒 60 帧，每秒写入约 32 个（HE★）或 36 个（HE）NEF（03.12.q1）。C20 下，仅 RAW 连拍在 HE 下同样只解码部分帧（FX 每第 5 帧、DX 每第 3 帧）。Z8 机身配高速 CFexpress 卡实测（03.12.q2）：FX HE★ C20 连拍 12.5 秒 251 张，每秒写入 20 个 NEF，缓存未写满；每个 NEF 写入约 48 毫秒，接近 50 毫秒的帧间隔，较慢的卡会逐渐落后。（本条中文由 AI 根据英文原文翻译。）
- C20 下定时“后拍”的时长尚未测试：相机可能仍按每秒 15 帧计算帧数，使定时后拍提前结束。（本条中文由 AI 根据英文原文翻译。）
- 机内 NEF（RAW）处理现可用于预拍 NEF，包括带灰色预览的帧（已在 Z8 机身上测试，固件 03.12.v9）。用早期构建拍摄的预拍 NEF 带有高速快门模式值（MakerNote 0x0034 = 0x60），对其执行“润饰 › NEF（RAW）处理”会使相机重启；请在电脑上处理这些文件。（本条中文由 AI 根据英文原文翻译。）
- 实际 NEF 写入失败、写后找不到文件或达到默认 1.5 秒预算时，仍会尝试创建 `Z8PRESTP.BIN`。重启不清除停止文件；保留两卡文件并按[停止文件指南](stop-file.md)处理。停止额外 RAW 拍摄可选择 JPEG-only 或退出 C20／C30／C60。
- NEF 头按原厂 NEF 标签表写出：六个 SubIFD、镜头校正等 NEFInfo 块（0x05–0x07、0x0C、0x10–0x13）以及 MakerNote 0x0046／0x008C／0x00A4，不再带入仅属于 JPEG 的标签。SubIFD3–5 是空占位，仍没有原厂的 384×256 灰度子图；XMP 校正数据和 MakerNote 0x0093 仍缺失；使用自定义色调曲线的优化校准时不写 ContrastCurve。这项改动（[问题 #23](https://github.com/XinmiaoZhao/NikonFirmwarePatch/issues/23)、[#27](https://github.com/XinmiaoZhao/NikonFirmwarePatch/issues/27) 的机内“NEF（RAW）处理”与元数据差异）已在 Z8 机身上测试。
- 同时安装[照片工具](sdr-heif.md)时，C20／C30／C60 仍按 FX 或 DX 写 NEF／JPEG。C20 至 C120 中 SDR HEIF 禁用、压缩照片使用 JPEG；[新增画幅](photo-crop.md)只用于普通拍摄，在 C 档中禁用。（本条中文由 AI 根据英文原文翻译。）

## English

### Overview

`--features raw-precapture` makes C20 (formerly C15)/C30/C60 history and post-release frames follow ordinary Image quality: RAW/RAW+JPEG/JPEG. RAW recording selects HE/HE★. QUAL/f2, the i menu and shooting-screen indicators use the same ordinary quality setting. Pre-capture has no lossless compression: C20/C30/C60 disable the lossless option and record a lossless setting saved for ordinary shooting as HE★. At C20/C30/C60 the button assigned to Image quality/size fixes the size at L and greys out M/S.

### Supported modes

Supports **photo mode, FX/DX, full-size L, C20/C30/C60 and HE or HE★**; C60 always records the DX area. The former C15 now takes 20 photos per second and is shown as C20: in FX the sensor still runs at 30 fps and 2 of every 3 frames are kept (frames alternately 33 and 67 ms apart); in DX it runs at 60 fps and every 3rd frame is kept (50 ms apart). Viewfinder and AF keep stock C15's rates. JPEG supports Fine/Normal/Basic with or without ★. True lossless RAW, C120 RAW, HLG/HEIF and separately sized secondary JPEG plans are unsupported.

With a full buffer, 0.3/1-second history saves up to 6/20 frames at C20, 9/30 at C30 or 18/60 at C60. The 30-frame ceiling (60 in C60) applies to history, not the entire burst. With pre-capture off, current frames still use the selected format.

### Steps

1. Select FX/L or DX/L and C20, C30 or C60 (C60 always records DX).
2. Select file type, JPEG grade and ★ in ordinary Image quality; select HE/HE★ in RAW recording.
3. Set history duration, post-release limit, primary slot and secondary-slot role. No `Z8PRE.CFG` is required; old configuration files are ignored.
4. Half-press to fill history, then fully press to shoot. Let writing finish before changing cards or file format.

### Files and display

NEFs use the stock photo database/writer and support direct playback. FX output normally contains an **8256×5504** preview. RAW+JPEG Basic without ★ reuses its main JPEG for that preview; other paired grades encode a separate preview. Standalone JPEGs use the selected quality. Public builds do not append diagnostic footers.

Each submitted frame stores the primary slot and secondary role, so queued frames retain those settings:

| Secondary-slot role | RAW | RAW+JPEG |
|---|---|---|
| Overflow / one destination | NEF on the stock-selected destination | NEF + JPEG on that destination |
| Backup | NEF on each card | NEF + JPEG on each card |
| RAW primary – JPEG secondary | NEF on each card | NEF on primary, JPEG on secondary |
| JPEG primary – JPEG secondary (single-JPEG frame plan) | NEF on each card | NEF + JPEG on each card |

Remaining counts include NEF size and refresh with file type, RAW compression, JPEG grade and ★. JPEG-only retains the stock file path.

### Known issues

- C15/C30 disable the lossless option; a saved lossless setting is recorded as HE★ and restored afterwards. Camera files confirmed the 5392×3592 active area for DX pre-capture.
- Admission, reservations, overflow switching and r/buffer display retain the stock high-speed JPEG plan. Database/lock refusal attempts JPEG fallback, even for RAW-only; that refusal does not create a stop marker.
- RAW buffers remain occupied until NEF writing finishes, and a burst ends when the buffer is full; pre-release frames count against it. Measured on a Z8 with a CFexpress card, RAW-only (03.12.f1): C30 HE about 184 frames, C30 HE★ about 74, C15 HE★ about 130; C15 HE nearly keeps up (14.4 NEFs written per second against 15 frames per second). In C60 (03.12.q1, fast card, 60 fps): HE★ 214–266 frames, HE 394–519. Choose HE for longer bursts. Leave ample space on each destination card.
- In C15/C30 the camera keeps each frame in the buffer as compressed HE/HE★ RAW and decodes it again to make the preview JPEGs in the NEF (in JPEG modes, also the JPEG itself). That decode handles about 245 MB of compressed RAW per second, so frames are developed and written at most about 14 per second with HE (17 MB) and about 8.6 per second with HE★ (29 MB), whatever the card speed; stock C30 JPEG has the same limit with HE. A faster card does not lengthen C15/C30 RAW bursts. C20 does not go through this decode (on the same card it wrote 12 HE★ NEFs per second), so there the card is the limit.
- RAW-only HE★ bursts decode only some frames for the preview images: the first, every 5th in FX, every 3rd in DX, and the last (DX often decodes more when the camera has time). The other NEFs carry uniform gray previews at the usual sizes, including a full-size gray JpgFromRaw, so camera playback and zoom show plain gray for them; the RAW data is complete and raw converters render them normally. Measured on a Z8 with a fast CFexpress card: FX HE★ about 20 NEFs per second (about 130 frames per C30 burst), limited by writing to the card; DX HE★ keeps up at 30 fps (510 frames in 17 s). In C60, RAW-only bursts decode the first frame, every 4th frame with HE★ or every 3rd with HE, and the last; with 60 frames captured per second, about 32 (HE★) or 36 (HE) NEFs per second are written (03.12.q1). In C20, RAW-only bursts decode only some frames with HE as well (every 5th in FX, every 3rd in DX). Measured on a Z8 with a fast CFexpress card (03.12.q2): FX HE★ in C20 ran 251 frames over 12.5 s, written at 20 NEFs per second without filling the buffer; each NEF takes about 48 ms to write, close to the 50 ms frame interval, so a slower card falls behind gradually.
- A timed post-release burst in C20 has not been tested: the camera may still count its frames at 15 per second, which would end it early.
- In-camera NEF (RAW) processing works for pre-capture NEFs, including frames with gray previews (tested on a Z8, 03.12.v9). Pre-capture NEFs recorded with earlier builds carry the high-speed ShutterMode value (MakerNote 0x0034 = 0x60), with which Retouch › NEF (RAW) processing restarts the camera; process those files on a computer instead.
- Failed/missing NEF writes or reaching the default 1.5-second budget still attempt to create `Z8PRESTP.BIN`. Restarting does not clear it. Preserve both cards and follow the [stop-file guide](stop-file.md#english-summary). Select JPEG-only or leave C20/C30/C60 to stop extra RAW capture.
- NEF headers follow the stock NEF tag lists: six SubIFDs, the lens-correction and other NEFInfo blocks (0x05–0x07, 0x0C, 0x10–0x13) and MakerNote 0x0046/0x008C/0x00A4, without the JPEG-only tags. SubIFD3–5 are empty placeholders, so the stock 384×256 grayscale subimage is still absent, as are XMP correction metadata and MakerNote 0x0093. A Picture Control with a custom tone curve omits ContrastCurve. This change, made for the in-camera NEF (RAW) processing failure and metadata differences in [issue #23](https://github.com/XinmiaoZhao/NikonFirmwarePatch/issues/23) and [#27](https://github.com/XinmiaoZhao/NikonFirmwarePatch/issues/27), has been tested on a Z8.
- With the [still-photo tools](sdr-heif.md) installed, C20/C30/C60 still write NEF/JPEG in FX or DX. C20 through C120 disable SDR HEIF and use JPEG for compressed photos; the [added image areas](photo-crop.md) apply to ordinary shooting only and are disabled in the C modes.

## 相关文档 / Related documents

[构建与截图 / Build and screenshots](../README.md) · [已知问题 / Known issues](known-issues.md) · [验证记录 / Validation](validation.md) · [致谢与许可 / Attribution](../NOTICE.md)
