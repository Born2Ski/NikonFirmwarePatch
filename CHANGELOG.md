# 更新日志 / Changelog

## 未发布 / Unreleased

已在 Z8 机身上测试（`photo-tools`，C15／C30／C60 预拍，机内“NEF（RAW）处理”与 RAW-only 回放）。`resources/compiled.json` 与 `resources/combinations.json` 中的预拍单元和组合配方已用 Apple clang 21.0.0（clang-2100.4.1.1）重新生成；构建方法：将本分支文件覆盖到解压后的 v0.4.0 完整工具包（其余八个预编译单元不变），运行 `python tools/build_precapture_unit.py` 生成并核对 `resources/precapture.bin`，再按默认预编译模式构建。

### 修改与修复

- **预拍 NEF 文件头。** 针对[问题 #23](https://github.com/XinmiaoZhao/NikonFirmwarePatch/issues/23)、[#27](https://github.com/XinmiaoZhao/NikonFirmwarePatch/issues/27)：机身自带的 NEF 读取器要求 IFD0 的 SubIFDs 恰好六项且后三项偏移非零，旧文件头只写三项（回退路径两项），因此“NEF（RAW）处理”提示“无法编辑照片”。现在始终写六个 SubIFD，SubIFD3–5 采用原厂无图像时的空占位。
- **与原厂 NEF 标签表对齐。** 新增 NEFInfo 块 0x05–0x07、0x0C、0x10–0x13（由原厂写入函数生成）和 MakerNote 0x0046、0x008C、0x00A4；不再从 JPEG 头带入 IFD0 0x013E／0x013F／0x0211、Exif 0xA500 与 MakerNote 0x0050。
- **RAW-only 预拍的连拍起始文件编号。** NEF 头由原厂为 JPEG 计划生成的文件头构建，因此 MakerNote 0x0056 的连拍起始编号为 JPG 类型，指向 RAW-only 下被取消的 JPEG。仅写 NEF 时，现将该编号的类型改为 NEF；原厂写入器完成时用于回放文件列表的 M+0x118／+0x11C 在写入期间同样给出 NEF 类型，写完后恢复。只修改通过原厂校验的编号；同卡 RAW+JPEG 不变。
- **RAW-only 连拍的回放连拍组图标。** RAW-only 时 NEF 写完后会取消该帧的 JPEG 成员，取消操作按数据库刷新回放列表中的条目，而数据库不含连拍字段，因此连拍组图标要到重新插卡后才显示（分组与翻组正常）。现在取消后按原厂写入器完成时的方式（0x406cd6bc–0x406cd75c）再次发送该 NEF 的“文件已写入”事件，带 NEF 类型的起始编号与连拍序号；只用于卡 1／2 上的连拍帧，不写卡。
- **C15／C30 连拍的 NEF 写入加速（固件 03.12.f1 实测）。** 旧 NEF 把 VGA、FHD 和整幅预览紧接排列在未对齐的文件偏移上；约四分之三的 NEF 在原厂写入器中要多用约 0.13 秒，RAW 帧每秒只能写入 5–6 张，缓存很快写满。现在 NEF 各部分与原厂 NEF 一样从 512 字节边界开始（在 MakerNote 范围内及预览之间补零）；图像数据不变，文件大小不变或增加 4 KB（RAW 数据仍从 4 KB 边界开始）。Z8 机身配 CFexpress 卡、仅 RAW 实测：C30 HE 由 134 张增至 184 张（每秒 6.4 → 14.3 个 NEF），C30 HE★ 66 → 74 张，C15 HE★ 90 → 130 张；C15 HE 每秒写入 14.4 个 NEF（拍摄 15 张／秒），一次连拍 412 张。剩余的限制是相机对缓存中每帧的解码（每秒约 245 MB 压缩 RAW），见已知问题。（本条中文由 AI 根据英文原文翻译。）
- **仅 RAW 的 HE★ 连拍只解码部分帧（已在 Z8 机身上测试，固件 03.12.p4）。** C15／C30 下缓存中每帧都要解码以生成预览 JPEG，这使仅 RAW 的 HE★ 每秒最多约 8.6 帧。现在只解码部分帧：连拍的第一帧、FX 每第 5 帧、DX 每第 3 帧，以及最后一帧（轮到解码时恰好是最新的帧也会解码）。其余帧的解码请求会被解码器拒绝；由于缓存中会残留较早帧的图像，这些 NEF 改为写入生成的均匀灰色预览（缩略图、VGA、FHD 及整幅 JpgFromRaw，相机放大时显示灰色）。RAW 数据完整，RAW 转换软件可正常显示。Z8 机身配高速 CFexpress 卡实测：FX HE★ 每次 C30 连拍由 74 张增至 84–94 张，每秒约 16 个 NEF，受相机 JPEG 编码限制（每帧仍会编码）；DX HE★ 由 135 张变为每秒 30 帧连续拍摄（17 秒 510 张）。HE、RAW+JPEG 与 JPEG 不变。（本条中文由 AI 根据英文原文翻译。）
- **跳过解码的帧不再编码主 JPEG（已在 Z8 机身上测试，固件 03.12.p6）。** 这些帧的 NEF 预览使用生成的灰色图像，但其主 JPEG 仍以全尺寸编码（FX 每帧在相机两个 JPEG 引擎上约 60 毫秒）后被丢弃。现在以一幅 160×120 灰色 JPEG 代替，不再执行该编码；NEF 仍由相机为该帧生成的文件头构建。Z8 机身配高速 CFexpress 卡实测：FX HE★ 每次 C30 连拍由 84–94 张增至约 100 张，每秒约 17 个 NEF，现受相机解码后逐帧处理的限制（每帧仍会处理）；DX HE★ 仍保持每秒 30 帧（9.7 秒 293 张）。所有文件通过 NEF 结构检查；这些帧的回放、放大和机内 NEF 处理均正常。（本条中文由 AI 根据英文原文翻译。）
- **跳过解码的帧不再进行显像处理（已在 Z8 机身上测试，固件 03.12.p8）。** 这些帧此前仍会用残留的解码缓存，在两个流水线阶段各做一次全尺寸显像处理（FX 每帧各约 48 毫秒）。现在不再执行显像任务，第二遍处理只交接缓冲区；相机自身的准备、元数据复制和清理仍照常进行。Z8 机身配高速 CFexpress 卡实测：FX HE★ 每次 C30 连拍由约 100 张增至 128 张，每秒 20.5 个 NEF，现受写卡速度限制（每个 NEF 约 34 毫秒写入，另加约 9 毫秒文件系统处理）；DX HE★ 仍保持每秒 30 帧（8.4 秒 254 张）。机内 NEF（RAW）处理的问题见下方 03.12.v9 的修正。（本条中文由 AI 根据英文原文翻译。）
- **C60 RAW（已在 Z8 机身上测试，固件 03.12.q1）。** C60 现在与 C15／C30 相同：预拍历史帧和正式帧按普通“画质”（RAW、RAW+JPEG、JPEG）和“RAW 记录”（HE／HE★）输出，预拍最多 60 帧（每秒 60 帧下 1 秒）。C60 始终记录 DX 区域（5408×3608 NEF，与 C15／C30 的 DX 文件相同）。仅 RAW 的 C60 连拍为第一帧、HE★ 每第 4 帧或 HE 每第 3 帧以及最后一帧生成真实预览，其余帧使用灰色预览。Z8 机身配高速 CFexpress 卡、仅 RAW、每秒 60.0 帧实测：HE★ 每次连拍 214–266 张（3.6–4.4 秒），每秒约 32 个 NEF；HE 394–519 张（6.6–8.6 秒），每秒约 36 个；缓存写满时连拍结束（约 140 张 HE★ 或 210 张 HE 待写入）。C120 RAW 仍不支持；C60 的 RAW+JPEG 以及 C60 文件在 RAW 转换软件中的表现尚未测试。（本条中文由 AI 根据英文原文翻译。）
- **C15 改为每秒 20 张并显示为 C20（已在 Z8 机身上测试，固件 03.12.q2）。** 传感器帧率保持原厂设置：FX 下以每秒 30 帧运行，每 3 帧取 2 帧作为照片（间隔交替为 33 与 67 毫秒）；DX 下以每秒 60 帧运行，每第 3 帧为照片（间隔 50 毫秒）。取景与对焦保持原厂 C15 的帧率。预拍 0.3／0.5／1 秒保存 6／10／20 帧（原为 5／8／15），仅 RAW 的连拍在 HE 下也只解码部分帧（FX 每第 5 帧、DX 每第 3 帧）。菜单、i 菜单等处的“C15”字样（36 种语言）改为“C20”，拍摄画面和释放模式选择中的连拍图标也由“15”改为“20”（CH 15 张／秒的图标不变）。Z8 机身配高速 CFexpress 卡、FX HE★、预拍 1 秒实测：12.5 秒连拍 251 张，每秒写入 20 个 NEF，缓存未写满（每个 NEF 写入约 48 毫秒，接近 50 毫秒的帧间隔，较慢的卡会逐渐落后）。FX HE、DX 以及定时后拍尚未测试。（本条中文由 AI 根据英文原文翻译。）
- **预拍 NEF 可在机内执行 NEF（RAW）处理（已在 Z8 机身上测试，固件 03.12.v9）。** 预拍 NEF 的 MakerNote 0x0034（快门模式）沿用高速连拍 JPEG 文件头中的 0x60（电子快门，高速），原厂固件从不把该值写入 NEF；“润饰 › NEF（RAW）处理”遇到该值会使相机重启（只改该值的普通 Z8 NEF 同样如此）。现在写入普通 Z8 NEF 的 0x10（电子快门）。已解码帧和带灰色预览的帧均可在机内处理。用早期构建拍摄的文件仍带 0x60。（本条中文由 AI 根据英文原文翻译。）

### 新增（已在 Z8 机身上测试，固件 03.12.d2）

> 本节中文由 AI 根据英文原文翻译。

- **DX 镜头使用 FX 影像区域。** 针对[问题 #45](https://github.com/XinmiaoZhao/NikonFirmwarePatch/issues/45)：`photo-tools` 现在允许在安装电子 DX 镜头（Z 卡口 DX 镜头，或经 FTZ 转接的 F 卡口 DX 镜头）时选择 FX（36×24），相当于 D850 的“自动 DX 裁切：关闭”。相机不再自动切换到 DX；需要 DX 时请手动选择。照片、视频和延时视频的“选择影像区域”、8K 与 FX N-RAW／ProRes RAW 视频尺寸、影像区域按键功能以及 PTP 设置不再因 DX 镜头而锁定。“图像除尘参照照片”在 DX 镜头下仍不可用；镜头仍按 DX 报告（EXIF、PTP）。共 36 处固定字节修改（`z8dxlens/patcher.py`），无新增代码；`resources/combinations.json` 中包含 `photo-tools` 的配置各增加这 36 行，其余不变。详见 [DX 镜头使用 FX 影像区域](docs/dx-lens-fx.md)。

### English

Tested on a Z8 (`photo-tools`, C15/C30/C60 pre-capture, in-camera NEF (RAW) processing and RAW-only playback). The pre-capture unit and combination recipes in `resources/compiled.json` and `resources/combinations.json` were regenerated with Apple clang 21.0.0 (clang-2100.4.1.1). To build, copy this branch over an extracted v0.4.0 toolkit (the other eight prebuilt units are unchanged), run `python tools/build_precapture_unit.py` to compile and check `resources/precapture.bin`, then build in the default prebuilt mode.

- **Pre-capture NEF header.** For [issue #23](https://github.com/XinmiaoZhao/NikonFirmwarePatch/issues/23) and [#27](https://github.com/XinmiaoZhao/NikonFirmwarePatch/issues/27): the camera's own NEF reader requires exactly six SubIFDs in IFD0 with non-zero offsets for the last three. The previous header wrote three (two on the fallback path), so Retouch › NEF (RAW) processing reported “Unable to edit picture”. Six are now always written; SubIFD3–5 are the empty placeholders stock firmware writes when a frame has no such image.
- **Stock NEF tag lists.** Adds NEFInfo blocks 0x05–0x07, 0x0C, 0x10–0x13 (produced by the stock writer functions) and MakerNote 0x0046, 0x008C, 0x00A4. IFD0 0x013E/0x013F/0x0211, Exif 0xA500 and MakerNote 0x0050 are no longer carried over from the JPEG header.
- **Burst-start file ID in RAW-only pre-capture.** The NEF header is built from the header the camera made for the JPEG plan, so MakerNote 0x0056 carried a JPG-typed burst-start ID pointing at a JPEG that RAW-only cancels. When a card gets only the NEF, the ID now has the NEF type. The stock writer's completion, which re-reads M+0x118/+0x11C for the playback file list, sees the same NEF-typed ID during the write, and the word is restored afterwards. Only IDs the stock validator accepts are changed; RAW+JPEG on one card is unchanged.
- **Series symbol in playback for RAW-only bursts.** In RAW-only, the frame's JPEG member is cancelled after the NEF is written. The cancel refreshes the playback-list entry from the database, which has no series fields, so the series symbol appeared only after the card was reloaded (grouping and group navigation already worked). After the cancel, the NEF's "file written" event is now sent again, built as the stock writer's completion builds it (0x406cd6bc–0x406cd75c), with the NEF-typed start ID and the shot number. This applies only to series frames on card 1 or 2 and writes nothing to the card.
- **Faster NEF writing in C15/C30 bursts (tested on a Z8, firmware 03.12.f1).** The NEF placed the VGA, FHD and full-size previews back to back at unaligned file offsets. For about three of every four NEFs the stock writer took about 0.13 s longer, so RAW frames reached the card at only 5–6 per second and the buffer filled quickly. Every part of the NEF now starts on a 512-byte boundary, as in stock NEFs (zero padding inside the MakerNote's range and between the previews); the image data is unchanged and a file is the same size or 4 KB larger (the RAW data still starts on a 4 KB boundary). Measured on a Z8 with a CFexpress card, RAW-only: C30 HE 134 → 184 frames (6.4 → 14.3 NEFs per second), C30 HE★ 66 → 74, C15 HE★ 90 → 130; C15 HE writes 14.4 NEFs per second against 15 frames per second and ran 412 frames in one burst. The remaining limit is the camera's decode of each buffered frame (about 245 MB of compressed RAW per second); see the known issues.
- **Partial decoding for RAW-only HE★ bursts (tested on a Z8, firmware 03.12.p4).** In C15/C30 the decode of each buffered frame for the preview JPEGs limits RAW-only HE★ to about 8.6 frames per second. Now only some frames are decoded: the first frame of a burst, every 5th frame in FX and every 3rd in DX, and the last frame (plus any frame that is the newest one when its turn comes). The other frames get a decode job the decoder refuses; because that leaves a stale image from an earlier frame in the buffer, their NEFs get generated uniform-gray previews instead (thumbnail, VGA, FHD and a full-size JpgFromRaw, so camera zoom shows gray). The RAW data is complete and raw converters render these frames normally. Measured on a Z8 with a fast CFexpress card: FX HE★ 74 → 84–94 frames per C30 burst at about 16 NEFs per second, limited by the camera's JPEG encoding, which still runs for every frame; DX HE★ 135 → continuous at 30 fps (510 frames in 17 s). HE, RAW+JPEG and JPEG are unchanged.
- **No main JPEG encode for the frames whose decode is skipped (tested on a Z8, firmware 03.12.p6).** Those frames' main JPEG was still encoded at full size (about 60 ms per FX frame on the camera's two JPEG engines) and then thrown away, since their NEF previews are the generated gray ones. Now a 160×120 gray JPEG stands in for it and the encode is not run; the NEF is still built from the camera's own header for the frame. Measured on a Z8 with a fast CFexpress card: FX HE★ 84–94 → about 100 frames per C30 burst at about 17 NEFs per second, now limited by the camera's processing of each frame after the decode, which still runs for every frame; DX HE★ still keeps up at 30 fps (293 frames in 9.7 s). All files passed the NEF structure check; playback, zoom and in-camera NEF processing work on these frames.
- **No development for the frames whose decode is skipped (tested on a Z8, firmware 03.12.p8).** Those frames were still developed at full size from the stale decode buffer, twice, in two pipeline stages (about 48 ms each per FX frame). Now the development job is not run and the second pass only hands its buffers on; the camera's own set-up, metadata copy and clean-up still run. Measured on a Z8 with a fast CFexpress card: FX HE★ about 100 → 128 frames per C30 burst at 20.5 NEFs per second, now limited by writing to the card (about 34 ms per NEF plus about 9 ms of file-system work); DX HE★ still keeps up at 30 fps (254 frames in 8.4 s). For in-camera NEF (RAW) processing see the 03.12.v9 fix below.
- **C60 with RAW (tested on a Z8, firmware 03.12.q1).** C60 now works like C15/C30: history and post-release frames follow ordinary Image quality (RAW, RAW+JPEG, JPEG) and RAW recording (HE/HE★), with up to 60 pre-release frames (1 s at 60 fps). C60 always records the DX area (5408×3608 NEFs, the same files as DX in C15/C30). RAW-only C60 bursts make real previews for the first frame, every 4th frame with HE★ or every 3rd with HE, and the last; the others get the gray previews. Measured on a Z8 with a fast CFexpress card, RAW-only, at 60.0 fps: HE★ 214–266 frames per burst (3.6–4.4 s) at about 32 NEFs per second, HE 394–519 frames (6.6–8.6 s) at about 36 per second; the burst ends when the buffer is full (about 140 HE★ or 210 HE frames waiting). C120 RAW is still unsupported; RAW+JPEG in C60 and raw-converter checks of C60 files have not been tested yet.
- **C15 takes 20 photos per second and is shown as C20 (tested on a Z8, firmware 03.12.q2).** The sensor rate stays stock: 30 fps in FX, where 2 of every 3 frames become photos (alternately 33 and 67 ms apart), and 60 fps in DX, where every 3rd frame does (50 ms apart); viewfinder and AF keep stock C15's rates. Pre-release keeps 6/10/20 frames for 0.3/0.5/1 s (stock 5/8/15), and RAW-only bursts decode only some frames with HE as well (every 5th in FX, every 3rd in DX). The "C15" label (36 languages) reads "C20", and the release-mode icon in the shooting display and the release-mode selection shows 20 instead of 15 (CH at 15 fps keeps its icon). Measured on a Z8 with a fast CFexpress card, FX HE★ with 1 s pre-release: 251 frames over 12.5 s, written at 20 NEFs per second without filling the buffer (about 48 ms per NEF against the 50 ms frame interval, so a slower card falls behind gradually). FX HE, DX and a timed post-release burst have not been tested yet.
- **In-camera NEF (RAW) processing of pre-capture NEFs (tested on a Z8, firmware 03.12.v9).** Pre-capture NEFs carried MakerNote 0x0034 (ShutterMode) = 0x60 (electronic, high speed) from the high-speed frame capture's JPEG header, a value stock firmware never writes into a NEF; Retouch › NEF (RAW) processing restarts the camera when it meets it (a normal Z8 NEF with only this value changed does too). The NEF now carries 0x10 (electronic), as a normal Z8 NEF does. Decoded frames and frames with gray previews process in camera. Files recorded with earlier builds still carry 0x60.

**New, tested on a Z8 (firmware 03.12.d2)** (the Chinese text for this entry was translated by AI):

- **FX image area with DX lenses.** For [issue #45](https://github.com/XinmiaoZhao/NikonFirmwarePatch/issues/45): `photo-tools` now lets you choose FX (36×24) with an electronic DX lens attached (Z-mount DX, or F-mount DX on the FTZ), like "Auto DX crop: Off" on the D850. The camera no longer switches to DX by itself; select DX when you want it. The photo, video and time-lapse "Choose image area" items, the 8K and FX N-RAW/ProRes RAW video sizes, the image-area button functions and the PTP image-area settings are no longer locked by a DX lens. Image Dust Off ref photo stays unavailable with DX lenses, and the lens is still reported as DX (EXIF, PTP). 36 fixed byte edits (`z8dxlens/patcher.py`), no new code; in `resources/combinations.json` every profile that includes `photo-tools` gains these 36 rows and nothing else changes. See [FX image area with DX lenses](docs/dx-lens-fx.md).

## [v0.4.0](https://github.com/XinmiaoZhao/NikonFirmwarePatch/releases/tag/v0.4.0) — 四组补丁 / Four feature groups

2026-11-10 发布。以下变化相对于上一公开功能系列 v0.3.0／v0.3.0-r1。v0.4.0 的源码、九份预编译补丁单元和固件补丁与预发布版 v0.4.0-rc.2 相同，只更新版本标注和下载链接；RC2 补全了 README 使用说明、致谢和模拟器截图，固件补丁与 RC1 相同。

### 新增

- **构建选项。** 可独立选择画幅、视频品质、Log 色彩和照片工具，或从原厂 C 3.11 一次构建任意非空组合，共 15 种。分别使用 `framing`、`video-quality`、`log-colour`、`photo-tools`；原来的四个 CLI 名称仅适用于对应旧工具包。
- **反挤压监看。** 画幅组新增关闭及 1.25× 至 2.00× 共七种校正倍率；按视频菜单库保存，用于取景、放大导航和回放，录像保留原始像素比例。开放门和 N-RAW 四档画质仍归同一组。
- **H.265 码率。** 视频品质组提供原厂标称码率的 100%、60%、45%、30%、20%，菜单可显示当前模式的目标 Mbps。100% 使用星标。ProRes 的 HQ／422／LT／Proxy 继续按菜单库保存，新增 HQ 星标。
- **Log 录像与监看。** 视频菜单可选 N-Log／BT.2020、S-Log3／S-Gamut3.Cine、Log3G10／REDWideGamutRGB。两种新增 Log 使用实拍标定的线性矩阵与色度补偿，具有对应的图标、片段名称和显示辅助。
- **DX RAW 预拍。** 照片工具扩展 C15/C30 的 DX 输出，保留完整 DX 预览，并按所选画质写出 RAW 或 RAW+JPEG。FX 和 DX 的无损选项在预拍时回退为 HE★。
- **后期与复核。** 增加中英文色彩报告、实拍／模拟色差图、两套机内监看表的来源、Resolve／Final Cut Pro 输入设置，以及供后期使用的 65³ F LUT。

### 修改与修复

- **像素位移组识别。** 修复[问题 #17](https://github.com/XinmiaoZhao/NikonFirmwarePatch/issues/17)。扫描器按文件类型、卡槽、文件夹和起始编号分别读取组身份；过去从 0001、2049 等之外的编号起拍时，完整组可能在列表中消失。现在无需重置文件编号，同一文件夹连续多组、跨 DSC_9999 边界和副卡组也可识别。常规完整性、曝光及位移检查仍然生效。
- **N-RAW 代理回放。** 详情页名称与显示辅助根据片段自己的 Log 名称选择。机身实测覆盖旧录与新录素材；回取景时恢复录像菜单选择。保留 RAW 本体的原厂色调分类，便于后期按 RAW 解码。
- **显示几何。** 反挤压状态下同步调整 AF 框、亮起的 AF 点与触控映射。影片回放按当前反挤压倍率显示。
- **视频菜单与编码。** ProRes 和 H.265 的星标按格式分流；离开 H.265 模式时，码率行显示百分比。调整 H.265 保护计时，避免部分 4K50/60 模式选 60% 后意外变成全帧内编码。
- **组合与分发。** 四组共享菜单布局、语言资源及菜单库字段复制。完整 toolkit 提供九份与源码匹配的编译单元。Windows CI 使用经哈希验证的发行 ZIP 构建固件，并将全选输出与提供的参考哈希比较。

### English

Released 2026-11-10. Changes are relative to the previous public series, v0.3.0/v0.3.0-r1. The source, nine compiled patch units and firmware patches of v0.4.0 match pre-release v0.4.0-rc.2; only version labels and download links changed.

**Added**

- Choose any of four build groups from stock Z8 C 3.11. The CLI supports all 15 nonempty combinations and has an interactive selection mode.
- Framing adds seven anamorphic desqueeze factors (1.25× through 2.00×) plus Off. The factor follows the movie bank in live view and is selectable for playback. Open gate and the four N-RAW quality tiers stay together.
- Video quality adds five H.265 bitrate targets (100/60/45/30/20%) and a displayed target in Mbps. The highest H.265 setting and ProRes HQ have format-specific stars.
- Select N-Log, S-Log3 or Log3G10 in the recording menu. Both new Log modes have calibrated recording matrices, chroma compensation, clip labels, icons and dedicated monitoring transforms.
- C15/C30 RAW pre-capture supports DX geometry and previews as well as FX. Lossless selection produces HE★ in pre-capture.
- The bilingual colour report, measurements, control simulations, grading instructions and optional 65³ F LUT document the capture-to-post workflow.

**Changed and fixed**

- Pixel-shift group discovery now checks the fields in the burst-start word individually. Complete groups can start at any file number, share a folder, roll over DSC_9999 or reside on the secondary card. This fixes the empty-list symptom in [issue #17](https://github.com/XinmiaoZhao/NikonFirmwarePatch/issues/17).
- N-RAW proxy playback selects the label and assist transform from the clip’s own Log name. The tester confirmed both on existing and new recordings. Returning to live view restores the recording selection.
- Desqueeze adjusts lit AF points, AF overlays and touch mapping. ProRes and H.265 share icon resources while keeping format-specific indicators and independent saved settings.
- The H.265 row shows a percentage outside H.265 mode. A protection-timer correction prevents an unintended all-intra pattern in certain 4K50/60 modes at the 60% setting.
- The toolkit bundles nine reviewed compiled units. Windows CI downloads and verifies the release ZIP before building and checking the reference full-selection firmware. RC2 restores the bilingual setup and recovery guidance, contributor credits and emulator gallery; its firmware patches match RC1.

## [v0.3.0-r1](https://github.com/XinmiaoZhao/NikonFirmwarePatch/releases/tag/v0.3.0-r1) — 2026-10-29

- v0.3.0 的第一次主机工具修订，修复 [issue #12](https://github.com/XinmiaoZhao/NikonFirmwarePatch/issues/12)：Windows 的反斜杠路径被误判为源码不匹配。
- 源码身份键统一为 `/`；仍逐字节校验源码与预编译补丁，不改变哈希要求。
- 加入 Windows／POSIX 路径回归、缺失与损坏文件负控，以及 Windows 默认预编译构建检查。
- 四份补丁机器码、15 种组合配方、原厂 C 3.11 输入要求及机内功能均与 v0.3.0 相同。原 v0.3.0 标签与附件保持不变。

English: first host-tool revision of v0.3.0. Fixes Windows source-path comparison by using forward-slash manifest keys, while preserving exact byte/hash checks. Adds cross-platform path regression, integrity negative controls and Windows prebuilt CLI checks. Firmware code, all 15 recipes and the required C 3.11 input are unchanged; the original v0.3.0 tag and assets are retained.

## [v0.3.0](https://github.com/XinmiaoZhao/NikonFirmwarePatch/releases/tag/v0.3.0) — 2026-10-29

- 新增机内像素位移组浏览、选择与 NEFX 合成，支持 4／8／16／32 张无损 NEF 组。
- 新增 FX 3:2 N-RAW 开放门，支持 8.3K 30／25／24p。
- 新增 N-RAW Fine／Basic，形成 High／Fine／Normal／Basic 四档，并提供相应菜单、文件标识与剩余录制时间估算。
- 四个功能选项可独立选择，共 15 种非空组合；ProRes 可与“开放门＋N-RAW”分别构建。
- 改进 RAW 预拍剩余张数：计入 NEF，并随 RAW 压缩、JPEG 档位及 ★ 设置刷新。
- 改进 RAW 预拍的登记拒绝处理：只尝试 JPEG 回退，不再绕过数据库直接写 NEF；后续帧可继续尝试正常 NEF 写入。停止文件机制仍保留。

English: adds in-camera pixel-shift merging, FX 3:2 N-RAW at 8.3K 30/25/24p, four N-RAW quality tiers, and independent selection of four features. Improves pre-capture remaining counts and database-refusal handling; the stop-file mechanism remains in use.

## [v0.2.0](https://github.com/XinmiaoZhao/NikonFirmwarePatch/releases/tag/v0.2.0)

- RAW 连拍／预拍新增 HE★，可在机内“RAW 记录”选择 HE／HE★。
- 移除对 `Z8PRE.CFG` 的依赖，直接使用机内设置；旧配置文件不再读取。
- QUAL／f2、i 菜单和取景画质标识使用普通“画质”设置。
- 完善双卡备份及 RAW／JPEG 分卡规则，每帧使用提交时的主卡槽和副卡槽设置。
- 保留 ProRes 四档与菜单库分别保存功能。

English: adds HE★ RAW capture, removes the CFG dependency, aligns quality controls/displays with the ordinary menu, and extends dual-card routing using the settings stored when each frame is submitted.

## [v0.1.0](https://github.com/XinmiaoZhao/NikonFirmwarePatch/releases/tag/v0.1.0)

- 首次公开面向官方 Nikon Z8 C 3.11 的补丁构建工具。
- 提供 ProRes HQ／Standard／LT／Proxy，支持按拍摄菜单库分别保存。
- 提供 C15／C30 HE RAW 连拍与预拍，使用普通画质菜单选择 RAW／RAW+JPEG／JPEG；NEF 带整幅预览并支持机内回放。
- ProRes 与 RAW 预拍可单独或组合构建。
- 提供源码、预编译补丁工具包和独立固件核验工具。

English: first public release for official Z8 C 3.11, with four ProRes grades, per-bank settings, C15/C30 HE RAW/pre-capture, selectable feature combinations, precompiled patch distribution and independent output verification.
