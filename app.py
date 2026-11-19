import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(16, 4))

top_artists(df, 10).sort_values().plot(kind="barh", ax=axes[0])
axes[0].set_title("Top 10 nghệ sĩ (phút nghe)")
axes[0].set_xlabel("Phút")
axes[0].set_ylabel("")

plays_by_hour(df).plot(kind="bar", ax=axes[1])
axes[1].set_title("Số lượt nghe theo giờ")
axes[1].set_xlabel("Giờ trong ngày")
axes[1].set_ylabel("Số lượt")

plays_by_weekday(df).plot(kind="bar", ax=axes[2])
axes[2].set_title("Số lượt nghe theo thứ")
axes[2].set_xlabel("")
axes[2].tick_params(axis="x", rotation=45)

plt.tight_layout()
plt.show()