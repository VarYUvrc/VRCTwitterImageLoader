# src/VRCTwitterImageLoader/x_auto_get_post_urls.py
import os
import csv
import re
import requests
import time
from datetime import datetime, timedelta, timezone
from typing import Tuple, Any

from scripts.user_config import VTILSettings


# スクリプトのあるディレクトリを基準にしてパスを設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # スクリプトのディレクトリ
CSV_FILE_PATH = os.path.join(BASE_DIR, "data", "urls_orig_date.csv")


def ensure_data_directory_exists(csv_file_path: str) -> None:
    """CSVファイルのディレクトリが存在しない場合は作成する

    Args:
        csv_file_path (str): CSVファイルのフルパス
    """
    dir_path = os.path.dirname(csv_file_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def extract_tweet_id(url: str) -> str:
    """URLからツイートID（数値部分）を抽出する.

    Args:
        url (str): ツイートのURL.

    Returns:
        str: ツイートID（数値部分）
    """
    match = re.search(r"(\d+)$", url)
    return match.group(1) if match else ""


def create_url(
    x_hashtag_str: str, n_days: int, max_results: int
) -> Tuple[str, dict[str, Any]]:
    """Twitter API リクエスト用の URL とパラメータを作成する

    今回は expansions と user.fields を追加して投稿者のユーザー名を取得する

    Args:
        x_hashtag_str (str): 検索に使用するハッシュタグ文字列
        n_days (int): 過去 n 日間のツイートを取得するための日数
        max_results (int): 取得する最大件数

    Returns:
        Tuple[str, dict[str, Any]]: リクエストURL とパラメータの辞書
    """
    url = "https://api.twitter.com/2/tweets/search/recent"

    start_time = (
        (datetime.now(timezone.utc) - timedelta(days=n_days))
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )

    # リツイートを除外するクエリを作成
    query = f"{x_hashtag_str} -is:retweet"
    params = {
        "query": query,
        "tweet.fields": "created_at,author_id",
        "max_results": max_results,
        "start_time": start_time,
        # expansions を指定して投稿者情報を取得
        "expansions": "author_id",
        "user.fields": "username",
    }
    return url, params


def connect_to_endpoint(
    url: str, params: dict[str, Any], token: str, max_retries: int = 3
) -> dict[str, Any]:
    """Twitter API エンドポイントにリクエストを送り、結果の JSON を返す

    Args:
        url (str): APIエンドポイントのURL
        params (dict[str, Any]): リクエストパラメータの辞書
        token (str): Bearer Token
        max_retries (int, optional): 最大リトライ回数. Defaults to 3.

    Returns:
        dict[str, Any]: APIからのレスポンスのJSON辞書

    Raises:
        Exception: レスポンスコードが200以外の場合、または最大リトライ回数を超えた場合
    """
    headers = {"Authorization": f"Bearer {token}", "User-Agent": "v2RecentSearchPython"}
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            retry_after = int(response.headers.get("retry-after", "60"))
            print(
                f"Rate limit hit. Sleeping for {retry_after} seconds. Attempt {attempt+1} of {max_retries}."
            )
            time.sleep(retry_after)
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")
    raise Exception("Max retries exceeded due to rate limiting.")


def fetch_tweets(
    token: str, x_hashtag_str: str, n_days: int, max_results: int
) -> list[dict[str, str]]:
    """Twitter API からツイート情報を取得し、URL と日付（YYYY-MM-DD）のリストを返す

    ツイート情報取得時に expansions で投稿者情報も取得することで、各ツイートの URL を
    「https://x.com/ユーザー名/status/ツイートID」の形式で組み立てる。また、作成日時を
    日本時間（UTC+9）に補正した日付で記録する。

    Args:
        token (str): Bearer Token
        x_hashtag_str (str): 検索に使用するハッシュタグ文字列
        n_days (int): 過去 n 日間のツイートを取得するための日数
        max_results (int): 取得する最大件数

    Returns:
        list[dict[str, str]]: ツイートの URL と作成日（日本時間）の辞書のリスト
    """
    url, params = create_url(x_hashtag_str, n_days, max_results)
    json_response = connect_to_endpoint(url, params, token)
    tweets_list = []

    # 取得した投稿者情報（ユーザー名）のマッピングを作成
    user_mapping = {}
    if "includes" in json_response and "users" in json_response["includes"]:
        for user in json_response["includes"]["users"]:
            user_mapping[user["id"]] = user["username"]

    if "data" in json_response:
        # 作成日の降順にソート
        tweets = sorted(
            json_response["data"], key=lambda x: x["created_at"], reverse=True
        )
        for tweet in tweets:
            tweet_id = tweet["id"]
            # 投稿者のユーザー名が取得できた場合はその名前を用いてURLを組み立てる
            username = user_mapping.get(tweet.get("author_id", ""), "")
            if username:
                tweet_url = f"https://x.com/{username}/status/{tweet_id}"
            else:
                tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"
            # UTCの日時文字列を datetime オブジェクトに変換
            dt_utc = datetime.fromisoformat(tweet["created_at"].replace("Z", "+00:00"))
            # 日本時間（UTC+9）に変換
            dt_jst = dt_utc.astimezone(timezone(timedelta(hours=9)))
            tweet_date = dt_jst.strftime("%Y-%m-%d")
            tweets_list.append({"url": tweet_url, "date": tweet_date})
    return tweets_list


def read_csv_file(csv_file_path: str) -> list[dict[str, str]]:
    """CSV ファイルを読み込み、各行を辞書のリストとして返す

    Args:
        csv_file_path (str): CSVファイルのフルパス

    Returns:
        list[dict[str, str]]: CSVの各行（url, date）の辞書リスト
    """
    rows = []
    if os.path.exists(csv_file_path):
        with open(csv_file_path, "r", encoding="utf-8", newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                rows.append(row)
    return rows


def write_csv_file(csv_file_path: str, rows: list[dict[str, str]]) -> None:
    """CSV ファイルにデータを書き出す

    Args:
        csv_file_path (str): CSVファイルのフルパス
        rows (list[dict[str, str]]): 書き出す各行の辞書リスト（フィールド名: url, date）
    """
    with open(csv_file_path, "w", encoding="utf-8", newline="") as csvfile:
        fieldnames = ["url", "date"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def update_csv_with_new_tweets(
    new_tweets: list[dict[str, str]], csv_file_path: str
) -> None:
    """新規取得したツイート情報を、既存の CSV に追加（重複なし）

    既存の CSV にすでに記録済みのツイートID（URL末尾の数値部分）と重複しないものだけを追加する

    Args:
        new_tweets (list[dict[str, str]]): 新たに取得したツイート情報（url, date）
        csv_file_path (str): CSVファイルのフルパス
    """
    ensure_data_directory_exists(csv_file_path)

    existing_rows = read_csv_file(csv_file_path)

    # 既存のツイートIDを取得（URLの末尾の数値部分）
    existing_tweet_ids = {extract_tweet_id(row["url"]) for row in existing_rows}

    # 既存にない新規ツイートのみを抽出
    unique_new_tweets = [
        tweet
        for tweet in new_tweets
        if extract_tweet_id(tweet["url"]) not in existing_tweet_ids
    ]

    # 新規ツイートを上部に追加
    updated_rows = unique_new_tweets + existing_rows
    write_csv_file(csv_file_path, updated_rows)
    print(f"Collected URLs: {new_tweets}")
    print(f"Extracted Unique URLs: {unique_new_tweets}")
    print(
        f"Updated CSV file at {csv_file_path} with {len(unique_new_tweets)} new tweets."
    )


def save_hashtag_post_info_to_csv(
    token: str,
    x_hashtag_str: str,
    n_days: int,
    max_results: int,
    csv_file_path: str,
) -> None:
    """指定のハッシュタグ、期間、件数でツイートを取得し、CSV ファイルに更新する

    Args:
        token (str): Bearer Token
        x_hashtag_str (str): 検索に使用するハッシュタグ文字列
        n_days (int, optional): 過去 n 日間のツイートを取得. Defaults to 3.
        max_results (int, optional): 取得する最大件数. Defaults to 50.
        csv_file_path (str, optional): CSVファイルのフルパス. Defaults to CSV_FILE_PATH.
    """
    new_tweets = fetch_tweets(token, x_hashtag_str, n_days, max_results)
    update_csv_with_new_tweets(new_tweets, csv_file_path)


if __name__ == "__main__":
    # 環境変数 "X_BEARER_TOKEN" からトークンを取得
    token = os.environ.get("X_BEARER_TOKEN")
    if token is None:
        raise Exception("環境変数 X_BEARER_TOKEN が設定されていません。")

    settings = VTILSettings()

    save_hashtag_post_info_to_csv(
        token=token,
        x_hashtag_str=settings.X_HASHTAG_STR,
        n_days=settings.N_DAYS,
        max_results=settings.MAX_RESULTS,
        csv_file_path=CSV_FILE_PATH,
    )
