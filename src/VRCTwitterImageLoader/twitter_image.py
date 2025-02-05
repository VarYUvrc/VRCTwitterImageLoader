# src/VRCTwitterImageLoader/twitter_image.py
import pandas as pd
from scripts.html_render import save_html_as_png
from scripts.user_config import VTILSettings


settings = VTILSettings()

file_path = "src/VRCTwitterImageLoader/data/urls_orig_date.csv"
image_num = settings.IMAGE_NUM

df_urls_date = pd.read_csv(file_path)
df_urls_date = df_urls_date.dropna(subset=["url"])

if settings.IS_RANDOM:
    # ランダム抽出
    df_selected_urls = (
        df_urls_date["url"]
        .drop_duplicates()
        .sample(n=image_num, replace=False)
        .sort_index(ascending=True)
    )
else:
    # 新着順で抽出
    df_selected_urls = (
        df_urls_date.sort_values(by="date", ascending=False)["url"]
        .drop_duplicates()
        .head(image_num)
    )

list_selected_urls = df_selected_urls.tolist()

# URL失効時の確認用ログ
print("取得したツイートURL:")
print(list_selected_urls)

# レンダリング
save_html_as_png(list_selected_urls)
