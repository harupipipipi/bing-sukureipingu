#!/usr/bin/env python3
"""
Streamlit GUI for Web Scraping Tool
簡単なWebインターフェースでスクレイピング
"""

import streamlit as st
import pandas as pd
from fast_scraper import FastWebScraper
import asyncio
import json
import os
from datetime import datetime

# ページ設定
st.set_page_config(
    page_title="爆速Webスクレイピングツール",
    page_icon="🚀",
    layout="wide"
)

# セッション状態の初期化
if 'scraping_results' not in st.session_state:
    st.session_state.scraping_results = None
if 'output_dir' not in st.session_state:
    st.session_state.output_dir = None

def main():
    # タイトル
    st.title("🚀 爆速Webスクレイピングツール")
    st.markdown("Bing検索を使用して上位5件のサイトを高速スクレイピング")
    
    # サイドバー
    with st.sidebar:
        st.header("📋 機能説明")
        st.markdown("""
        - **Bing検索**: キーワードで上位5件を自動取得
        - **並列処理**: 複数サイトを同時スクレイピング
        - **テキスト抽出**: ページ内容を整形して取得
        - **画像URL収集**: 全画像のURLをリスト化
        - **ファイル出力**: .txt形式で結果を保存
        - **AI連携**: JSON形式でデータ出力
        """)
        
        st.header("💡 使い方")
        st.markdown("""
        1. 検索キーワードを入力
        2. 「スクレイピング開始」をクリック
        3. 結果を確認・ダウンロード
        """)
    
    # メインコンテンツ
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 検索フォーム
        search_query = st.text_input(
            "🔍 検索キーワードを入力",
            placeholder="例: Python プログラミング 入門",
            help="Bing検索で使用するキーワード"
        )
        
        if st.button("🚀 スクレイピング開始", type="primary", disabled=not search_query):
            if search_query:
                with st.spinner("スクレイピング実行中... (最大30秒)"):
                    try:
                        # スクレイピング実行
                        scraper = FastWebScraper()
                        
                        # URL取得
                        urls = scraper.search_bing(search_query, num_results=5)
                        
                        if urls:
                            # 非同期スクレイピング
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            results = loop.run_until_complete(scraper.scrape_urls_async(urls))
                            loop.close()
                            
                            # 結果を保存
                            output_dir = scraper.save_results(search_query, results)
                            
                            # セッション状態に保存
                            st.session_state.scraping_results = results
                            st.session_state.output_dir = output_dir
                            
                            st.success(f"✅ スクレイピング完了！ {len(results)}件のサイトを取得しました。")
                        else:
                            st.error("❌ 検索結果が見つかりませんでした。")
                            
                    except Exception as e:
                        st.error(f"エラーが発生しました: {str(e)}")
    
    with col2:
        if st.session_state.output_dir:
            st.info(f"📁 出力フォルダ: {st.session_state.output_dir}")
    
    # 結果表示
    if st.session_state.scraping_results:
        st.header("📊 スクレイピング結果")
        
        # タブで結果を整理
        tab1, tab2, tab3, tab4 = st.tabs(["📝 テキスト内容", "🖼️ 画像URL", "📊 統計情報", "💾 ダウンロード"])
        
        with tab1:
            st.subheader("取得したテキスト内容")
            for i, result in enumerate(st.session_state.scraping_results, 1):
                with st.expander(f"サイト {i}: {result['url']}", expanded=False):
                    st.text_area(
                        "コンテンツ",
                        value=result['content'][:3000],
                        height=300,
                        key=f"content_{i}"
                    )
                    if len(result['content']) > 3000:
                        st.info("※ 表示は最初の3000文字のみ。完全版はファイルをダウンロードしてください。")
        
        with tab2:
            st.subheader("取得した画像URL")
            for i, result in enumerate(st.session_state.scraping_results, 1):
                if result['images']:
                    with st.expander(f"サイト {i}: {len(result['images'])}個の画像", expanded=False):
                        for j, img_url in enumerate(result['images'][:10], 1):
                            st.text(f"{j}. {img_url}")
                        if len(result['images']) > 10:
                            st.info(f"※ 他{len(result['images'])-10}個の画像URL")
        
        with tab3:
            st.subheader("統計情報")
            
            # データフレームで表示
            stats_data = []
            for i, result in enumerate(st.session_state.scraping_results, 1):
                stats_data.append({
                    'サイト番号': i,
                    'URL': result['url'],
                    'テキスト文字数': len(result['content']),
                    '画像数': len(result['images']),
                    '取得時刻': result['scraped_at']
                })
            
            df = pd.DataFrame(stats_data)
            st.dataframe(df, use_container_width=True)
            
            # サマリー
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("総サイト数", len(stats_data))
            with col2:
                st.metric("総文字数", f"{sum(d['テキスト文字数'] for d in stats_data):,}")
            with col3:
                st.metric("総画像数", sum(d['画像数'] for d in stats_data))
        
        with tab4:
            st.subheader("ファイルダウンロード")
            
            if st.session_state.output_dir and os.path.exists(st.session_state.output_dir):
                st.success("✅ ファイルが生成されました")
                
                # ファイルリスト
                files = os.listdir(st.session_state.output_dir)
                
                for file in files:
                    file_path = os.path.join(st.session_state.output_dir, file)
                    if os.path.isfile(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        st.download_button(
                            label=f"📥 {file}",
                            data=content,
                            file_name=file,
                            mime='text/plain' if file.endswith('.txt') else 'application/json'
                        )

if __name__ == "__main__":
    main()