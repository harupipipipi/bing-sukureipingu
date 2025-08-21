#!/usr/bin/env python3
"""
高速Webスクレイピングツール
Bing検索を使用して上位5件のサイトをスクレイピング
テキストと画像URLを抽出してファイルに保存
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
from urllib.parse import urljoin, urlparse, quote
from typing import List, Dict, Tuple
import concurrent.futures
from functools import partial

class FastWebScraper:
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
        
    def search_bing(self, query: str, num_results: int = 5) -> List[str]:
        """Bing検索を実行して上位のURLを取得"""
        print(f"\n🔍 Bing検索実行中: '{query}'")
        
        # Bing検索URLを構築
        search_url = f"https://www.bing.com/search?q={quote(query)}&count={num_results * 2}"
        
        try:
            response = requests.get(search_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 検索結果のリンクを抽出
            urls = []
            
            # 通常の検索結果を取得
            for result in soup.find_all('li', class_='b_algo'):
                link = result.find('h2')
                if link and link.find('a'):
                    url = link.find('a').get('href')
                    if url and url.startswith('http'):
                        urls.append(url)
                        if len(urls) >= num_results:
                            break
            
            # 代替の検索結果セレクター
            if len(urls) < num_results:
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('http') and 'bing.com' not in href and 'microsoft.com' not in href:
                        if href not in urls:
                            urls.append(href)
                            if len(urls) >= num_results:
                                break
            
            print(f"✅ {len(urls)}件のURLを取得しました")
            return urls[:num_results]
            
        except Exception as e:
            print(f"❌ Bing検索エラー: {str(e)}")
            return []
    
    async def fetch_page_async(self, session: aiohttp.ClientSession, url: str) -> Tuple[str, str, List[str]]:
        """非同期でページを取得してコンテンツと画像URLを抽出"""
        try:
            async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    # BeautifulSoupでパース
                    soup = BeautifulSoup(html_content, 'lxml')
                    
                    # スクリプトとスタイルタグを削除
                    for script in soup(["script", "style", "noscript"]):
                        script.decompose()
                    
                    # テキストコンテンツを取得
                    text_content = self.html_converter.handle(str(soup))
                    
                    # 画像URLを抽出
                    image_urls = []
                    for img in soup.find_all('img'):
                        img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                        if img_url:
                            # 相対URLを絶対URLに変換
                            absolute_url = urljoin(url, img_url)
                            if absolute_url.startswith('http'):
                                image_urls.append(absolute_url)
                    
                    # og:imageメタタグからも画像を取得
                    og_image = soup.find('meta', property='og:image')
                    if og_image and og_image.get('content'):
                        og_img_url = urljoin(url, og_image['content'])
                        if og_img_url not in image_urls:
                            image_urls.append(og_img_url)
                    
                    return url, text_content, image_urls
                else:
                    return url, f"Error: HTTP {response.status}", []
                    
        except asyncio.TimeoutError:
            return url, "Error: Timeout", []
        except Exception as e:
            return url, f"Error: {str(e)}", []
    
    async def scrape_urls_async(self, urls: List[str]) -> List[Dict]:
        """複数のURLを非同期で高速スクレイピング"""
        print(f"\n⚡ {len(urls)}件のサイトを並列スクレイピング中...")
        
        results = []
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_page_async(session, url) for url in urls]
            responses = await asyncio.gather(*tasks)
            
            for i, (url, content, images) in enumerate(responses, 1):
                print(f"  [{i}/{len(urls)}] ✅ {urlparse(url).netloc}")
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
            f.write(f"スクレイピング結果\n")
            f.write(f"検索キーワード: {query}\n")
            f.write(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"取得サイト数: {len(results)}\n")
            f.write("="*80 + "\n\n")
            
            for i, result in enumerate(results, 1):
                f.write(f"\n{'='*80}\n")
                f.write(f"サイト {i}: {result['url']}\n")
                f.write(f"取得日時: {result['scraped_at']}\n")
                f.write(f"画像数: {len(result['images'])}\n")
                f.write("-"*80 + "\n\n")
                f.write(result['content'][:50000])  # 最大50000文字まで
                if len(result['content']) > 50000:
                    f.write("\n\n[... コンテンツが長すぎるため省略 ...]\n")
                f.write("\n\n")
        
        # 個別サイトごとのファイル
        for i, result in enumerate(results, 1):
            site_file = os.path.join(output_dir, f"site_{i}_content.txt")
            with open(site_file, 'w', encoding='utf-8') as f:
                f.write(f"URL: {result['url']}\n")
                f.write(f"取得日時: {result['scraped_at']}\n")
                f.write("="*80 + "\n\n")
                f.write(result['content'])
        
        # 画像URLリストファイル
        images_file = os.path.join(output_dir, "all_image_urls.txt")
        with open(images_file, 'w', encoding='utf-8') as f:
            f.write(f"画像URL一覧\n")
            f.write(f"検索キーワード: {query}\n")
            f.write("="*80 + "\n\n")
            
            for i, result in enumerate(results, 1):
                f.write(f"\nサイト {i}: {result['url']}\n")
                f.write(f"画像数: {len(result['images'])}\n")
                f.write("-"*40 + "\n")
                
                if result['images']:
                    for j, img_url in enumerate(result['images'], 1):
                        f.write(f"{j}. {img_url}\n")
                else:
                    f.write("画像なし\n")
                f.write("\n")
        
        # AI用のJSON形式でも保存
        ai_data_file = os.path.join(output_dir, "ai_data.json")
        ai_data = {
            'query': query,
            'scraped_at': datetime.now().isoformat(),
            'results': []
        }
        
        for result in results:
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
    
    def scrape(self, query: str):
        """メインのスクレイピング処理"""
        start_time = time.time()
        
        print("\n" + "="*80)
        print("🚀 高速Webスクレイピング開始")
        print("="*80)
        
        # Bing検索でURLを取得
        urls = self.search_bing(query, num_results=5)
        
        if not urls:
            print("❌ 検索結果が見つかりませんでした")
            return None
        
        print(f"\n取得したURL:")
        for i, url in enumerate(urls, 1):
            print(f"  {i}. {url}")
        
        # 非同期でスクレイピング実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(self.scrape_urls_async(urls))
        loop.close()
        
        # 結果を保存
        output_dir = self.save_results(query, results)
        
        elapsed_time = time.time() - start_time
        print(f"\n⏱️ 処理時間: {elapsed_time:.2f}秒")
        print(f"✨ スクレイピング完了！")
        
        return output_dir

def main():
    """メイン実行関数"""
    print("="*80)
    print("🔥 爆速Webスクレイピングツール")
    print("="*80)
    print("\n機能:")
    print("  - Bing検索で上位5件のサイトを自動取得")
    print("  - 並列処理で高速スクレイピング")
    print("  - テキストコンテンツと画像URLを抽出")
    print("  - 結果を整理してファイル保存")
    print("  - AI処理用のJSON形式でも出力")
    print("\n")
    
    # 検索キーワードを入力
    query = input("🔍 検索キーワードを入力してください: ").strip()
    
    if not query:
        print("❌ キーワードが入力されていません")
        return
    
    # スクレイピング実行
    scraper = FastWebScraper()
    output_dir = scraper.scrape(query)
    
    if output_dir:
        print(f"\n📊 結果サマリー:")
        print(f"  検索キーワード: {query}")
        print(f"  出力ディレクトリ: {output_dir}")
        print(f"\n💡 ヒント: AI処理には ai_data.json ファイルを使用してください")

if __name__ == "__main__":
    main()