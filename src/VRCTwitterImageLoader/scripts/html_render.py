# src/VRCTwitterImageLoader/scripts/html_render.py
import os
import urllib.request
import json
from playwright.sync_api import sync_playwright


def get_tweet_embedcode(tweet_url):
    """
    指定されたツイートURLから埋め込みHTMLコードを取得
    """
    try:
        with urllib.request.urlopen(
            f"https://publish.twitter.com/oembed?url={tweet_url}"
        ) as url:
            data = json.loads(url.read().decode())
            return data["html"]
    except Exception as e:
        print(f"Error fetching embed code for {tweet_url}: {e}")
        return ""


def is_tweet_rendered(page):
    """
    ツイートのレンダリング状況を複数の条件で判定する：
    1. ツイートコンテナが存在し、レンダリング完了クラスを持っていること
    2. コンテナが表示されていること（高さ > 0）
    3. display: flexが設定されていること
    4. ドキュメントの読み込みが完了していること
    """
    try:
        debug_info = page.evaluate("""() => {
            const container = document.querySelector('.twitter-tweet');
            const iframe = document.querySelector('iframe[id^="twitter-widget"]');
            const widgetsScript = document.querySelector('script[src*="platform.twitter.com/widgets.js"]');
            
            // コンテナのスタイル情報を取得
            const containerStyle = container ? window.getComputedStyle(container) : null;
            const isRendered = container ? container.classList.contains('twitter-tweet-rendered') : false;
            const displayFlex = containerStyle ? containerStyle.display === 'flex' : false;
            
            // デバッグ情報の収集
            const info = {
                containerExists: !!container,
                containerHeight: container ? container.getBoundingClientRect().height : 0,
                iframeExists: !!iframe,
                isRendered: isRendered,
                displayFlex: displayFlex,
                htmlStructure: document.body.innerHTML,
                documentState: document.readyState,
                errors: [],
                networkRequests: performance.getEntriesByType('resource').map(entry => ({
                    name: entry.name,
                    duration: entry.duration,
                    status: entry.responseStatus
                }))
            };
            
            // エラーコンソールの取得
            if (window.console && console.error) {
                const originalError = console.error;
                const errors = [];
                console.error = (...args) => {
                    errors.push(args.join(' '));
                    originalError.apply(console, args);
                };
                // エラー情報を収集
                info.errors = errors;
            }
            
            return info;
        }""")

        # デバッグ情報の出力
        print("\n=== Tweet Rendering Debug Info ===")
        print(f"Container exists: {debug_info['containerExists']}")
        print(f"Container height: {debug_info['containerHeight']}px")
        print(f"iframe exists: {debug_info['iframeExists']}")
        print(f"Rendered class: {debug_info['isRendered']}")
        print(f"Display flex: {debug_info['displayFlex']}")
        print(f"Document state: {debug_info['documentState']}")

        if debug_info["networkRequests"]:
            print("\nNetwork Requests:")
            for req in debug_info["networkRequests"]:
                print(f"- {req['name']}: {req['duration']}ms (Status: {req['status']})")

        if debug_info["errors"]:
            print("\nErrors found:")
            for error in debug_info["errors"]:
                print(f"- {error}")

        print("\nHTML Structure:")
        print(
            debug_info["htmlStructure"][:500] + "..."
            if len(debug_info["htmlStructure"]) > 500
            else debug_info["htmlStructure"]
        )
        print("================================\n")

        # レンダリング成功の判定
        is_rendered = (
            debug_info["containerExists"]
            and debug_info["containerHeight"] > 0  # コンテナが表示されていること
            and debug_info["isRendered"]  # twitter-tweet-renderedクラスの存在
            and debug_info["displayFlex"]  # display: flexの確認
            and debug_info["documentState"] == "complete"
        )

        if not is_rendered:
            print("\nRendering failed due to:")
            if not debug_info["containerExists"]:
                print("- Tweet container not found")
            if debug_info["containerHeight"] <= 0:
                print("- Container height is zero")
            if not debug_info["isRendered"]:
                print("- Tweet not fully rendered")
            if not debug_info["displayFlex"]:
                print("- Display flex not set")
            if debug_info["documentState"] != "complete":
                print("- Document loading not complete")

        print(f"Rendering status: {'Success' if is_rendered else 'Failed'}")
        return is_rendered

    except Exception as e:
        print("Error evaluating tweet container:", e)
        return False


def save_html_as_png(
    converted_urls, file_name="src/VRCTwitterImageLoader/temp/tweet.html"
):
    """
    ツイート埋め込みHTMLをレンダリングしてPNG形式で保存
    ※もともとの待機タイミングを基本とし、レンダリング完了しているかを
      ツイートコンテナの高さで判定し、不具合の場合は再試行する。
    """
    clip_width = 512
    clip_height = 786
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        for index, render_url in enumerate(converted_urls):
            html_content = get_tweet_embedcode(render_url)
            if not html_content:
                print(f"ツイートの埋め込みコード取得に失敗しました: {render_url}")
                continue

            # HTMLファイルに書き出し
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(f"""
                <html>
                  <head>
                    <script async src="https://platform.twitter.com/widgets.js"></script>
                  </head>
                  <body>
                    {html_content}
                  </body>
                </html>
                """)

            # ローカルHTMLファイルのパスを生成
            local_url = "file://" + os.path.abspath(file_name)

            # レンダリング完了の再試行（最大4回、ブラウザの再起動を含む）
            max_attempts = 4
            attempt = 0
            rendered = False

            while attempt < max_attempts and not rendered:
                print(f"[{render_url}] Attempt {attempt+1} / {max_attempts}")

                if attempt > 0:
                    # 2回目以降の試行では、ブラウザを再起動
                    print("ブラウザを再起動して再試行します...")
                    browser.close()
                    browser = playwright.chromium.launch(headless=True)
                    context = browser.new_context()
                    page = context.new_page()

                page.goto(local_url, wait_until="networkidle")
                page.wait_for_timeout(3000)  # 初回待機（3秒）
                page.set_viewport_size({"width": clip_width, "height": clip_height})
                page.wait_for_timeout(8000)  # レンダリング完了待機（8秒）

                if is_tweet_rendered(page):
                    rendered = True
                    print("レンダリングが正常に完了しました。")
                else:
                    attempt += 1
                    if attempt < max_attempts:
                        print(
                            f"レンダリング未完了。再試行 {attempt}/{max_attempts} ..."
                        )

            if not rendered:
                print(
                    f"最大試行回数({max_attempts})に達しましたが、レンダリングが完了しませんでした: {render_url}"
                )

            # スクリーンショットの保存
            screenshot_path = (
                f"src/VRCTwitterImageLoader/pages/images/screenshot_{index}.png"
            )
            # 最大高さを制限し、超えるなら上寄せでトリミング
            page.screenshot(
                path=screenshot_path,
                clip={"x": 0, "y": 0, "width": clip_width, "height": clip_height} 
            )
            print(f"Screenshot saved to {screenshot_path}")

        browser.close()
