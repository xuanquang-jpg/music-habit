import json
from pathlib import Path
import pandas as pd
def load_history(folder):
    """Đọc tất cả file lịch sử nghe nhạc trong folder, trả về 1 DataFrame."""
    folder = Path(folder)

    # Account data (1 năm): StreamingHistory_music_*.json
    files = sorted(folder.rglob("StreamingHistory_music*.json"))
    extended = False

    # Nếu không có thì thử bản Extended
    if not files:
        files = sorted(folder.rglob("Streaming_History_Audio*.json"))
        extended = True

    if not files:
        raise FileNotFoundError(f"Không tìm thấy file lịch sử nghe trong {folder}")
 
    frames = []
    for f in files:
        with open(f, encoding="utf-8") as fp:
            frames.append(pd.DataFrame(json.load(fp)))
    df = pd.concat(frames, ignore_index=True)

    # Bản Extended dùng tên cột khác, đổi về cùng một dạng
    if extended:
        df = df.rename(columns={
            "ts": "endTime",
            "master_metadata_album_artist_name": "artistName",
            "master_metadata_track_name": "trackName",
            "ms_played": "msPlayed",
        })
        df = df[["endTime", "artistName", "trackName", "msPlayed"]]

    return df
WEEKDAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]


def clean_history(df):
    """Làm sạch bảng lịch sử nghe và thêm các cột phục vụ phân tích."""
    df = df.copy()

    # 1. Đổi chữ thành thời gian (UTC), rồi chuyển sang giờ Việt Nam
    df["endTime"] = pd.to_datetime(df["endTime"], utc=True)
    df["endTime"] = df["endTime"].dt.tz_convert("Asia/Ho_Chi_Minh")

    # 2. Bỏ dòng thiếu tên bài hoặc nghệ sĩ, bỏ dòng trùng
    df = df.dropna(subset=["artistName", "trackName"])
    df = df.drop_duplicates()

    # 3. Thêm các cột mới
    df["minutes"] = df["msPlayed"] / 60000
    df["date"] = df["endTime"].dt.date
    df["hour"] = df["endTime"].dt.hour
    df["weekday"] = df["endTime"].dt.dayofweek.map(lambda i: WEEKDAYS[i])
    df["month"] = df["endTime"].dt.strftime("%Y-%m")
    df["is_short"] = df["msPlayed"] < 30000   # nghe dưới 30 giây

    # 4. Sắp xếp theo thời gian
    df = df.sort_values("endTime").reset_index(drop=True)
    return df
def top_artists(df, n=10, by="minutes"):
    """Top n nghệ sĩ. by='minutes' (tổng phút nghe) hoặc 'plays' (số lượt)."""
    if by == "plays":
        result = df.groupby("artistName").size()
    else:
        result = df.groupby("artistName")["minutes"].sum()
    return result.sort_values(ascending=False).head(n)


def top_tracks(df, n=10):
    """Top n bài hát theo số lượt nghe."""
    return (df.groupby(["trackName", "artistName"]).size()
              .sort_values(ascending=False).head(n))


def plays_by_hour(df):
    """Số lượt nghe theo từng giờ trong ngày (đủ 24 giờ)."""
    return df.groupby("hour").size().reindex(range(24), fill_value=0)


def plays_by_weekday(df):
    """Số lượt nghe theo thứ trong tuần, đúng thứ tự Thứ 2 → Chủ nhật."""
    return df.groupby("weekday").size().reindex(WEEKDAYS, fill_value=0)


def minutes_by_month(df):
    """Tổng số phút nghe mỗi tháng."""
    return df.groupby("month")["minutes"].sum()


def summary(df):
    """Các con số tổng quan cho trang Tổng quan."""
    return {
        "total_plays": len(df),
        "total_hours": df["minutes"].sum() / 60,
        "unique_artists": df["artistName"].nunique(),
        "unique_tracks": df["trackName"].nunique(),
        "avg_per_day": df.groupby("date")["minutes"].sum().mean(),
    }
def filter_by_date(df, start=None, end=None):
    """Lọc theo khoảng ngày. start, end là chuỗi 'YYYY-MM-DD' (có thể bỏ trống)."""
    result = df
    if start:
        result = result[result["date"] >= pd.to_datetime(start).date()]
    if end:
        result = result[result["date"] <= pd.to_datetime(end).date()]
    return result