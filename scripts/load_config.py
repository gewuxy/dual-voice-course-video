#!/usr/bin/env python3
"""dual-voice-course-video 统一配置加载器（JSON，零第三方依赖）。

合并三层（优先级从高到低）：
  1. 环境变量  VOICE_CLONE / CHROME_BIN / FFMPEG / SYS_PY / TEACHER_NAME
  2. 课程配置  $H/视频课/course_config.json   （取向确认 gate 时生成）
  3. 环境配置  config.local.json              （机器相关，gitignore；缺失回退 config.example.json）

设计目标（对齐最佳实践「配置与代码分离、禁止 voodoo 常量」）：
  - 所有机器相关路径、音色模型名、帧间 gap、老师显示名都只在配置里出现一次
    （帧间 gap 走 frame_gap()，脚本里不许再出现字面量 0.9）
  - 脚本不写死任何绝对路径；换机只改 config.local.json 或 export 环境变量

用法（作为模块）：
    from load_config import load_config
    cfg = load_config(course_dir="/path/视频课")   # 返回合并 dict
    cfg["voice_clone_dir"]                         # 绝对路径（env 或 config）
    cfg["voices"]["teacher"]["exp"]                # "xiaoxian_v2"
    cfg["teacher_display_name"]                    # 展示层老师名（course 覆盖 defaults）
    frame_gap()                                    # 帧间静音秒（三方共用的唯一来源）

用法（CLI，供 bash 脚本取单值）：
    python3 load_config.py --get paths.voice_clone_dir
    python3 load_config.py --course "$H/视频课" --get voices.teacher.farewell
    python3 load_config.py --course "$H/视频课" --json     # 打印完整合并结果
"""
import os
import sys
import json
import argparse

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 帧间静音秒（阶段3 拼 _merged.wav、阶段4 standalone 时间轴、阶段6 切片切点三方共用）。
# 三者必须严格相等，否则末帧漂移数秒、音画失步（历史上写 0.25 漂移近 10s）。
# 全流水线唯一来源：脚本一律调 frame_gap()，禁止再写字面量 0.9。
DEFAULT_FRAME_GAP = 0.9


def _load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def load_config(course_dir=None):
    """返回合并后的配置 dict（环境变量 > 课程配置 > 环境配置）。"""
    env_cfg = _load_json(os.path.join(SKILL_DIR, "config.local.json")) \
        or _load_json(os.path.join(SKILL_DIR, "config.example.json")) \
        or {}

    course_cfg = {}
    if course_dir:
        course_cfg = _load_json(os.path.join(course_dir, "course_config.json")) or {}

    # 浅 + 局部深合并：course 的顶层键覆盖 env；dict 类值做一层合并
    merged = dict(env_cfg)
    for k, v in course_cfg.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = {**merged[k], **v}
        else:
            merged[k] = v

    # 环境变量最高优先级
    paths = merged.setdefault("paths", {})
    if os.environ.get("VOICE_CLONE"):
        paths["voice_clone_dir"] = os.environ["VOICE_CLONE"]
    if os.environ.get("CHROME_BIN"):
        paths["chrome_bin"] = os.environ["CHROME_BIN"]
    if os.environ.get("FFMPEG"):
        paths["ffmpeg"] = os.environ["FFMPEG"]
    if os.environ.get("SYS_PY"):
        paths["sys_py"] = os.environ["SYS_PY"]
    if os.environ.get("TEACHER_NAME"):
        merged["teacher_display_name"] = os.environ["TEACHER_NAME"]

    # 便捷顶层访问器（合并 defaults 与 course 覆盖）
    defaults = merged.get("defaults", {})
    merged["voice_clone_dir"] = paths.get("voice_clone_dir", "")
    merged["teacher_display_name"] = merged.get("teacher_display_name") \
        or defaults.get("teacher_display_name", "老师")
    merged["frame_gap"] = _as_float(
        merged.get("frame_gap", defaults.get("frame_gap", DEFAULT_FRAME_GAP)),
        DEFAULT_FRAME_GAP)
    merged["gap"] = merged["frame_gap"]      # 兼容旧键名
    return merged


def _as_float(v, fallback):
    try:
        return float(v)
    except (TypeError, ValueError):
        return fallback


def frame_gap(course_dir=None):
    """帧间静音秒——全流水线唯一来源。

    音频侧（_merged.wav）与画面侧（standalone 时间轴 / make_clips 切点）都取这个值，
    任何一方另写字面量都会造成音画失步。要改节奏请改 config 的 defaults.frame_gap，
    不要改脚本。（注：dialog2audio 的 --gap 是另一个东西——帧内行距，默认 0.4。）
    """
    return load_config(course_dir)["frame_gap"]


def voice_clone_dir():
    """返回 voice_clone 绝对路径；未配置则报错退出（不让脚本静默用错目录）。"""
    d = load_config().get("voice_clone_dir", "")
    if not d:
        sys.stderr.write(
            "✗ 未配置 voice_clone 目录。请二选一：\n"
            "  1) 复制 config.example.json 为 config.local.json 并填 paths.voice_clone_dir；\n"
            "  2) 运行前 export VOICE_CLONE=/path/to/voice_clone\n"
        )
        sys.exit(2)
    return d


def teacher_prefixes():
    """剧本老师角色标签列表（TTS 判声线用）。

    剧本固定写通用「老师：」；「小贤老师」兼容旧剧本；环境变量 TEACHER_NAME
    追加自定义前缀（方案 A 遗留写法）。verify_steps / dialog2audio_local 共用，
    不再各自维护一份。"""
    ps = ["老师", "小贤老师"]
    tn = os.environ.get("TEACHER_NAME")
    if tn and tn not in ps:
        ps.append(tn)
    return ps


def ref_path(speaker):
    """返回某说话人参考音的绝对路径（基于 voice_clone_dir + voices.<sp>.ref）。"""
    cfg = load_config()
    rel = cfg.get("voices", {}).get(speaker, {}).get("ref", "")
    if not rel:
        sys.exit(f"✗ voices.{speaker}.ref 未配置")
    return os.path.join(voice_clone_dir(), rel)


def farewell_path():
    """返回老师告别词音频的绝对路径（基于 voice_clone_dir + voices.teacher.farewell）。"""
    cfg = load_config()
    rel = cfg.get("voices", {}).get("teacher", {}).get("farewell", "")
    if not rel:
        sys.exit("✗ voices.teacher.farewell 未配置")
    return os.path.join(voice_clone_dir(), rel)


def _get_path(cfg, dotted):
    cur = cfg
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def main():
    ap = argparse.ArgumentParser(description="dual-voice-course-video 统一配置加载器")
    ap.add_argument("--get", help="取 dotted key，如 paths.voice_clone_dir / voices.teacher.ref")
    ap.add_argument("--course", help="课程目录（含 course_config.json）")
    ap.add_argument("--json", action="store_true", help="打印完整合并配置")
    args = ap.parse_args()

    cfg = load_config(args.course)
    if args.json:
        print(json.dumps(cfg, ensure_ascii=False, indent=2))
    elif args.get:
        val = _get_path(cfg, args.get)
        if val is None:
            sys.stderr.write(f"✗ 未找到配置项：{args.get}\n")
            sys.exit(1)
        print(val)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
