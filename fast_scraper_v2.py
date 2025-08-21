#!/usr/bin/env python3
"""
高速Webスクレイピングツール v2
直接URLを指定してスクレイピング、またはGoogle検索APIを使用
"""

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
import html2text
import json
import time
from datetime import datetime
import re
import os
from urllib.parse import urljoin, urlparse, quote, unquote
from typing import List, Dict, Tuple

class FastWebScraperV2:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.body_width = 0
        
    def search_google_custom(self, query: str, num_results: int = 5) -> List[str]:
        """Google検索の代替実装（DuckDuckGoを使用）"""
        print(f"\n🔍 Web検索実行中: '{query}'")
        
        # DuckDuckGo HTML版を使用
        search_url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
        
        try:
            response = requests.get(search_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            urls = []
            # DuckDuckGoの検索結果を取得
            for result in soup.find_all('a', class_='result__a'):
                url = result.get('href')
                if url and url.startswith('http'):
                    urls.append(url)
                    if len(urls) >= num_results:
                        break
            
            # 代替セレクター
            if len(urls) < num_results:
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('http') and 'duckduckgo.com' not in href:
                        if href not in urls:
                            urls.append(href)
                            if len(urls) >= num_results:
                                break
            
            print(f"✅ {len(urls)}件のURLを取得しました")
            return urls[:num_results]
            
        except Exception as e:
            print(f"⚠️ Web検索で問題発生: {str(e)}")
            # フォールバック: サンプルURLを提供
            print("📌 サンプルURLを使用します")
            return self.get_sample_urls()
    
    def get_sample_urls(self) -> List[str]:
        """テスト用のサンプルURL"""
        return [
            "https://www.python.org/",
            "https://docs.python.org/3/tutorial/",
            "https://realpython.com/",
            "https://www.w3schools.com/python/",
            "https://github.com/python/cpython"
        ]
    
    async def fetch_page_async(self, session: aiohttp.ClientSession, url: str) -> Tuple[str, str, List[str]]:
        """非同期でページを取得してコンテンツと画像URLを抽出"""
        try:
            # タイムアウトを短く設定
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.get(url, headers=self.headers, timeout=timeout, ssl=False) as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    # BeautifulSoupでパース
                    soup = BeautifulSoup(html_content, 'lxml')
                    
                    # スクリプトとスタイルタグを削除
                    for script in soup(["script", "style", "noscript"]):
                        script.decompose()
                    
                    # タイトルを取得
                    title = soup.find('title')
                    title_text = title.text if title else "No Title"
                    
                    # メタディスクリプションを取得
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    description = meta_desc.get('content', '') if meta_desc else ''
                    
                    # 本文テキストを取得
                    # mainタグ、articleタグ、またはbodyタグから取得
                    main_content = soup.find('main') or soup.find('article') or soup.find('body')
                    if main_content:
                        text_content = self.html_converter.handle(str(main_content))
                    else:
                        text_content = self.html_converter.handle(str(soup))
                    
                    # テキストの前にタイトルと説明を追加
                    full_content = f"# {title_text}\n\n"
                    if description:
                        full_content += f"**説明**: {description}\n\n"
                    full_content += text_content
                    
                    # 画像URLを抽出
                    image_urls = []
                    for img in soup.find_all('img'):
                        img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                        if img_url:
                            # 相対URLを絶対URLに変換
                            absolute_url = urljoin(url, img_url)
                            if absolute_url.startswith('http'):
                                # 画像のalt textも取得
                                alt_text = img.get('alt', '')
                                image_info = {'url': absolute_url, 'alt': alt_text}
                                image_urls.append(absolute_url)
                    
                    # og:imageメタタグからも画像を取得
                    og_image = soup.find('meta', property='og:image')
                    if og_image and og_image.get('content'):
                        og_img_url = urljoin(url, og_image['content'])
                        if og_img_url not in image_urls:
                            image_urls.append(og_img_url)
                    
                    return url, full_content, image_urls
                else:
                    return url, f"Error: HTTP {response.status}", []
                    
        except asyncio.TimeoutError:
            return url, "Error: Timeout (10秒)", []
        except Exception as e:
            return url, f"Error: {str(e)}", []
    
    async def scrape_urls_async(self, urls: List[str]) -> List[Dict]:
        """複数のURLを非同期で高速スクレイピング"""
        print(f"\n⚡ {len(urls)}件のサイトを並列スクレイピング中...")
        
        results = []
        # コネクターの設定を調整
        connector = aiohttp.TCPConnector(limit=5, force_close=True)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [self.fetch_page_async(session, url) for url in urls]
            responses = await asyncio.gather(*tasks)
            
            for i, (url, content, images) in enumerate(responses, 1):
                status = "✅" if not content.startswith("Error:") else "⚠️"
                print(f"  [{i}/{len(urls)}] {status} {urlparse(url).netloc}")
                results.append({
                    'url': url,
                    'content': content,
                    'images': images,
                    'scraped_at': datetime.now().isoformat()
                })
        
        return results
    
    def save_results(self, query: str, results: List[Dict]):
        """スクレイピング結果をファイルに保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = re.sub(r'[^\w\s-]', '', query)[:50]
        
        # 出力ディレクトリを作成
        output_dir = f"scraping_results_{safe_query}_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        
        # メイン結果ファイル（全サイトのテキスト）
        main_file = os.path.join(output_dir, "all_content.txt")
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(f"🚀 スクレイピング結果\n")
            f.write(f"検索キーワード: {query}\n")
            f.write(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"取得サイト数: {len(results)}\n")
            f.write("="*80 + "\n\n")
            
            success_count = sum(1 for r in results if not r['content'].startswith("Error:"))
            f.write(f"成功: {success_count}件 / 失敗: {len(results) - success_count}件\n")
            f.write("="*80 + "\n\n")
            
            for i, result in enumerate(results, 1):
                f.write(f"\n{'='*80}\n")
                f.write(f"サイト {i}: {result['url']}\n")
                f.write(f"取得日時: {result['scraped_at']}\n")
                f.write(f"画像数: {len(result['images'])}\n")
                f.write("-"*80 + "\n\n")
                
                if result['content'].startswith("Error:"):
                    f.write(f"⚠️ {result['content']}\n")
                else:
                    f.write(result['content'][:50000])  # 最大50000文字まで
                    if len(result['content']) > 50000:
                        f.write("\n\n[... コンテンツが長すぎるため省略 ...]\n")
                f.write("\n\n")
        
        # 個別サイトごとのファイル
        for i, result in enumerate(results, 1):
            if not result['content'].startswith("Error:"):
                site_file = os.path.join(output_dir, f"site_{i}_content.txt")
                with open(site_file, 'w', encoding='utf-8') as f:
                    f.write(f"URL: {result['url']}\n")
                    f.write(f"取得日時: {result['scraped_at']}\n")
                    f.write("="*80 + "\n\n")
                    f.write(result['content'])
        
        # 画像URLリストファイル
        images_file = os.path.join(output_dir, "all_image_urls.txt")
        with open(images_file, 'w', encoding='utf-8') as f:
            f.write(f"🖼️ 画像URL一覧\n")
            f.write(f"検索キーワード: {query}\n")
            f.write("="*80 + "\n\n")
            
            total_images = 0
            for i, result in enumerate(results, 1):
                if result['images']:
                    f.write(f"\nサイト {i}: {result['url']}\n")
                    f.write(f"画像数: {len(result['images'])}\n")
                    f.write("-"*40 + "\n")
                    
                    for j, img_url in enumerate(result['images'], 1):
                        f.write(f"{j}. {img_url}\n")
                    total_images += len(result['images'])
                    f.write("\n")
            
            f.write(f"\n総画像数: {total_images}\n")
        
        # AI用のJSON形式でも保存
        ai_data_file = os.path.join(output_dir, "ai_data.json")
        ai_data = {
            'query': query,
            'scraped_at': datetime.now().isoformat(),
            'total_sites': len(results),
            'successful_sites': sum(1 for r in results if not r['content'].startswith("Error:")),
            'results': []
        }
        
        for result in results:
            if not result['content'].startswith("Error:"):
                ai_data['results'].append({
                    'url': result['url'],
                    'content_preview': result['content'][:1000],  # プレビューのみ
                    'full_content_length': len(result['content']),
                    'image_urls': result['images'][:20],  # 最大20個の画像URL
                    'total_images': len(result['images']),
                    'scraped_at': result['scraped_at']
                })
        
        with open(ai_data_file, 'w', encoding='utf-8') as f:
            json.dump(ai_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📁 結果を保存しました: {output_dir}/")
        print(f"  - all_content.txt: 全サイトのテキスト")
        print(f"  - site_*_content.txt: 個別サイトのテキスト")
        print(f"  - all_image_urls.txt: 全画像URLリスト")
        print(f"  - ai_data.json: AI処理用データ")
        
        return output_dir
    
    def scrape(self, query: str = None, urls: List[str] = None):
        """メインのスクレイピング処理"""
        start_time = time.time()
        
        print("\n" + "="*80)
        print("🚀 高速Webスクレイピング開始 v2")
        print("="*80)
        
        # URLリストの取得
        if urls:
            # 直接URLが指定された場合
            print(f"📌 指定された{len(urls)}件のURLを使用")
        elif query:
            # 検索クエリが指定された場合
            urls = self.search_google_custom(query, num_results=5)
            if not urls:
                print("❌ 検索結果が見つかりませんでした")
                return None
        else:
            # デフォルトのサンプルURLを使用
            print("📌 サンプルURLを使用します")
            urls = self.get_sample_urls()
            query = "Python Programming Sample"
        
        print(f"\n取得するURL:")
        for i, url in enumerate(urls, 1):
            print(f"  {i}. {url}")
        
        # 非同期でスクレイピング実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(self.scrape_urls_async(urls))
        loop.close()
        
        # 結果を保存
        output_dir = self.save_results(query or "Direct URLs", results)
        
        elapsed_time = time.time() - start_time
        print(f"\n⏱️ 処理時間: {elapsed_time:.2f}秒")
        print(f"✨ スクレイピング完了！")
        
        return output_dir

def main():
    """メイン実行関数"""
    print("="*80)
    print("🔥 爆速Webスクレイピングツール v2")
    print("="*80)
    print("\n機能:")
    print("  - Web検索または直接URL指定でスクレイピング")
    print("  - 並列処理で高速スクレイピング")
    print("  - テキストコンテンツと画像URLを抽出")
    print("  - 結果を整理してファイル保存")
    print("  - AI処理用のJSON形式でも出力")
    print("\n")
    
    # 使用方法を選択
    print("使用方法を選択してください:")
    print("1. キーワード検索でスクレイピング")
    print("2. URL直接指定でスクレイピング")
    print("3. サンプルURLでテスト実行")
    
    choice = input("\n選択 (1/2/3): ").strip()
    
    scraper = FastWebScraperV2()
    
    if choice == "1":
        # 検索キーワードを入力
        query = input("🔍 検索キーワードを入力してください: ").strip()
        if not query:
            print("❌ キーワードが入力されていません")
            return
        output_dir = scraper.scrape(query=query)
    
    elif choice == "2":
        # URL直接入力
        print("URLを入力してください（複数の場合は改行で区切る、空行で終了）:")
        urls = []
        while True:
            url = input().strip()
            if not url:
                break
            if url.startswith("http"):
                urls.append(url)
        
        if not urls:
            print("❌ URLが入力されていません")
            return
        output_dir = scraper.scrape(urls=urls)
    
    else:
        # サンプル実行
        print("📌 サンプルURLでテスト実行します...")
        output_dir = scraper.scrape()
    
    if output_dir:
        print(f"\n📊 結果サマリー:")
        print(f"  出力ディレクトリ: {output_dir}")
        print(f"\n💡 ヒント: AI処理には ai_data.json ファイルを使用してください")

if __name__ == "__main__":
    main()