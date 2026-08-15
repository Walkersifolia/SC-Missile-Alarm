# -*- coding: utf-8 -*-
"""导弹来袭音效合成器 — DeepSeek Harness 黑白极简风格 GUI (v4)
功能: 船厂选择 / 锁定固定1遍 / 远近次数可配 / 试听 / 导出 WAV
v4: 仅保留浅色模式 (移除深色模式与主题切换)
"""
import os
import sys
import tempfile
import threading
import winsound

import customtkinter as ctk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth_core import VENDORS, VENDOR_CN, get_material_files, synth, write_wav

APP_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(os.path.dirname(APP_DIR), "output")

# ============================================================
# DeepSeek Harness 浅色 token (来自 UI设计规范.md 实测值)
# ============================================================
T = {
    "bg": "#FFFFFF",          # 主背景
    "sidebar": "#F9FAFB",     # 侧边栏
    "nav_active": "#EBEEF2",  # 选中项
    "border": "#E5E9EE",      # 边框
    "label": "#0F1115",       # 主文字
    "label2": "#61666B",      # 次级文字
    "label3": "#81858C",      # 弱化文字
    "btn_primary": "#0F1115", # 主按钮黑底
    "btn_primary_hover": "#43454A",
    "btn_text": "#FFFFFF",
    "hover": "rgba(38,49,72,0.06)",
    "error": "#EC1313",
    "success": "#22C55E",
    "warn": "#F59E0B",
    "disabled_bg": "#F5F6F7",
}

FONT = "Microsoft YaHei UI"


class MissileAlertApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.current_vendor = "RSI"
        self.preview_path = None

        ctk.set_appearance_mode("light")
        self.title("星际公民玩家自己的闹钟生成器")
        self.geometry("1080x720")
        self.minsize(960, 640)
        self.configure(fg_color=T["bg"])

        # 设置窗口图标 (星际公民 logo)
        icon_path = os.path.join(APP_DIR, "assets", "app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self._build_sidebar()
        self._build_main()
        self._select_vendor("RSI")

    # ==========================================================
    # 构建: 左侧 280px 导航
    # ==========================================================
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=T["sidebar"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo 区
        logo_row = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=60)
        logo_row.pack(fill="x", padx=16, pady=(16, 10))
        self.logo_label = ctk.CTkLabel(logo_row, text="⏰ 闹钟生成器", font=(FONT, 15, "bold"),
                                       text_color=T["label"])
        self.logo_label.pack(side="left")

        # 主操作按钮
        self.export_btn = ctk.CTkButton(self.sidebar, text="导出 WAV", height=38, corner_radius=12,
                                        fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"],
                                        text_color=T["btn_text"], font=(FONT, 14, "bold"),
                                        command=self._export)
        self.export_btn.pack(fill="x", padx=14, pady=(0, 8))
        self.preview_btn = ctk.CTkButton(self.sidebar, text="▶ 预览合成", height=38, corner_radius=12,
                                         fg_color="transparent", border_width=1,
                                         border_color=T["border"], hover_color=T["hover"],
                                         text_color=T["label"], font=(FONT, 14, "bold"),
                                         command=self._preview)
        self.preview_btn.pack(fill="x", padx=14, pady=(0, 8))

        # 船厂选择区
        sec = ctk.CTkLabel(self.sidebar, text="选择船厂", font=(FONT, 12), text_color=T["label3"])
        sec.pack(fill="x", padx=16, pady=(12, 4))
        self.vendor_frame = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent", corner_radius=0)
        self.vendor_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._build_vendor_buttons()

        # 底部状态
        foot = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=42)
        foot.pack(fill="x", padx=16, pady=(0, 12))
        self.status_label = ctk.CTkLabel(foot, text="就绪", font=(FONT, 12), text_color=T["label3"])
        self.status_label.pack(side="left")

    # ==========================================================
    # 船厂按钮
    # ==========================================================
    def _build_vendor_buttons(self):
        for w in self.vendor_frame.winfo_children():
            w.destroy()
        self.vendor_buttons = {}
        for v in VENDORS:
            locked, far, near = get_material_files(v)
            ok = locked is not None and far is not None and near is not None
            label = f"{VENDOR_CN[v]}  {v}"
            if not ok:
                label += "  ⚠"
            btn = ctk.CTkButton(self.vendor_frame, text=label, height=34, corner_radius=12,
                                anchor="w", font=(FONT, 13),
                                fg_color=T["sidebar"], hover_color=T["hover"],
                                text_color=T["label"],
                                command=lambda vv=v: self._select_vendor(vv))
            btn.pack(fill="x", padx=6, pady=2)
            if not ok:
                btn.configure(state="disabled", text_color=T["label3"])
            self.vendor_buttons[v] = btn
        self._select_vendor(self.current_vendor)

    # ==========================================================
    # 构建: 主区 (grid 布局, 标签/控件分列)
    # ==========================================================
    def _build_main(self):
        main = ctk.CTkFrame(self, corner_radius=0, fg_color=T["bg"])
        main.pack(side="left", fill="both", expand=True)
        self.main = main

        # 居中内容容器
        content = ctk.CTkFrame(main, fg_color="transparent", width=760)
        content.pack(expand=True, fill="y")
        content.pack_propagate(False)

        # 标题
        self.title_label = ctk.CTkLabel(content, text="罗伯茨太空工业 (RSI)", font=(FONT, 24, "bold"),
                                        text_color=T["label"])
        self.title_label.pack(pady=(36, 2))
        self.sub_label = ctk.CTkLabel(content, text="被锁定 → 导弹来袭 音效合成", font=(FONT, 13),
                                      text_color=T["label3"])
        self.sub_label.pack(pady=(0, 24))

        # ---- 素材信息卡 ----
        self.info_card = ctk.CTkFrame(content, corner_radius=12, fg_color=T["disabled_bg"])
        self.info_card.pack(fill="x", padx=24, pady=(0, 20))
        self.info_label = ctk.CTkLabel(self.info_card, text="", font=(FONT, 13),
                                       text_color=T["label2"], justify="left")
        self.info_label.pack(fill="x", padx=18, pady=12)
        self._update_info()

        # ---- 参数区 (grid: 标签列 180px | 控件列 expand) ----
        params = ctk.CTkFrame(content, fg_color="transparent")
        params.pack(fill="x", padx=24)
        params.columnconfigure(0, minsize=180)
        params.columnconfigure(1, weight=1)
        self.params_frame = params

        r = 0
        # 锁定音 (固定 1 遍)
        self._param_label(params, r, "锁定音效")
        self.locked_val = ctk.CTkLabel(params, text="固定播放 1 遍（不可更改）", font=(FONT, 14),
                                       text_color=T["label2"], anchor="w")
        self.locked_val.grid(row=r, column=1, sticky="ew", padx=(8, 0), pady=6)
        r += 1

        # 远告警次数 (步进器 + 数字输入框)
        self._param_label(params, r, "远告警次数")
        self.far_repeat = self._stepper(params, default=12, minv=1, maxv=60)
        self.far_repeat["frame"].grid(row=r, column=1, sticky="w", padx=(8, 0), pady=6)
        r += 1

        # 远告警间隔 (滑块 + 数值)
        self._param_label(params, r, "远告警间隔 (秒)")
        frow = ctk.CTkFrame(params, fg_color="transparent")
        frow.grid(row=r, column=1, sticky="ew", padx=(8, 0), pady=6)
        self.far_period_slider = ctk.CTkSlider(frow, from_=0.08, to=0.50, number_of_steps=42,
                                               command=self._on_slider,
                                               fg_color=T["nav_active"], progress_color=T["label"],
                                               button_color=T["label"], button_hover_color=T["label2"])
        self.far_period_slider.set(0.16)
        self.far_period_slider.pack(side="left", fill="x", expand=True)
        self.far_period_val = ctk.CTkLabel(frow, text="0.16 秒", width=70, font=(FONT, 14),
                                           text_color=T["label2"])
        self.far_period_val.pack(side="left", padx=(12, 0))
        r += 1

        # 近告警次数
        self._param_label(params, r, "近告警次数")
        self.near_repeat = self._stepper(params, default=8, minv=1, maxv=60)
        self.near_repeat["frame"].grid(row=r, column=1, sticky="w", padx=(8, 0), pady=6)
        r += 1

        # 近告警间隔
        self._param_label(params, r, "近告警间隔 (秒)")
        nrow = ctk.CTkFrame(params, fg_color="transparent")
        nrow.grid(row=r, column=1, sticky="ew", padx=(8, 0), pady=6)
        self.near_period_slider = ctk.CTkSlider(nrow, from_=0.10, to=0.60, number_of_steps=50,
                                                command=self._on_slider,
                                                fg_color=T["nav_active"], progress_color=T["label"],
                                                button_color=T["label"], button_hover_color=T["label2"])
        self.near_period_slider.set(0.28)
        self.near_period_slider.pack(side="left", fill="x", expand=True)
        self.near_period_val = ctk.CTkLabel(nrow, text="0.28 秒", width=70, font=(FONT, 14),
                                            text_color=T["label2"])
        self.near_period_val.pack(side="left", padx=(12, 0))
        r += 1

        # 时长预览
        self.dur_label = ctk.CTkLabel(params, text="预计时长: —", font=(FONT, 14),
                                      text_color=T["label3"], anchor="w")
        self.dur_label.grid(row=r, column=0, columnspan=2, sticky="ew", pady=(14, 4))
        r += 1

        # 操作提示
        tip = ctk.CTkLabel(content, text="素材源自《星际公民》游戏音频 · 仅供个人使用",
                           font=(FONT, 11), text_color=T["label3"])
        tip.pack(pady=(22, 14))
        self._update_duration()

    def _param_label(self, parent, row, text):
        lbl = ctk.CTkLabel(parent, text=text, font=(FONT, 15), text_color=T["label"], anchor="w")
        lbl.grid(row=row, column=0, sticky="w", pady=6)
        return lbl

    # ==========================================================
    # 步进器 (− 数字输入框 +)
    # ==========================================================
    def _stepper(self, parent, default, minv, maxv):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        val = {"v": default}

        def clamp(n):
            return max(minv, min(maxv, n))

        def dec():
            val["v"] = clamp(val["v"] - 1)
            entry.delete(0, "end")
            entry.insert(0, str(val["v"]))
            self._update_duration()

        def inc():
            val["v"] = clamp(val["v"] + 1)
            entry.delete(0, "end")
            entry.insert(0, str(val["v"]))
            self._update_duration()

        def on_enter(_=None):
            try:
                n = clamp(int(entry.get()))
            except ValueError:
                n = val["v"]
            val["v"] = n
            entry.delete(0, "end")
            entry.insert(0, str(n))
            self._update_duration()

        b1 = ctk.CTkButton(frame, text="−", width=36, height=36, corner_radius=8,
                           fg_color="transparent", border_width=1, border_color=T["border"],
                           hover_color=T["hover"], text_color=T["label"], font=("Segoe UI", 18),
                           command=dec)
        b1.pack(side="left")
        entry = ctk.CTkEntry(frame, width=90, height=36, corner_radius=8, justify="center",
                             font=(FONT, 16, "bold"),
                             fg_color=T["bg"], border_color=T["border"], text_color=T["label"])
        entry.insert(0, str(default))
        entry.bind("<Return>", on_enter)
        entry.pack(side="left", padx=6)
        b2 = ctk.CTkButton(frame, text="+", width=36, height=36, corner_radius=8,
                           fg_color="transparent", border_width=1, border_color=T["border"],
                           hover_color=T["hover"], text_color=T["label"], font=("Segoe UI", 18),
                           command=inc)
        b2.pack(side="left")
        val["entry"] = entry
        return {"frame": frame, "get": (lambda: val["v"]), "entry": entry}

    # ==========================================================
    # 交互
    # ==========================================================
    def _select_vendor(self, v):
        self.current_vendor = v
        if hasattr(self, "title_label"):
            self.title_label.configure(text=f"{VENDOR_CN[v]} ({v})")
        self._update_info()
        for vv, btn in self.vendor_buttons.items():
            if vv == v and btn.cget("state") != "disabled":
                btn.configure(fg_color=T["nav_active"])
            elif btn.cget("state") == "disabled":
                btn.configure(fg_color=T["sidebar"], text_color=T["label3"])
            else:
                btn.configure(fg_color=T["sidebar"])
        self._update_duration()

    def _update_info(self):
        v = self.current_vendor
        locked, far, near = get_material_files(v)
        lines = []
        if locked:
            import wave
            w = wave.open(locked, "rb")
            dur = w.getnframes() / w.getframerate()
            w.close()
            lines.append(f"锁定: {os.path.basename(locked).replace('locked_', '').replace('.wav', '')}  ({dur:.2f}s)")
        if far:
            lines.append(f"远:   {os.path.basename(far).replace('far_', '').replace('.wav', '')}")
        if near:
            lines.append(f"近:   {os.path.basename(near).replace('near_', '').replace('.wav', '')}")
        if not far or not near:
            lines.append("⚠ 该船厂远/近素材缺失")
        if hasattr(self, "info_label"):
            self.info_label.configure(text="\n".join(lines))

    def _on_slider(self, _=None):
        self.far_period_val.configure(text=f"{self.far_period_slider.get():.2f} 秒")
        self.near_period_val.configure(text=f"{self.near_period_slider.get():.2f} 秒")
        self._update_duration()

    def _update_duration(self):
        if not hasattr(self, "far_repeat") or not hasattr(self, "near_repeat"):
            return
        try:
            far_r = self.far_repeat["get"]()
            near_r = self.near_repeat["get"]()
            far_p = self.far_period_slider.get()
            near_p = self.near_period_slider.get()
            dur = 0.80 + far_r * far_p + near_r * near_p
            self.dur_label.configure(
                text=f"预计时长: {dur:.1f} 秒（锁定 1 遍 + 远 {far_r} 次 × {far_p:.2f}s + 近 {near_r} 次 × {near_p:.2f}s）")
        except Exception:
            pass

    def _synth_params(self):
        return {
            "vendor": self.current_vendor,
            "far_repeat": self.far_repeat["get"](),
            "near_repeat": self.near_repeat["get"](),
            "far_period": round(self.far_period_slider.get(), 3),
            "near_period": round(self.near_period_slider.get(), 3),
        }

    def _preview(self):
        def work():
            try:
                self.status_label.configure(text="合成中…")
                p = self._synth_params()
                L, R, dur = synth(**p)
                tmp = os.path.join(tempfile.gettempdir(), "missile_preview.wav")
                write_wav(tmp, L, R)
                self.preview_path = tmp
                winsound.PlaySound(tmp, winsound.SND_FILENAME | winsound.SND_ASYNC)
                self.status_label.configure(text=f"播放中 ({dur:.1f}s)")
            except Exception as e:
                self.status_label.configure(text=f"错误: {e}")

        threading.Thread(target=work, daemon=True).start()

    def _export(self):
        from tkinter import filedialog
        p = self._synth_params()
        default_name = f"missile_incoming_{p['vendor']}.wav"
        path = filedialog.asksaveasfilename(
            title="导出合成音效", defaultextension=".wav",
            initialdir=OUTPUT_DIR, initialfile=default_name,
            filetypes=[("WAV 音频", "*.wav")])

        def work():
            if not path:
                return
            try:
                self.status_label.configure(text="导出中…")
                L, R, dur = synth(**p)
                write_wav(path, L, R)
                self.status_label.configure(text=f"已导出: {os.path.basename(path)} ({dur:.1f}s)")
            except Exception as e:
                self.status_label.configure(text=f"错误: {e}")

        threading.Thread(target=work, daemon=True).start()


if __name__ == "__main__":
    app = MissileAlertApp()
    app.mainloop()
