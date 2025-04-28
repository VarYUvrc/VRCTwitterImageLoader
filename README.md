# ⚡️VRCTwitterImageLoader

X (Twitter)の投稿のうち、特定のハッシュタグの投稿をリストにまとめ、そのリストから任意の数の投稿を選び、GitHub Pagesに画像として自動で配信するシステムです。

このGitHub Pagesの画像URLは固定のため、例えばVRChatのImage Loadingの仕組みと組み合わせることで、ワールド内でXの投稿を眺めることが可能です。

使用例: https://x.com/Ring_Say_rip/status/1731264158828753358

>[!NOTE]
> **すべての動作はGitHub上で完結しているため、サーバを個人で建てる必要がありません。**
> 
> **2025年4月現在、無料ですべてのプログラムが動作します。**

- VRChatでこのシステムの画像を読み込むのは簡単ですが、前提としてワールド制作の知識が必要です。
    - Image Loadingについて: [Image Loading | VRChat](https://creators.vrchat.com/worlds/udon/image-loading/)
      - [VRChat公式のサンプル](https://creators.vrchat.com/worlds/examples/image-loading)には、`SlideshowFrame`プレハブが用意されています。
      - Udon SharpでImage Loadingを実装する一例として、namanonamako 氏のアセット [【無料】WebPhotoStand【VRChat】](https://namanonamako.booth.pm/items/4702922)もおすすめです。

## 👷必要なもの

どちらも無料アカウントで構いません（ただし実行頻度の上限がそれぞれ存在します）。
- GitHubアカウント
    - 設定ファイルの変更と定期実行を行うために必要です。
- Xアカウント
    - X開発者アカウント(後述)を発行するために必要です

## 👽️不要なもの

- プログラミングの知識
  - 不要です。ただし、このシステムによって取得した画像をVRChat内で表示するためには、前述のようなUdonの既製アセット or ご自身で作成したUdonシステム のどちらかが必要です。
- VSCode, Cursorなどのエディタ
  - 不要です。書き換えが必要な一部の箇所は、すべてGitHubのWeb UIだけで直接編集できます。

## 🧑‍💻使い方

### GitHub Actionsを用いた完全自動化

少しの操作が必要です。ほぼGitHubのUI上で行えます。
1. このプロジェクトをご自身のGitHubプロジェクトとしてForkしてください。
1. URLリストである[urls_orig_date.csv](src/VRCTwitterImageLoader/data/urls_orig_date.csv)ファイルの中身を自身の収集対象のXの投稿のURLに変更してください。
    - 動作するためには少なくとも10件の投稿が必要です。
    - 元の形式通り、ヘッダーに`url`列と`date`列の2列がカンマ区切りで必要です。
2. [user_config.py](src/VRCTwitterImageLoader/scripts/user_config.py)の`X_HASHTAG_STR`の値を収集対象のハッシュタグに変更してください。
    - 初期設定では`X_HASHTAG_STR = "#Quest散歩"`になっています。
3. [X開発者ページ](https://developer.twitter.com/en/portal/dashboard)にログイン(Freeアカウントでも可)し、BEARER TOKENを発行してください。
4. GitHub ActionsのRepository Secretsに4.で発行したTokenの値を保存してください。
    - 「Settings」→「Security」→「Actions」→「Repository secrets」セクションで、「New Repository secret」をクリック
        - Name: `X_BEARER_TOKEN`
        - Secret: Tokenの値（AAAA....）を貼り付け
    - 「Add secret」をクリック
5. 下記の操作で、リポジトリのGitHub ActionsにPull Requestの権限を付与してください。
    - 「Settings」→「Actions」→「General」→ 「Workflow permissions」セクションで以下を設定:
        - "Read and write permissions"を選択
        - "Allow GitHub Actions to create and approve pull requests"にチェック
        - 「Save」をクリック
6. 下記の操作で、リポジトリのGitHub PagesがActionsからデプロイされるように変更してください。
    - 「Settings」→「Pages」セクションで以下を設定:
        - 「Build and deployment」→「Source」を"Github Actions"に変更
        - 「Settings」→「Environments」に"github-pages"という環境変数が自動的に作成されていることを確認
7. ここまでの変更がmasterブランチに反映(push)されていれば完了です。初期設定では、毎週2回水曜と土曜の3:00に[urls_orig_date.csv](src/VRCTwitterImageLoader/data/urls_orig_date.csv)の中身の更新が提案され、毎日4:00にその中からランダムで10件の投稿が下記のURLに配信されます。
    - `https://{GitHubアカウント名}.github.io/VRCTwitterImageLoader/images/screenshot_0.png`
    - `https://{GitHubアカウント名}.github.io/VRCTwitterImageLoader/images/screenshot_1.png`
    - `https://{GitHubアカウント名}.github.io/VRCTwitterImageLoader/images/screenshot_2.png`
    - ...
    - `https://{GitHubアカウント名}.github.io/VRCTwitterImageLoader/images/screenshot_9.png`

        - 画像はスクリプト実行ごとに上書き変更されますが、画像URLは常に固定です。
            - 画像一覧のサンプル: https://varyuvrc.github.io/VRCTwitterImageLoader/
        - 画像数を変更したい場合は、[user_config.py](src/VRCTwitterImageLoader/scripts/user_config.py)の`IMAGE_NUM`の値と、[index.html](src/VRCTwitterImageLoader/pages/index.html)の中身を変更してください。
8. 定時実行を待たずに[.github/workflows](.github/workflows)内のCI/CDスクリプトをGitHub Webの"Actions"ページで手動実行することも可能です。
    - リポジトリのActionsタブに移動
    - 「All workflows」の"Update URLs list"か"Upload Random Images"をクリック
    - 「Run workflow」タブ内の「Run workflow」ボタンをクリックし実行を待つ
    - 緑色のアイコン（成功）になればOK
        - 赤色のアイコン（失敗）になった場合は、上記設定を見直してください。
        - それでも直らない場合は不具合報告（このページ下部）してください。
    - "Upload Random Images"実行に成功すると、`https://{GitHubアカウント名}.github.io/VRCTwitterImageLoader/`にデプロイされたGitHub PagesにXの投稿画像が配信されます。
9. VRChat UdonのImage Loadingを使用して上記URLから画像を取得することで、ワールド内で毎日更新されるテクスチャとして扱うことができます。画像サイズは 512 x 786 pxです。
10. 「[urls_orig_date.csv](src/VRCTwitterImageLoader/data/urls_orig_date.csv)の中身の更新」はPull Requestとして作成され、自動的にMergeされます。
    - もしMerge済の特定のURLを削除したい場合は、CSVファイルをGitHubのWeb UI上で"Edit this file"ボタンから直接編集してください。

### 🔧オプション設定

1. 初期設定では投稿リストから**ランダム抽出**で画像化する投稿が選ばれますが、**新着順**に投稿を選出することも可能です。
   - [user_config.py](src/VRCTwitterImageLoader/scripts/user_config.py)の`IS_RANDOM`を`False`に書き換えると新着順になります。

2. 同じURLに対する画像の差し替え頻度は初期設定では1日一回（日替わり）ですが、もっと短いスパンに変更することも可能です。
   - [upload_randam_images.yml](.github/workflows/upload_randam_images.yml)の`schedule:`のcronを書き換えることで、例えば3時間ごとの更新にもできます。
       - 2025年2月現在、GitHub無料アカウントはGitHub Actionsの実行時間が2000分/月に制限されています。
       - このCI/CDの実行時間は3分程度のため、GitHub無料アカウントにおける最短実行間隔は約70分に1回だと考えられます。

3. Xの投稿をリストに収集する頻度と一回当たりの収集数は、Xの開発者アカウントのグレードに依存します。
   - 2025年2月現在、無料アカウントは100回&50件/月に制限されています。
   - [update_urls_list.yml](.github/workflows/update_urls_list.yml)の`schedule:`のcronと、[user_config.py](src/VRCTwitterImageLoader/scripts/user_config.py)の`N_DAYS`と`MAX_RESULTS`を書き換えることで頻度と収集数を調整できますが、前述の制限により無料アカウントではほとんど増やすことができません。
     - 投稿頻度の高いハッシュタグを漏れなく収集したい場合には、X開発者アカウントのアップグレードをおすすめします。
     - 今月の残りURL取得可能数は[X開発者ページのダッシュボード](https://developer.twitter.com/en/portal/dashboard)に表示されています。

## 🚧既知の不具合

HTMLレンダリングが失敗した状態で画像が保存されてしまう場合があります。現在は失敗を検知して4回まで再トライするようになっています。

## 🍻その他

不具合報告などの手順は[CONTRIBUTING](CONTRIBUTING.md)をご確認ください。

## 🧑‍💻ローカルで動作確認

> [!IMPORTANT]  
> **-----基本的にこれより下の操作を行う必要はありません。-----** 
> 
> ローカル環境で動作確認をしたい特殊な人向けの説明です。
> 
> ローカル実行の場合、GitHub Pagesへの画像アップロードは実行されません。

- 動作確認済の環境
    - Windows11
    - Ubuntu22.04
    - Ubuntu24.04 (WSL2)

このプロジェクトはPythonパッケージマネージャ[uv](https://docs.astral.sh/uv/)で管理されています。事前にインストールしてください。

```shell
$ git clone {ForkしたリポジトリのURL}.git
$ cd VRCTwitterImageLoader
$ uv sync

## 0. 日本語フォントのインストール
$ sudo apt-get update
$ sudo apt-get install -y fonts-ipafont

## 1. 画像取得テスト
### 事前にPlaywrgithのchromiumのインストールが必要
$ uv run playwright install chromium
$ uv run python src/VRCTwitterImageLoader/twitter_image.py
### playwrightのエラーが出た場合はエラー文に記載されている必須パッケージを別途インストールする)

## 2. 特定ハッシュタグの投稿URLの自動取得テスト
### 事前にX Developer APIのBEARER TOKENの環境変数への登録が必要
$ export X_BEARER_TOKEN=xxxxxxx
$ uv run python src/VRCTwitterImageLoader/x_auto_get_post_urls.py
```

```shell
# formatterを実行
$ uv run ruff format
# linterを実行
$ uv run ruff check --fix
```
