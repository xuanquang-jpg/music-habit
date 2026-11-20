import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from analysis import (load_history, clean_history, summary,
                      plays_by_hour, plays_by_weekday, minutes_by_month,
                      top_artists, top_tracks, filter_by_date)


class MusicApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Phân tích thói quen nghe nhạc Spotify")
        self.geometry("1000x650")
        self.df = None  # dữ liệu sẽ nạp sau khi chọn thư mục
        self.df_all = None

        self.build_top_bar()
        self.build_tabs()
        self.build_time_tab()
        self.build_artists_tab()

    def build_top_bar(self):
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=10, pady=8)

        ttk.Button(bar, text="Chọn thư mục dữ liệu",
                   command=self.choose_folder).pack(side="left")
        self.status = ttk.Label(bar, text="Chưa nạp dữ liệu")
        self.status.pack(side="left", padx=10)

        ttk.Button(bar, text="Bỏ lọc", command=self.reset_filter).pack(side="right")
        ttk.Button(bar, text="Lọc", command=self.apply_filter).pack(side="right", padx=5)
        self.end_entry = ttk.Entry(bar, width=11)
        self.end_entry.pack(side="right")
        ttk.Label(bar, text="đến").pack(side="right", padx=4)
        self.start_entry = ttk.Entry(bar, width=11)
        self.start_entry.pack(side="right")
        ttk.Label(bar, text="Từ ngày (YYYY-MM-DD):").pack(side="right", padx=4)
    def build_tabs(self):
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=5)

        self.tab_overview = ttk.Frame(self.tabs)
        self.tab_time = ttk.Frame(self.tabs)
        self.tab_artists = ttk.Frame(self.tabs)

        self.tabs.add(self.tab_overview, text="Tổng quan")
        self.tabs.add(self.tab_time, text="Theo thời gian")
        self.tabs.add(self.tab_artists, text="Nghệ sĩ")

        self.overview_label = ttk.Label(self.tab_overview, text="",
                                        font=("Segoe UI", 14), justify="left")
        self.overview_label.pack(anchor="nw", padx=20, pady=20)

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục chứa StreamingHistory")
        if not folder:
            return
        try:
            self.df_all = clean_history(load_history(folder))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không đọc được dữ liệu:\n{e}")
            return
        self.reset_filter()

    def show_overview(self):
        s = summary(self.df)
        text = (f"Tổng lượt nghe: {s['total_plays']}\n"
                f"Tổng giờ nghe: {s['total_hours']:.1f}\n"
                f"Số nghệ sĩ khác nhau: {s['unique_artists']}\n"
                f"Số bài khác nhau: {s['unique_tracks']}\n"
                f"Trung bình mỗi ngày có nghe: {s['avg_per_day']:.0f} phút")
        self.overview_label.config(text=text)
    def build_time_tab(self):
        # Hàng chọn loại biểu đồ
        top = ttk.Frame(self.tab_time)
        top.pack(fill="x", padx=10, pady=8)
        ttk.Label(top, text="Xem theo:").pack(side="left")

        self.time_choice = ttk.Combobox(
            top, state="readonly", width=15,
            values=["Giờ trong ngày", "Thứ trong tuần", "Tháng"])
        self.time_choice.current(0)
        self.time_choice.pack(side="left", padx=8)
        self.time_choice.bind("<<ComboboxSelected>>",
                              lambda e: self.draw_time_chart())

        # Biểu đồ: tạo một lần
        self.time_fig = Figure(figsize=(7, 4), dpi=100)
        self.time_ax = self.time_fig.add_subplot(111)
        self.time_canvas = FigureCanvasTkAgg(self.time_fig, master=self.tab_time)
        self.time_canvas.get_tk_widget().pack(fill="both", expand=True,
                                              padx=10, pady=5)
    def build_artists_tab(self):
        # Hàng điều khiển
        top = ttk.Frame(self.tab_artists)
        top.pack(fill="x", padx=10, pady=8)

        ttk.Label(top, text="Xếp theo:").pack(side="left")
        self.artist_by = ttk.Combobox(top, state="readonly", width=14,
                                      values=["Phút nghe", "Số lượt"])
        self.artist_by.current(0)
        self.artist_by.pack(side="left", padx=8)
        self.artist_by.bind("<<ComboboxSelected>>",
                            lambda e: self.draw_artists())

        ttk.Label(top, text="Top N:").pack(side="left", padx=(20, 0))
        self.top_n = tk.IntVar(value=10)
        self.n_label = ttk.Label(top, text="10", width=3)
        ttk.Scale(top, from_=5, to=20, orient="horizontal", length=180,
                  command=self.on_n_change).pack(side="left", padx=8)
        self.n_label.pack(side="left")

        # Khung chia đôi: biểu đồ bên trái, bảng bài hát bên phải
        body = ttk.Frame(self.tab_artists)
        body.pack(fill="both", expand=True, padx=10, pady=5)

        self.art_fig = Figure(figsize=(5, 4), dpi=100)
        self.art_ax = self.art_fig.add_subplot(111)
        self.art_canvas = FigureCanvasTkAgg(self.art_fig, master=body)
        self.art_canvas.get_tk_widget().pack(side="left", fill="both", expand=True)

        self.track_table = ttk.Treeview(body, columns=("track", "artist", "plays"),
                                        show="headings", height=15)
        self.track_table.heading("track", text="Bài hát")
        self.track_table.heading("artist", text="Nghệ sĩ")
        self.track_table.heading("plays", text="Lượt")
        self.track_table.column("track", width=200)
        self.track_table.column("artist", width=130)
        self.track_table.column("plays", width=50, anchor="e")
        self.track_table.pack(side="right", fill="y", padx=(10, 0))
    def draw_time_chart(self):
        if self.df is None:
            return
        choice = self.time_choice.get()
        ax = self.time_ax
        ax.clear()

        if choice == "Giờ trong ngày":
            data = plays_by_hour(self.df)
            ax.bar(data.index, data.values)
            ax.set_xlabel("Giờ")
            ax.set_ylabel("Số lượt nghe")
            ax.set_xticks(range(0, 24, 2))
            ax.set_title("Số lượt nghe theo giờ trong ngày")
        elif choice == "Thứ trong tuần":
            data = plays_by_weekday(self.df)
            ax.bar(data.index, data.values)
            ax.set_ylabel("Số lượt nghe")
            ax.set_title("Số lượt nghe theo thứ trong tuần")
        else:
            data = minutes_by_month(self.df) / 60
            ax.plot(data.index, data.values, marker="o")
            ax.set_ylabel("Số giờ nghe")
            ax.set_title("Số giờ nghe theo tháng")
            ax.tick_params(axis="x", rotation=45)

        self.time_fig.tight_layout()
        self.time_canvas.draw()
    def on_n_change(self, value):
        self.top_n.set(int(float(value)))
        self.n_label.config(text=str(self.top_n.get()))
        self.draw_artists()

    def draw_artists(self):
        if self.df is None:
            return
        n = self.top_n.get()
        by = "plays" if self.artist_by.get() == "Số lượt" else "minutes"

        # Biểu đồ
        data = top_artists(self.df, n, by).sort_values()
        ax = self.art_ax
        ax.clear()
        ax.barh(data.index, data.values)
        ax.set_title(f"Top {n} nghệ sĩ")
        ax.set_xlabel("Số lượt" if by == "plays" else "Phút nghe")
        self.art_fig.tight_layout()
        self.art_canvas.draw()

        # Bảng bài hát
        for row in self.track_table.get_children():
            self.track_table.delete(row)
        for (track, artist), plays in top_tracks(self.df, n).items():
            self.track_table.insert("", "end", values=(track, artist, plays))
    def apply_filter(self):
        if self.df_all is None:
            messagebox.showinfo("Thông báo", "Hãy chọn thư mục dữ liệu trước.")
            return
        try:
            sub = filter_by_date(self.df_all,
                                 self.start_entry.get().strip(),
                                 self.end_entry.get().strip())
        except Exception:
            messagebox.showerror("Lỗi", "Ngày không hợp lệ. Nhập dạng YYYY-MM-DD, ví dụ 2025-06-01.")
            return
        if sub.empty:
            messagebox.showwarning("Không có dữ liệu", "Khoảng ngày này không có lượt nghe nào.")
            return
        self.df = sub
        self.refresh_all()

    def reset_filter(self):
        if self.df_all is None:
            return
        self.start_entry.delete(0, "end")
        self.end_entry.delete(0, "end")
        self.df = self.df_all
        self.refresh_all()

    def refresh_all(self):
        self.status.config(text=f"Đang xem {len(self.df)} / {len(self.df_all)} lượt nghe")
        self.show_overview()
        self.draw_time_chart()
        self.draw_artists()

if __name__ == "__main__":
    MusicApp().mainloop()