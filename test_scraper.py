#!/usr/bin/env python3
"""
スクレイピングツールのテストスクリプト
"""

from fast_scraper import FastWebScraper
import json
import os

def test_scraping():
    """テスト実行"""
    print("="*80)
    print("🧪 スクレイピングツールのテスト実行")
    print("="*80)
    
    # テスト用のキーワード
    test_query = "Python web scraping tutorial"
    
    print(f"\nテストキーワード: '{test_query}'")
    print("-"*40)
    
    # スクレイパーのインスタンス作成
    scraper = FastWebScraper()
    
    # スクレイピング実行
    output_dir = scraper.scrape(test_query)
    
    if output_dir and os.path.exists(output_dir):
        print("\n📁 生成されたファイル:")
        files = os.listdir(output_dir)
        for file in files:
            file_path = os.path.join(output_dir, file)
            file_size = os.path.getsize(file_path)
            print(f"  - {file} ({file_size:,} bytes)")
        
        # AI用JSONファイルの内容を確認
        ai_data_file = os.path.join(output_dir, "ai_data.json")
        if os.path.exists(ai_data_file):
            with open(ai_data_file, 'r', encoding='utf-8') as f:
                ai_data = json.load(f)
            
            print(f"\n📊 スクレイピング結果サマリー:")
            print(f"  - 検索キーワード: {ai_data['query']}")
            print(f"  - 取得サイト数: {len(ai_data['results'])}")
            
            total_images = sum(r['total_images'] for r in ai_data['results'])
            print(f"  - 総画像数: {total_images}")
            
            print(f"\n📝 取得したサイト:")
            for i, result in enumerate(ai_data['results'], 1):
                print(f"  {i}. {result['url']}")
                print(f"     - テキスト: {result['full_content_length']:,} 文字")
                print(f"     - 画像: {result['total_images']} 個")
        
        print(f"\n✅ テスト成功！")
        print(f"💡 結果は '{output_dir}' ディレクトリに保存されています。")
        return True
    else:
        print("\n❌ テスト失敗: 出力ディレクトリが作成されませんでした。")
        return False

if __name__ == "__main__":
    test_scraping()