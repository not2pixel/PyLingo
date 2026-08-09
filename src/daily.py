#!/usr/bin/env python3
"""无人值守每日任务:完成每日任务(Daily Quests)并保持当日连胜(Streak)。

设计用于 GitHub Actions 定时运行,不依赖 accounts.json,全部凭据来自环境变量:

  DUOLINGO_JWT   一个或多个 JWT,使用换行、逗号或分号分隔(必填)
  MAX_RETRY      单个步骤的最大重试次数,默认 3
  DELAY_MS       请求之间的间隔毫秒,默认 1500
  TZ             时区,例如 Asia/Shanghai,影响 Duolingo 的“当日”判定

本地测试时可把以上变量写进仓库根目录的 .env(已被 .gitignore 忽略),
或用 ENV_FILE 指定其他路径。真实环境变量优先级高于 .env。
"""
import os
import re
import sys
import time
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)


def load_env_file():
    """读取 .env 到 os.environ,已存在的真实环境变量不会被覆盖。"""
    candidates = [os.environ["ENV_FILE"]] if os.environ.get("ENV_FILE") else [
        os.path.join(os.path.dirname(_HERE), ".env"),
        os.path.join(_HERE, ".env"),
    ]
    path = next((p for p in candidates if os.path.isfile(p)), None)
    if not path:
        return None

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            os.environ.setdefault(key, value)

    if os.environ.get("TZ") and hasattr(time, "tzset"):
        time.tzset()
    return path


_ENV_FILE = load_env_file()

from main import (  # noqa: E402
    _streak_session_once,
    auto_daily_quest,
    get_user_info,
    jwt_expired,
    jwt_expires_at,
    jwt_sub,
    streak_done_today,
)

MAX_RETRY = max(1, int(os.environ.get("MAX_RETRY") or 3))
DELAY_MS = max(0, int(os.environ.get("DELAY_MS") or 1500))


def out(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def parse_tokens(raw):
    return [t.strip().strip("'\"") for t in re.split(r"[\s,;]+", raw or "") if t.strip()]


def mask(token):
    return f"{token[:6]}…{token[-4:]}" if len(token) > 12 else "***"


def keep_streak(jwt, sub, user_info):
    """在“今天”提交一次练习会话,以保持连胜记录。"""
    for attempt in range(1, MAX_RETRY + 1):
        now = int(time.time())
        if _streak_session_once(jwt, sub, user_info, now - 300, now):
            return True
        out(f"  连胜会话失败,重试 {attempt}/{MAX_RETRY}")
        time.sleep(DELAY_MS / 1000 * attempt)
    return False


def run_account(token, index, total):
    label = f"账号 {index}/{total}"
    out(f"{label} — token {mask(token)}")

    try:
        sub = jwt_sub(token)
    except Exception as e:
        out(f"{label} — 无法解析 JWT: {e}")
        return {"user": mask(token), "ok": False, "detail": "无法解析 JWT"}
    if not sub:
        return {"user": mask(token), "ok": False, "detail": "JWT 中缺少 sub 字段"}

    if jwt_expired(token):
        out(f"{label} — JWT 已过期({jwt_expires_at(token)}),请更新 secret")
        return {"user": mask(token), "ok": False, "detail": "JWT 已过期"}

    try:
        info = get_user_info(token, sub)
    except Exception as e:
        out(f"{label} — 获取用户信息失败: {e}")
        return {"user": mask(token), "ok": False, "detail": f"获取用户信息失败: {e}"}

    username = info.get("username") or sub
    out(f"{label} — 用户 {username} | 连胜 {info.get('streak', 0)} 天 | JWT 到期 {jwt_expires_at(token)}")

    streak_ok = True
    if streak_done_today(info.get("streakData", {})):
        out(f"{label} — 今日连胜已完成,跳过")
        streak_note = "已完成"
    else:
        streak_ok = keep_streak(token, sub, info)
        streak_note = "已保持" if streak_ok else "失败"
        out(f"{label} — 连胜{streak_note}")

    time.sleep(DELAY_MS / 1000)

    quest_ok = False
    for attempt in range(1, MAX_RETRY + 1):
        try:
            quest_ok = bool(auto_daily_quest(token, sub, info))
        except Exception as e:
            out(f"  每日任务异常: {e}")
            quest_ok = False
        if quest_ok:
            break
        out(f"  每日任务失败,重试 {attempt}/{MAX_RETRY}")
        time.sleep(DELAY_MS / 1000 * attempt)

    streak_after = info.get("streak", 0)
    try:
        streak_after = get_user_info(token, sub).get("streak", streak_after)
    except Exception:
        pass

    return {
        "user": username,
        "ok": streak_ok and quest_ok,
        "streak": streak_after,
        "detail": f"连胜:{streak_note} / 每日任务:{'完成' if quest_ok else '失败'}",
    }


def write_summary(results):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    lines = [
        "## DuoHacker 每日运行结果",
        "",
        f"运行时间:{datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}",
        "",
        "| 账号 | 状态 | 连胜 | 详情 |",
        "| --- | --- | --- | --- |",
    ]
    for r in results:
        icon = "✅" if r["ok"] else "❌"
        lines.append(f"| {r['user']} | {icon} | {r.get('streak', '-')} | {r['detail']} |")
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    if _ENV_FILE:
        out(f"已加载本地配置 {_ENV_FILE}")

    tokens = parse_tokens(os.environ.get("DUOLINGO_JWT", ""))
    if not tokens:
        out("未设置 DUOLINGO_JWT。本地测试请写入 .env,GitHub Actions 请添加同名 secret")
        return 1

    out(f"共 {len(tokens)} 个账号,时区 {os.environ.get('TZ', 'UTC')}")
    results = []
    for i, token in enumerate(tokens, 1):
        results.append(run_account(token, i, len(tokens)))
        if i < len(tokens):
            time.sleep(DELAY_MS / 1000)

    write_summary(results)
    failed = [r for r in results if not r["ok"]]
    out(f"完成:成功 {len(results) - len(failed)} / {len(results)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
