"""
afternoon.py — 每天 15:00 推播
內容：台灣 Google 熱搜關鍵字 Top 10
"""
import os
import sys
import datetime
import time

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from line_push import push_text

load_dotenv()


# ── 方法一：Google Trends 每日熱搜（最可靠）────────────
def get_trending_searches_rss():
    """
    透過 Google Trends RSS 取得台灣當日熱搜 Top 20
    回傳前 10 名清單
    """
    url = "https://trends.google.com.tw/trending/rss?geo=TW"
    try:
        resp = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "zh-TW,zh;q=0.9",
            },
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item")

        results = []
        for item in items[:10]:
            title_tag = item.find("title")
            traffic_tag = item.find("ht:approx_traffic")
            news_tag = item.find("ht:news_item_title")

            if title_tag:
                keyword = title_tag.get_text(strip=True)
                traffic = (
                    traffic_tag.get_text(strip=True)
                    if traffic_tag
                    else "N/A"
                )
                # 相關新聞標題
                related = (
                    news_tag.get_text(strip=True)[:40]
                    if news_tag
                    else ""
                )
                results.append((keyword, traffic, related))

        return results

    except Exception as e:
        print(f"⚠️ RSS 抓取失敗：{e}")
        return []


# ── 方法二：pytrends（備用）──────────────────────────
def get_trending_searches_pytrends():
    """備用方案：使用 pytrends 套件"""
    try:
        from pytrends.request import TrendReq
        pt = TrendReq(hl="zh-TW", tz=480, timeout=(10, 30))
        time.sleep(1)
        df = pt.trending_searches(pn="taiwan")
        if df is not None and not df.empty:
            return [(row[0], "—", "") for row in df.values[:10]]
    except Exception as e:
        print(f"⚠️ pytrends 備用失敗：{e}")
    return []


# ── 組合訊息 ──────────────────────────────────────────
def build_message(results):
    today = datetime.date.today()
    lines = [
        f"🔍 台灣 Google 熱搜 Top 10",
        f"📅 {today.strftime('%Y/%m/%d')} 下午",
        "─" * 30,
    ]

    if not results:
        lines.append("⚠️ 今日熱搜資料暫時無法取得，請稍後至 Google Trends 查看。")
        lines.append("🔗 https://trends.google.com.tw/trending?geo=TW")
    else:
        for rank, (keyword, traffic, related) in enumerate(results, 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"{rank:>2}.")
            traffic_str = f"  搜尋量：{traffic}" if traffic not in ("N/A", "—") else ""
            related_str = f"\n      └ {related}" if related else ""
            lines.append(f"{medal} {keyword}{traffic_str}{related_str}")

    lines.append(f"\n🕒 更新時間：{datetime.datetime.now():%Y/%m/%d %H:%M}")
    lines.append("🔗 https://trends.google.com.tw/trending?geo=TW")
    return "\n".join(lines)


# ── 主程式 ───────────────────────────────────────────
def main():
    print(f"\n{'='*50}")
    print(f"☀️ Afternoon Report 開始執行 {datetime.datetime.now():%Y-%m-%d %H:%M}")
    print(f"{'='*50}")

    # 先嘗試 RSS，失敗再用 pytrends
    results = get_trending_searches_rss()
    if not results:
        print("⏳ RSS 無資料，改用 pytrends...")
        results = get_trending_searches_pytrends()

    message = build_message(results)
    print(message)
    push_text(message)

    print("✅ Afternoon Report 完成\n")


if __name__ == "__main__":
    main()
