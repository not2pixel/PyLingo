```
  _____  _    _  ____  _    _          _____ _  ________ _____  
 |  __ \| |  | |/ __ \| |  | |   /\   / ____| |/ /  ____|  __ \ 
 | |  | | |  | | |  | | |__| |  /  \ | |    | ' /| |__  | |__) |
 | |  | | |  | | |  | |  __  | / /\ \| |    |  < |  __| |  _  / 
 | |__| | |__| | |__| | |  | |/ ____ \ |____| . \| |____| | \ \ 
 |_____/ \____/ \____/|_|  |_/_/    \_\_____|_|\_\______|_|  \_\
                                                                
                                                                
```

# DuoHacker

**简体中文** · [English](README.en.md)

Duolingo 自动化工具 —— 刷 XP、刷宝石、刷连胜、自动完成练习、自动完成每日任务。基于 `rich` 的终端界面。

内置 GitHub Action,可每天自动完成每日任务并保持连胜,见 [GitHub Action](#github-action--每日自动运行)。

---

## 环境要求

- Python 3.8 或更高版本
- 可用的网络连接

所有 Python 依赖会在首次通过启动器运行时自动安装。

| 依赖 | 用途 | 自动安装 |
|---|---|---|
| `rich` | 终端界面、进度条、表格 | 是 |

---

## 安装

```bash
git clone []()
cd DuoHacker
```

无需手动 `pip install`,启动器会处理全部依赖。

---

## 使用

### 推荐 —— 通过启动器运行

```bash
python Launcher/Launcher.py
```

启动器会从 GitHub 拉取最新的 `main.py` 和 `requirements.txt`,安装新增依赖并写入本地缓存,然后运行。这样始终使用最新版本。

### 直接运行(跳过更新检查)

```bash
pip install -r src/requirements.txt
python src/main.py
```

---

## 启动器

`Launcher/Launcher.py` 是零依赖的自动更新器(纯标准库)。每次启动都会从 GitHub 获取最新脚本和依赖清单。

```
  DuoHacker-Python Launcher  v1.0.0

  ⠹ Fetching DuoHacker-Python.py
  ⠼ Fetching requirements.txt
  ✓ Up to date  1.0.0
  ✓ Dependencies up to date
```

### 启动器参数

```
python Launcher/Launcher.py [options]

  --offline    使用缓存运行,跳过更新与依赖检查
  --help       显示帮助
```

### 缓存结构

```
DuoHacker-Python/
├── Launcher/
│   ├── Launcher.py
│   └── .pylingo_cache/         ← 启动器缓存(已被 gitignore)
│       ├── pylingo.py          ← 从 GitHub 缓存的脚本
│       ├── requirements.txt    ← 从 GitHub 缓存的依赖清单
│       ├── meta.json           ← 版本、哈希、时间戳
│       ├── accounts.json       ← 添加第一个账号时创建
│       └── config.json         ← 首次修改设置时创建
└── src/
    ├── main.py
    ├── daily.py
    └── requirements.txt
```

---

## 获取 JWT

JWT 是浏览器中已登录 Duolingo 会话的认证令牌。

**桌面端(Chrome / Firefox / Edge)**

1. 打开 [duolingo.com](https://www.duolingo.com) 并登录
2. 打开开发者工具 —— Windows/Linux 按 `Ctrl+Shift+I`,Mac 按 `Cmd+Option+I`
3. 切到 **Console** 标签
4. 粘贴并执行:
   ```js
   document.cookie.match(/jwt_token=([^;]+)/)[1]
   ```
5. 复制输出的整串(`eyJ` 开头,不要带引号),在程序提示时粘贴

**移动端**

- iOS:[Web Inspector]()
- Android:[Kiwi Browser]() 并启用开发者工具

> JWT 大约 30 天过期,退出登录也会失效。剩余 3 天及以内时程序会给出警告。若遇到 403 错误,重新获取一个新的令牌并重新添加账号。

---

## GitHub Action —— 每日自动运行

仓库自带 [.github/workflows/daily.yml](.github/workflows/daily.yml),每天定时运行 [src/daily.py](src/daily.py),完成当日的每日任务(Daily Quests)并提交一次练习会话以保持连胜记录。

### 配置

1. Fork 或使用本仓库,进入 **Settings → Secrets and variables → Actions**
2. 新建 Repository secret:

   | Secret | 说明 |
   |---|---|
   | `DUOLINGO_JWT` | 你的 JWT。多账号可用换行、逗号或分号分隔 |

3. 可选 Repository variables:

   | Variable | 默认值 | 说明 |
   |---|---|---|
   | `TZ` | `Asia/Shanghai` | 时区,影响 Duolingo 的「当日」判定 |
   | `DELAY_MS` | `1500` | 请求间隔毫秒 |
   | `MAX_RETRY` | `3` | 每个步骤的最大重试次数 |

4. 打开 **Actions** 页签启用工作流。也可在该页手动点击 **Run workflow** 立即执行一次。

添加 secret 需要对仓库有 admin 权限。如果是 fork 的仓库,要在自己的 fork 下配置 —— fork 默认不继承上游 secret,且定时任务默认禁用,需手动启用。

### 运行时间

默认每天两次:UTC `01:00`(北京时间 09:00)和 UTC `13:00`(北京时间 21:00),后者作为当日补跑。修改 `cron` 即可调整。GitHub 的定时任务在高峰期可能延迟数十分钟。

### 执行逻辑

对每个 token 依次:

1. 校验 JWT 是否可解析、是否过期,过期则跳过并在日志中提示更新 secret
2. 拉取用户信息,若当日连胜已完成则跳过连胜步骤
3. 否则用当前时间戳提交一次 `GLOBAL_PRACTICE` 会话保持连胜
4. 调用 Goals API 完成所有未完成的每日任务
5. 重新拉取连胜天数,并写入 Actions 运行摘要

任一账号失败时任务以非零码退出,便于收到 GitHub 的失败通知。日志中的 token 始终以掩码形式输出。

### 本地测试

同一个脚本在本地跑,配置写进仓库根目录的 `.env`(已被 [.gitignore](.gitignore) 忽略,不会提交):

```bash
cp .env.example .env
# 编辑 .env,填入 DUOLINGO_JWT
python src/daily.py
```

[.env.example](.env.example) 列出了全部可用变量。也可用 `ENV_FILE` 指定其他路径:

```bash
ENV_FILE=/path/to/my.env python src/daily.py
```

真实环境变量优先级高于 `.env`,所以临时覆盖某一项直接写在命令前即可:

```bash
DELAY_MS=3000 python src/daily.py
```

GitHub Actions 上不存在 `.env`,脚本会自动回退到 secret 与 variables,无需改代码。

> 这不是演练模式。脚本会真的提交练习会话并完成任务,所以第一次本地测试就已经对账号产生实际影响。

---

## 功能

### 刷 XP

调用 Stories API,每次请求 499 XP。被限流时自动回退到 UNIT_TEST 会话(约 110 XP)。带实时进度条。

```
  ● XP  ████████████░░░░░░░░  4,970  0:00:03
```

### 刷宝石

调用奖励接口,每次 30 宝石,批量大小可配置。连续 5 次出错后自动停止。

```
  ● gems  ████████████░░░░░░░░  720  0:00:03
```

### 刷连胜 —— 安全模式

先计算账号注册至今的天数,再从连胜起始日往前提交 GLOBAL_PRACTICE 会话。连胜上限为账号存在的天数,不会超出合理范围。

```
  ╭──────────── Streak Farm — Safe Mode ────────────╮
  │  Created          2022-03-15                     │
  │  Account age      1,098 days                     │
  │  Current streak   0 days                         │
  │  Safe target      1,098 days                     │
  ╰──────────────────────────────────────────────────╯

  ● streak days  ████████░░░░░░░░░░  440/1098  0:01:22
```

### 刷连胜 —— 普通模式

无上限,从当前连胜起始日一直往前刷。风控风险更高,需要二次确认。

### 混合模式

每轮交替执行一次 XP 请求和一次宝石请求,用同一个延迟设置同时刷两者。

### 自动每日任务

通过 Goals API 一次性完成所有待办的每日任务。无需延迟,跑完即退出。

### 自动联赛

循环刷 XP,直到分数领先当前联赛第二名 1000 XP 为止,达到差距后自动停止。

---

## 终端界面

用数字键导航 —— 输入序号后回车。各菜单按分类着色。

```
  DuoHacker-Python  1.0.0  ·  14:32

  3 accounts — 1 expiring soon

  1. Farm            XP / Gems / Streak / Mixed / Quest / League
  2. Account Manager  Add, remove, and view saved accounts
  3. Shop Items       Browse and buy Duolingo shop items
  4. Generate Account Auto-generate new Duolingo accounts
  5. Streak Status    Check streak status across all accounts
  6. Settings         Configure DuoHacker-Python options

  0. Exit

  > _
```

---

## 多账号支持

可添加任意数量的账号。每个账号的 JWT、用户 ID 和缓存的资料都保存在 `accounts.json` 中。账号选择器会显示用户名、连胜、XP 和令牌过期状态。

JWT 过期提醒会自动出现:
- **剩余 3 天及以内** —— 主菜单副标题和 Farm 菜单显示黄色警告
- **已过期** —— 显示红色标签,禁止刷取

---

## 配置文件

设置保存在 `config.json`(首次修改时自动创建)。

| 键 | 默认值 | 说明 |
|---|---|---|
| `delay_ms` | `1500` | 刷取请求之间的默认延迟(毫秒) |
| `debug` | `false` | 打印原始 API 响应 |

可通过主菜单的 **Settings** 修改,也可直接编辑该 JSON 文件。

---

## 设置菜单

- **Default delay** —— 修改刷取请求延迟(最小 200 毫秒)
- **Debug mode** —— 开关原始 API 响应日志
- **Clear all accounts** —— 清空 `accounts.json`
- **Show accounts file** —— 打印 `accounts.json` 和 `config.json` 的路径

---

## 目录结构

```
DuoHacker-Python/
├── .github/workflows/
│   └── daily.yml      每日任务 + 连胜的定时工作流
├── .env.example       本地测试配置模板
├── .gitignore
├── Launcher/
│   └── Launcher.py    自动更新器与入口
├── src/
│   ├── main.py        主程序(交互式终端界面)
│   ├── daily.py       无人值守入口,用于 CI 或本地定时任务
│   ├── requirements.txt
│   ├── accounts.json  已保存的账号(自动创建,已忽略)
│   └── config.json    设置(自动创建,已忽略)
├── README.md          中文(默认)
├── README.en.md       英文
└── .DuoHacker-Python_cache/
    ├── DuoHacker-Python.py     从 GitHub 缓存的版本
    ├── requirements.txt
    └── meta.json      更新元数据
```

---

## 安全

- JWT 以明文保存在 `accounts.json` 中。请勿公开该文件,也不要提交到版本控制。
- `.env`、`accounts.json`、`config.json` 和启动器缓存已列入 [.gitignore](.gitignore)。
- 程序仅向 `www.duolingo.com` 和 `stories.duolingo.com` 发起 HTTPS 请求。
- 启动器仅从 `raw.githubusercontent.com/not2pixel/DuoHacker-Python` 拉取脚本。
- 不向任何第三方服务发送数据。

---

## 致谢

- API 端点与会话载荷参考自 [DuoXPy]()
- 浏览器自动化思路来自 [DuoHacker]()
- 界面主题来自 [DuoKLI]()

---

## 免责声明

本项目仅用于学习与研究。自动化 Duolingo 活动可能违反其[服务条款](https://www.duolingo.com/terms)。请自行承担风险。作者不对 Duolingo 对账号采取的任何处理负责。

---

## 许可证

MIT
