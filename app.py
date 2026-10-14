import json
import os
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

APP_NAME = "Мій день"
BG = "#f4f6fb"
CARD = "#ffffff"
TEXT = "#202638"
MUTED = "#788198"
ACCENT = "#536dfe"
GREEN = "#239b72"
RED = "#d95368"
FONT = ("Segoe UI", 10)

def data_path():
    root = Path(os.environ.get("APPDATA", Path.home())) / "MiyDen"
    root.mkdir(parents=True, exist_ok=True)
    return root / "tasks.json"

class MiyDen:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("760x700")
        self.root.minsize(600, 560)
        self.root.configure(bg=BG)
        self.tasks = []
        self.timer_seconds = 25 * 60
        self.timer_running = False
        self.timer_mode = "focus"
        self.timer_job = None
        self.load_tasks()
        self.build_ui()
        self.render_tasks()
        self.update_timer()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def build_ui(self):
        outer = tk.Frame(self.root, bg=BG, padx=28, pady=24)
        outer.pack(fill="both", expand=True)
        header = tk.Frame(outer, bg=BG)
        header.pack(fill="x", pady=(0, 18))
        tk.Label(header, text="Мій день", bg=BG, fg=TEXT,
                 font=("Segoe UI", 25, "bold")).pack(anchor="w")
        tk.Label(header, text="Менше хаосу — більше зосередженості",
                 bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))

        timer = tk.Frame(outer, bg=CARD, padx=18, pady=15,
                         highlightthickness=1, highlightbackground="#e6e9f2")
        timer.pack(fill="x", pady=(0, 16))
        left = tk.Frame(timer, bg=CARD)
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text="ЧАС ДЛЯ ФОКУСУ", bg=CARD, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.timer_label = tk.Label(left, text="25:00", bg=CARD, fg=TEXT,
                                    font=("Segoe UI", 28, "bold"))
        self.timer_label.pack(anchor="w", pady=(2, 0))
        right = tk.Frame(timer, bg=CARD)
        right.pack(side="right", padx=(8, 0))
        self.timer_button = tk.Button(right, text="▶ Почати", command=self.toggle_timer,
            bg=ACCENT, fg="white", activebackground="#4058e8", activeforeground="white",
            relief="flat", bd=0, padx=16, pady=9, font=("Segoe UI", 10, "bold"), cursor="hand2")
        self.timer_button.pack(side="left", padx=(0, 7))
        tk.Button(right, text="Скинути", command=self.reset_timer, bg="#eef0ff", fg=ACCENT,
            relief="flat", bd=0, padx=12, pady=9, font=FONT, cursor="hand2").pack(side="left")
        self.mode_label = tk.Label(timer, text="25 хв фокус · 5 хв перерва",
                                   bg=CARD, fg=MUTED, font=("Segoe UI", 9))
        self.mode_label.pack(anchor="w", pady=(8, 0))

        tk.Label(outer, text="Завдання", bg=BG, fg=TEXT,
                 font=("Segoe UI", 16, "bold")).pack(anchor="w")
        form = tk.Frame(outer, bg=BG)
        form.pack(fill="x", pady=(10, 12))
        self.task_entry = tk.Entry(form, font=("Segoe UI", 11), relief="flat",
                                   bg=CARD, fg=TEXT, insertbackground=TEXT,
                                   highlightthickness=1, highlightbackground="#dfe3ee")
        self.task_entry.pack(side="left", fill="x", expand=True, ipady=11, padx=(0, 8))
        self.task_entry.bind("<Return>", lambda event: self.add_task())
        self.priority = tk.StringVar(value="Звичайний")
        tk.OptionMenu(form, self.priority, "Високий", "Звичайний", "Низький").pack(side="left", padx=(0, 8))
        tk.Button(form, text="+ Додати", command=self.add_task, bg=ACCENT, fg="white",
                  activebackground="#4058e8", activeforeground="white", relief="flat", bd=0,
                  padx=15, pady=10, font=("Segoe UI", 10, "bold"), cursor="hand2").pack(side="left")

        summary = tk.Frame(outer, bg=BG)
        summary.pack(fill="x", pady=(0, 8))
        self.progress_label = tk.Label(summary, text="0 із 0 виконано", bg=BG, fg=MUTED, font=FONT)
        self.progress_label.pack(side="left")
        self.progress_canvas = tk.Canvas(summary, height=6, bg="#e2e6f1", bd=0,
                                         highlightthickness=0)
        self.progress_canvas.pack(side="right", fill="x", expand=True, padx=(16, 0))

        list_wrap = tk.Frame(outer, bg=CARD, highlightthickness=1, highlightbackground="#e6e9f2")
        list_wrap.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(list_wrap, bg=CARD, bd=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(list_wrap, orient="vertical", command=self.canvas.yview)
        self.task_frame = tk.Frame(self.canvas, bg=CARD)
        self.task_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.task_frame, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.canvas_window, width=e.width))
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True, padx=10, pady=8)
        scrollbar.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        tk.Label(outer, text="Завдання зберігаються автоматично на цьому комп’ютері.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 0))

    def load_tasks(self):
        try:
            self.tasks = json.loads(data_path().read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError):
            self.tasks = []

    def save_tasks(self):
        try:
            data_path().write_text(json.dumps(self.tasks, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Помилка збереження", str(exc))

    def add_task(self):
        title = self.task_entry.get().strip()
        if not title:
            self.task_entry.focus_set()
            return
        self.tasks.append({"title": title, "priority": self.priority.get(), "done": False})
        self.task_entry.delete(0, "end")
        self.save_tasks()
        self.render_tasks()

    def delete_task(self, index):
        if 0 <= index < len(self.tasks):
            del self.tasks[index]
            self.save_tasks()
            self.render_tasks()

    def toggle_task(self, index, value):
        if 0 <= index < len(self.tasks):
            self.tasks[index]["done"] = bool(value)
            self.save_tasks()
            self.render_tasks()

    def render_tasks(self):
        for child in self.task_frame.winfo_children():
            child.destroy()
        if not self.tasks:
            tk.Label(self.task_frame, text="Поки немає завдань. Додайте перше вище ✨",
                     bg=CARD, fg=MUTED, font=("Segoe UI", 11), pady=28).pack(fill="x")
        for i, task in enumerate(self.tasks):
            row = tk.Frame(self.task_frame, bg=CARD, padx=7, pady=9)
            row.pack(fill="x")
            tk.Frame(row, bg="#edf0f6", height=1).pack(side="bottom", fill="x")
            checked = tk.BooleanVar(value=task.get("done", False))
            tk.Checkbutton(row, variable=checked, command=lambda idx=i, v=checked: self.toggle_task(idx, v.get()),
                bg=CARD, activebackground=CARD, selectcolor=CARD, relief="flat",
                highlightthickness=0, cursor="hand2").pack(side="left", padx=(0, 5))
            label = tk.Label(row, text=task.get("title", ""), bg=CARD,
                fg="#9aa1b1" if task.get("done") else TEXT,
                font=("Segoe UI", 10), anchor="w")
            label.pack(side="left", fill="x", expand=True)
            if task.get("done"):
                label.configure(font=("Segoe UI", 10, "overstrike"))
            priority = task.get("priority", "Звичайний")
            color = RED if priority == "Високий" else GREEN if priority == "Низький" else MUTED
            tk.Label(row, text=priority, bg=CARD, fg=color, font=("Segoe UI", 9, "bold")).pack(side="left", padx=8)
            tk.Button(row, text="×", command=lambda idx=i: self.delete_task(idx), bg=CARD, fg="#9aa1b1",
                      activebackground="#fff0f2", activeforeground=RED, relief="flat", bd=0,
                      font=("Segoe UI", 15), cursor="hand2").pack(side="right", padx=(4, 0))
        total = len(self.tasks)
        done = sum(1 for t in self.tasks if t.get("done"))
        self.progress_label.configure(text=f"{done} із {total} виконано")
        self.progress_canvas.delete("all")
        width = max(1, self.progress_canvas.winfo_width())
        self.progress_canvas.create_rectangle(0, 0, width * (done / total if total else 0), 6,
                                              fill=GREEN, outline="")

    def toggle_timer(self):
        self.timer_running = not self.timer_running
        self.timer_button.configure(text="Ⅱ Пауза" if self.timer_running else "▶ Продовжити")
        if self.timer_running:
            self.tick()

    def tick(self):
        if not self.timer_running:
            return
        if self.timer_seconds > 0:
            self.timer_seconds -= 1
            self.update_timer()
            self.timer_job = self.root.after(1000, self.tick)
        else:
            self.timer_running = False
            self.timer_button.configure(text="▶ Почати")
            messagebox.showinfo("Таймер", "Час завершився! Зробіть паузу та відпочиньте.")
            self.timer_mode = "break" if self.timer_mode == "focus" else "focus"
            self.timer_seconds = 5 * 60 if self.timer_mode == "break" else 25 * 60
            self.update_timer()

    def reset_timer(self):
        self.timer_running = False
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
        self.timer_seconds = 5 * 60 if self.timer_mode == "break" else 25 * 60
        self.timer_button.configure(text="▶ Почати")
        self.update_timer()

    def update_timer(self):
        mins, secs = divmod(self.timer_seconds, 60)
        self.timer_label.configure(text=f"{mins:02d}:{secs:02d}")
        self.mode_label.configure(text="5 хв перерва" if self.timer_mode == "break" else "25 хв фокус · 5 хв перерва")

    def close(self):
        self.save_tasks()
        if self.timer_job:
            try:
                self.root.after_cancel(self.timer_job)
            except tk.TclError:
                pass
        self.root.destroy()

if __name__ == "__main__":
    window = tk.Tk()
    MiyDen(window)
    window.mainloop()
