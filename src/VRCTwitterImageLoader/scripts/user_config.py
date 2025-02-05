from pydantic_settings import BaseSettings


class VTILSettings(BaseSettings):
    # X投稿URL取得フローの設定値
    X_HASHTAG_STR: str = "#Quest散歩"  # 収集対象のハッシュタグ
    N_DAYS: int = 5  # n日前までのツイートを検索(無料プランは最大7)
    MAX_RESULTS: int = 30  # URLを取得する最大数(無料プランは10から50)

    # 画像配信フローの設定値
    IMAGE_NUM: int = 10  # 配信画像枚数
    IS_RANDOM: bool = (
        True  # リストからランダムで投稿を選ぶ(True)か新着順に選ぶ(False)か
    )
    CLIP_WIDTH: int = 512  # 配信画像の横幅 (px)
    CLIP_HEIGHT: int = 786  # 配信画像の縦幅 (px)
    MAX_ATTEMPTS: int = 4  # レンダリング失敗後の最大試行数
