# 🚀 爆速Webスクレイピングツール

Bing検索を使用して上位5件のサイトを高速でスクレイピングし、テキストと画像URLを抽出するPythonツールです。

## 📋 特徴

- **🔍 Bing検索統合**: キーワードで自動的に上位5件のサイトを取得
- **⚡ 高速並列処理**: 非同期処理で複数サイトを同時スクレイピング
- **📝 テキスト抽出**: HTMLを整形されたテキストに変換
- **🖼️ 画像URL収集**: ページ内の全画像URLを自動収集
- **💾 ファイル出力**: 結果を.txtファイルで保存
- **🤖 AI連携対応**: JSON形式でのデータ出力

## 📦 必要なパッケージ

```bash
pip install -r requirements.txt
```

追加でGUI版を使用する場合:
```bash
pip install streamlit pandas
```

## 🚀 使い方

### 1. コマンドライン版

```bash
python fast_scraper.py
```

実行後、検索キーワードを入力するとスクレイピングが開始されます。

### 2. プログラマブルAPI

```python
from scraper_api import scrape_with_query, quick_scrape, get_all_image_urls

# 完全なスクレイピング（ファイル保存付き）
result = scrape_with_query("Python プログラミング")

# テキストのみ取得
text = quick_scrape("機械学習 入門")

# 画像URLのみ取得
images = get_all_image_urls("深層学習 画像認識")
```

### 3. GUI版（Streamlit）

```bash
streamlit run scraper_gui.py
```

ブラウザで`http://localhost:8501`にアクセスして使用します。

## 📁 出力ファイル構造

スクレイピング実行後、以下のファイルが生成されます：

```
scraping_results_[キーワード]_[タイムスタンプ]/
├── all_content.txt        # 全サイトのテキスト（メインファイル）
├── site_1_content.txt     # サイト1の個別テキスト
├── site_2_content.txt     # サイト2の個別テキスト
├── ...
├── all_image_urls.txt     # 全サイトの画像URLリスト
└── ai_data.json          # AI処理用のJSON形式データ
```

## 📊 出力ファイルの詳細

### all_content.txt
- 検索キーワード、実行日時、取得サイト数
- 各サイトのURL、取得日時、画像数
- 各サイトのテキストコンテンツ（最大50,000文字）

### site_*_content.txt
- 個別サイトの完全なテキストコンテンツ
- 文字数制限なし

### all_image_urls.txt
- 各サイトごとの画像URL一覧
- サイトURL、画像数、各画像のURL

### ai_data.json
- AI処理に適したJSON形式
- 各サイトのURL、コンテンツプレビュー（1000文字）
- 画像URL（最大20個）、統計情報

## 🔧 カスタマイズ

### 検索結果数の変更

`fast_scraper.py`の`search_bing`メソッドで`num_results`パラメータを変更:

```python
urls = self.search_bing(query, num_results=10)  # 10件取得
```

### タイムアウトの調整

`fetch_page_async`メソッドでタイムアウトを変更:

```python
timeout=aiohttp.ClientTimeout(total=30)  # 30秒に変更
```

## ⚠️ 注意事項

- スクレイピング対象サイトの利用規約を確認してください
- 過度なアクセスは避け、適切な間隔を設けてください
- robots.txtを尊重してください
- 取得したデータの利用は自己責任でお願いします

## 🐛 トラブルシューティング

### エラー: "No module named 'aiohttp'"
```bash
pip install aiohttp
```

### エラー: "Timeout"
- ネットワーク接続を確認
- タイムアウト値を増やす
- VPNやプロキシの設定を確認

### 検索結果が取得できない
- Bing検索のレート制限の可能性
- User-Agentを変更してみる
- 時間を空けて再実行

## 📝 ライセンス

MIT License

## 🤝 貢献

プルリクエストを歓迎します！

## 📧 サポート

問題が発生した場合は、Issueを作成してください。