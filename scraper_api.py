#!/usr/bin/env python3
"""
プログラマブルWebスクレイピングAPI
他のPythonスクリプトから呼び出し可能
"""

from fast_scraper import FastWebScraper
import json
import os

def scrape_with_query(query: str, save_to_file: bool = True) -> dict:
    """
    指定されたクエリでWebスクレイピングを実行
    
    Args:
        query: 検索キーワード
        save_to_file: ファイルに保存するかどうか
    
    Returns:
        スクレイピング結果の辞書
    """
    scraper = FastWebScraper()
    
    # URLを取得
    urls = scraper.search_bing(query, num_results=5)
    
    if not urls:
        return {
            'success': False,
            'error': 'No search results found',
            'query': query,
            'results': []
        }
    
    # スクレイピング実行
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results = loop.run_until_complete(scraper.scrape_urls_async(urls))
    loop.close()
    
    # ファイルに保存
    output_dir = None
    if save_to_file:
        output_dir = scraper.save_results(query, results)
    
    # 結果を返す
    return {
        'success': True,
        'query': query,
        'output_dir': output_dir,
        'results': results
    }

def quick_scrape(query: str) -> str:
    """
    クイックスクレイピング - テキストのみを結合して返す
    
    Args:
        query: 検索キーワード
    
    Returns:
        全サイトのテキストを結合した文字列
    """
    result = scrape_with_query(query, save_to_file=False)
    
    if not result['success']:
        return f"Error: {result.get('error', 'Unknown error')}"
    
    # 全テキストを結合
    combined_text = []
    for i, site_result in enumerate(result['results'], 1):
        combined_text.append(f"\n{'='*80}")
        combined_text.append(f"サイト {i}: {site_result['url']}")
        combined_text.append(f"{'='*80}\n")
        combined_text.append(site_result['content'])
    
    return '\n'.join(combined_text)

def get_all_image_urls(query: str) -> list:
    """
    指定クエリで検索して全画像URLを取得
    
    Args:
        query: 検索キーワード
    
    Returns:
        全画像URLのリスト
    """
    result = scrape_with_query(query, save_to_file=False)
    
    if not result['success']:
        return []
    
    # 全画像URLを収集
    all_images = []
    for site_result in result['results']:
        all_images.extend(site_result['images'])
    
    return all_images

# 使用例
if __name__ == "__main__":
    # テスト実行
    test_query = "Python web scraping"
    
    print("テスト実行中...")
    
    # 完全なスクレイピング
    result = scrape_with_query(test_query)
    print(f"結果: {result['success']}")
    if result['output_dir']:
        print(f"出力ディレクトリ: {result['output_dir']}")
    
    # クイックテキスト取得
    # text = quick_scrape(test_query)
    # print(f"取得テキスト長: {len(text)} 文字")
    
    # 画像URL取得
    # images = get_all_image_urls(test_query)
    # print(f"取得画像数: {len(images)}")