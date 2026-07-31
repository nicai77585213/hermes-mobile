---
name: Hermes
description: Sanitized Hermes Android APK project handoff memory for the public repository.
metadata:
  node_type: memory
  type: project
updated_at: 2026-07-14 09:55:00 +08:00
privacy: Public copy; local paths, device identifiers, network addresses, session IDs, delivery channels, and credentials are intentionally omitted.
---

# Hermes Android 项目读档

## 读档规则

1. 新会话先完整读取本文件，以 `updated_at`、`当前状态`、`当前阻塞`、`下一步` 为准。
2. 不要从历史提交中的旧“下一步”恢复任务，除非本文件明确要求回查。
3. 有新的架构决定、源码路径、构建结果、真机结论、阻塞或用户要求时，及时更新本文件。
4. 只保留可接续结论；不要写入凭据、真实设备信息、内网地址、个人路径、数据库内容或会话标识。
5. 涉及 UI 架构、首屏、导航或交互模式的大改，应先说明方案并获得确认。

## 项目目标

- 将完整 Hermes Agent 做成普通用户安装后即可使用的 Android App。
- 用户侧不安装 Termux、不手动部署 Agent、不依赖远程服务器或命令行。
- Hermes Agent、Python、Dashboard、Node/TUI 和必要依赖由 APK 内置，在手机本地初始化和运行。
- UI 延续 Hermes Desktop GUI 的产品气质，并针对移动设备提供抽屉、设置中心和能力页面。
- 当前发行目标允许较大的 APK，依赖和构建问题尽量在打包阶段解决。

## 当前状态

### Android 版本

- 当前 App 版本为 `versionCode 2` / `versionName 1.1`。
- 当前构建为 `arm64-v8a` debug APK，尚未完成正式签名和商店发布验收。
- `assembleDebug` 已成功，APK 元数据已通过 Android build-tools 校验。

### 已跑通的底层闭环

- 自定义 OpenAI 兼容端点现会把站点根地址规范化为 `/v1`，并按规范化端点或生成的 provider 名合并重复配置，同时保留已有非空密钥。该修复解决了重复 provider 使运行时选中错误根地址并返回空流的问题。
- 已用真实 Hermes Agent 会话验证 OpenAI 兼容中转的流式 Chat Completions：模型正常返回文本，单次 API 调用以 `finish_reason=stop` 完成。
- 移动模型预设和 Python provider 模型目录已加入 `gpt-5.6-sol`、`gpt-5.6-terra`、`gpt-5.6-luna`。
- APK 已内置 Python Agent、Dashboard 静态资源、Node.js/TUI runtime 及 ARM64 原生依赖。
- Dashboard、Agent 主进程、Node 子进程和 PTY 已在实体 Android 设备上验证可运行。
- 移动聊天使用本机 `/api/ws` JSON-RPC，包括 `session.create`、`session.resume`、`prompt.submit`、`message.delta` 和 `message.complete`。
- 移动会话已严格区分临时 live RPC ID 与持久数据库 session key；连续对话、App 强制停止后恢复和工具调用后的续聊已通过真机回归。
- 旧版误保存短 live ID 的会话仅在后端明确返回 `session not found` 时执行一次受控迁移，不再对正常长格式会话静默新建。
- 推理事件已显示为可折叠“思考过程”：流式生成期间自动展开，完成后自动折叠并保留完整内容。
- 工具事件已显示为运行中/完成/失败卡片，可展开查看摘要、耗时和结果；消息生命周期由结构化状态控制。
- 英文流式 token 不再错误插入空格，两份移动桥接文件保持同步。

### 内置无线 ADB

- 移动抽屉提供“接管手机”入口和无线调试配对/连接界面。
- Xiaomi、Redmi 和 POCO 设备会优先通过 Settings `SubSettings` 打开 `WirelessDebuggingFragment`，标准 Android 无线调试 Intent 保留为回退；真机 Fragment 状态已确认实际进入“无线调试”页面，而不是通用开发者选项。
- Android 原生桥支持 `devices`、`pair`、`connect` 和 `shell`。
- Agent 提供 `android_debug` 工具，使用 APK 内置的 ARM64 ADB 可执行文件，不依赖 Termux 或系统 `adb` 命令。
- 原生页面和 Python Agent 使用统一的 App ADB HOME，共享配对密钥和连接状态。
- Agent 初始化完成后会校验 `android_debug` 是否进入最终工具快照；如果工具集过滤遗漏，会从 registry 追加 schema，并记录不包含敏感值的诊断状态。
- 普通聊天曾因 Android 系统提示代码使用 `os.environ` 却缺少 `import os` 而崩溃；该根因已修复。
- 真机回归已确认：普通聊天成功、`android_debug` 真实执行并显示工具卡片、未错误调用 terminal 查找 adb、工具后续聊成功、App 强制停止后恢复成功。
- App 内 ADB 仍需用户在 Android 无线调试页面完成有效配对/连接，工具可用不代表设备已处于 `device` 状态。

### 已接入的移动能力页

- 资源中心：真实目录浏览、下载、返回上级和根目录。
- 定时自动化：读取任务、投递目标和模板，并支持触发/暂停/恢复。
- 接入：读取平台和 Gateway 状态，支持启停、重启和平台测试。
- 远程实例、记忆管理、Skills Hub：已读取真实状态。
- Persona、MCP、工具集、用量和外观：已接真实接口，但仍需继续完善操作闭环和真机覆盖。
- 沙箱、子代理、命令面板：仍待接入完整移动数据页和操作闭环。

## 当前阻塞

- App 当前没有 Foreground Service、`FOREGROUND_SERVICE` 权限或受控 WakeLock。短时切后台时后端任务曾继续运行，但 WebView JavaScript、流式事件和渲染可能被冻结；长时后台、锁屏、省电和系统回收下不保证存活。
- 推荐的后台架构是：由带常驻通知的 Foreground Service 承载 Hermes runtime；仅在活动任务期间持有受控 partial WakeLock；WebView 回前台后按持久 session key 补拉消息和任务状态。该架构属于产品级大改，实施前需确认通知与电量取舍。
- Chaquopy SQLite 缄少 FTS5，全文会话搜索当前禁用。
- 部分插件资源目录会产生缺少 `__init__.py` 的警告，需要区分资源目录提示和真实缺包。
- 内置 ADB 二进制目前来自 LADB 项目并已附带许可说明；该来源不适用于非官方 Google Play 发布，上架前必须替换为独立构建的 AOSP adb。
- 当前仍是 arm64-only debug 构建，尚未完成 release 签名、升级迁移、全新安装和覆盖升级验收。

## 下一步

1. 继续回归移动能力页的真实字段、刷新、错误提示和返回行为。
2. 补齐沙箱、子代理和命令面板的数据页，再按低风险到高风险增加操作闭环。
3. 所有删除、重置、卸载、销毁操作必须包含确认、结果反馈和失败恢复。
4. 若确认后台方案，增加 Foreground Service、任务期 WakeLock 和前台恢复补拉机制。
5. 继续覆盖不同 Android 厂商的无线调试设置跳转，并完成 App 内 ADB 的真实配对/连接闭环。
6. 最后处理 SQLite FTS5、插件警告、TTS/语音遗留、release 签名和发布工程。

## 关键工程路径

- Android App：`android/app/`
- 移动 Web 源码：`www/`
- Python Agent：`android/app/src/main/python/`
- Android 原生桥：`android/app/src/main/java/com/sesaloy/hermes/`
- ARM64 原生依赖：`android/app/src/main/jniLibs/arm64-v8a/`
- 常见 APK 输出：`android/app/build/outputs/apk/debug/app-debug.apk`

### 变更保护

- 两份移动桥文件必须保持完全一致：
  - `www/hermes-mobile-bridge.js`
  - `android/app/src/main/assets/public/hermes-mobile-bridge.js`
- 修改前先检查工作树状态，不要覆盖无关的既存改动。
- 不提交 `node_modules`、Gradle/build 目录、APK/AAB、签名文件、本机 `local.properties`、数据库、会话 dump、设备备份、日志或环境文件。

## 必须保留的技术约束

### Android 本机运行

- 当前 APK 仅支持 `arm64-v8a`。
- Node 可执行文件以 `jniLibs/arm64-v8a/libnode_exec.so` 打包，因为 Android 不允许直接执行私有 files 目录中的普通二进制。
- Gradle 必须保留 `packagingOptions { jniLibs { useLegacyPackaging true } }`。
- 启动环境涉及 `HERMES_NODE`、`HERMES_ANDROID_NATIVE_LIB_DIR`、`HERMES_ANDROID_ADB_HOME`、`HERMES_TUI_DIR`、`HERMES_SKIP_NODE_BOOTSTRAP` 和 `LD_LIBRARY_PATH`。
- Dashboard 静态构建产物必须存在于 APK 的 Chaquopy assets 中，否则启动后会出现 `Frontend not built`。

### WebView 与移动桥

- 不要只用 `/api/status` 判断本机服务是否真正可用。
- 页面请求必须有超时和渲染异常兜底，避免单页异常让整个移动壳黑屏。
- 文件附件应拉起 Android DocumentsUI。
- 不要全局启用 `CapacitorHttp.enabled: true`，否则本地静态资源可能白屏。
- 流式响应处理必须保持字节类型一致，不能把 `Uint8Array` 当字符串直接拼接。

### 安全与产品文案

- 不得把 API 密钥、令牌或签名材料写入源码、APK、日志或项目记忆。
- 面向普通用户的界面避免出现 Termux、部署、runtime、filesDir、dataDir、nativeLibraryDir、包名和调试路径等工程术语。
- 使用普通用户文案，例如“正在准备”“服务已启动”“需要完成模型设置”“连接失败，请检查 API 端点或密钥”。

## 构建

```powershell
./android/gradlew.bat -p ./android assembleDebug --console=plain
```

构建环境需要可用的 Android SDK、JDK、Python/Chaquopy 依赖以及项目要求的 ARM64 原生资源。

## 公开仓库隐私规则

- 本文件为公开副本；不得写入 API 密钥、访问令牌、个人绝对路径、设备标识、内网地址、真实会话 ID 或私人交付渠道信息。
- 不提交本机配置、签名文件、数据库、会话 dump、设备备份、日志、APK 或其他构建产物。
