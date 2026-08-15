# -*- coding: utf-8 -*-
"""拼接核心引擎: 锁定固定 1 遍 + 远/近告警按用户指定次数循环"""
import sys
import wave
import struct
import math
import os
import json

SR = 48000

if getattr(sys, "frozen", False):
    # PyInstaller 打包环境: 素材打包在 _internal (onedir) / _MEIPASS (onefile)
    BASE = sys._MEIPASS
else:
    BASE = os.path.dirname(os.path.abspath(__file__))
MATERIALS = os.path.join(BASE, "materials")

VENDOR_CN = {
    "RSI": "罗伯茨太空工业", "AEGS": "圣盾动力", "ANVL": "铁砧航天", "ARGO": "南船座宇航",
    "BANU": "巴努", "CNOU": "联合外域", "CRUS": "十字军工业", "DRAK": "德雷克行星际",
    "ESPR": "埃斯佩里亚", "GRIN": "灰猫工业", "KRIG": "克鲁格星际", "MISC": "武藏工业与星航株式会社",
    "ORIG": "起源跃动", "VNCL": "剜度", "XIAN": "希安", "TMBL": "盾博尔地面系统",
}
VENDORS = list(VENDOR_CN.keys())


def load_manifest():
    """从 _manifest.json 读取各厂素材 ID 与缺失项"""
    path = os.path.join(MATERIALS, "_manifest.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_wav(path):
    """读取 wav -> mono float 列表"""
    w = wave.open(path, "rb")
    nch, sw, sr, nframes = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
    if sr != SR:
        raise ValueError(f"{path}: {sr}Hz != {SR}Hz")
    raw = w.readframes(nframes)
    w.close()
    fmt = "<%dh" % (nframes * nch)
    samples = struct.unpack(fmt, raw)
    if nch == 2:
        return [(samples[i] + samples[i + 1]) / 2 / 32768.0 for i in range(0, len(samples), 2)]
    return [s / 32768.0 for s in samples]


def get_material_files(vendor):
    """返回 (locked, far, near) 素材文件路径; 缺失返回 None"""
    vdir = os.path.join(MATERIALS, vendor)
    m = load_manifest().get(vendor, {})
    files = {}
    for role in ("locked", "far", "near"):
        sid = m.get(role)
        if sid:
            p = os.path.join(vdir, f"{role}_{sid}.wav")
            if os.path.exists(p):
                files[role] = p
    return files.get("locked"), files.get("far"), files.get("near")


def synth(vendor, far_repeat=12, near_repeat=8, far_period=0.16, near_period=0.28,
          far_start=0.80, locked_gain=0.9, alert_gain=0.9, total_override=None,
          fade_out=0.30):
    """
    合成音效:
      locked  固定 1 遍
      far     循环 far_repeat 次, 间隔 far_period
      near    循环 near_repeat 次, 间隔 near_period
    返回 (left, right) float 列表
    """
    locked_p, far_p, near_p = get_material_files(vendor)
    if locked_p is None:
        raise ValueError(f"{vendor} 缺少锁定音效素材")
    if far_p is None:
        raise ValueError(f"{vendor} 缺少远距离告警素材")

    lock = read_wav(locked_p)
    far = read_wav(far_p) if far_p else []
    near = read_wav(near_p) if near_p else []

    # 时间线
    lock_end = len(lock) / SR
    t_far = far_start
    far_dur = far_repeat * far_period if far_repeat > 0 else 0
    t_near = t_far + far_dur
    near_dur = near_repeat * near_period if near_repeat > 0 else 0
    total = t_near + near_dur

    if total_override and total_override > total:
        total = total_override

    n_total = int(total * SR)
    L = [0.0] * n_total
    R = [0.0] * n_total
    stereo = (L, R)

    def place(sound, offset_sec, gain):
        n = len(sound)
        start = int(offset_sec * SR)
        for i in range(n):
            idx = start + i
            if 0 <= idx < n_total:
                L[idx] += sound[i] * gain
                R[idx] += sound[i] * gain

    # 锁定固定 1 遍
    place(lock, 0.0, locked_gain)
    # 远告警 N 次
    for i in range(far_repeat):
        place(far, t_far + i * far_period, alert_gain)
    # 近告警 M 次
    for i in range(near_repeat):
        place(near, t_near + i * near_period, alert_gain)

    # 归一化 + 淡入淡出
    peak = max(max(abs(x) for x in L), max(abs(x) for x in R))
    if peak > 0:
        g = 0.98 / peak
        L = [x * g for x in L]
        R = [x * g for x in R]

    fade_in = int(0.01 * SR)
    for i in range(fade_in):
        f = i / fade_in
        L[i] *= f
        R[i] *= f
    fo = int(fade_out * SR)
    for i in range(min(fo, n_total)):
        f = (fo - i) / fo
        L[n_total - fo + i] *= f
        R[n_total - fo + i] *= f

    return L, R, total


def write_wav(path, left, right):
    n = min(len(left), len(right))
    out = bytearray()
    for i in range(n):
        l = max(-1.0, min(1.0, left[i]))
        r = max(-1.0, min(1.0, right[i]))
        out += struct.pack("<hh", int(l * 32767), int(r * 32767))
    w = wave.open(path, "wb")
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(bytes(out))
    w.close()
    return n / SR


if __name__ == "__main__":
    # 自测: RSI 默认参数
    L, R, dur = synth("RSI")
    print(f"RSI 合成成功: {dur:.2f}s, L峰值={max(abs(x) for x in L):.3f}")
    out = os.path.join(BASE, "..", "output", "test_synth_core.wav")
    write_wav(out, L, R)
    print(f"已写入 {os.path.abspath(out)}")
