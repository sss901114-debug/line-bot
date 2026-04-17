"""
evening.py — 每天 19:00 推播（優化排版版）
"""
import os
import sys
import datetime
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from line_push import push_text

load_dotenv()

TWSE_BASE = "https://www.twse.com.tw/rwd/zh"
TODAY = datetime.date.today().strftime("%Y%m%d")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.twse.com.tw/",
}


def section(title):
    return f"━━━━━━━━━━━━━━━━━━━━━━\n{title}\n━━━━━━━━━━━━━━━━━━━━━━"


def get_market_index():
    lines = [section("📊  大盤指數"), ""]
    for label, url in [
        ("加權指數", "https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_t00.tw"),
        ("櫃買指數", "https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=otc_o00.tw"),
    ]:
        try:
            data = requests.get(url, headers=HEADERS, timeout=10).json()
            if data.get("msgArray"):
                info = data["msgArray"][0]
                z = float(info.get("z", 0) or 0)
                y = float(info.get("y", 0) or 0)
                chg = z - y
                pct = chg / y * 100 if y else 0
                arrow = "▲" if chg >= 0 else "▼"
                sign = "+" if chg >= 0 else ""
                lines.append(f"{arrow} {label}")
                lines.append(f"    收盤  {z:>10,.2f}")
                lines.append(f"    漲跌  {sign}{chg:>8,.2f}  ({sign}{pct:.2f}%)")
                lines.append("")
        except Exception:
            lines.append(f"⚠️ {label} 抓取失敗\n")
    return "\n".join(lines)


def get_margin_trading():
    lines = [section("📋  融資融券增減 Top 10"), ""]
    try:
        url = f"{TWSE_BASE}/marginTrading/TWT93U?date={TODAY}"
        data = requests.get(url, headers=HEADERS, timeout=15).json()
        if data.get("stat") == "OK" and data.get("data"):
            rows = data["data"]
            def parse_int(s):
                try: return int(str(s).replace(",","").replace("+",""))
                except: return 0

            rows_sorted = sorted(rows, key=lambda r: parse_int(r[6]), reverse=True)

            lines.append("【 融資增加最多 】")
            for r in rows_sorted[:5]:
                lines.append(f"  {r[0]} {r[1]:<8}  {r[6]} 張")
            lines.append("")
            lines.append("【 融資減少最多 】")
            for r in sorted(rows, key=lambda r: parse_int(r[6]))[:5]:
                lines.append(f"  {r[0]} {r[1]:<8}  {r[6]} 張")
            lines.append("")
        else:
            lines.append("⚠️ 融資資料尚未公布（約17:30後）\n")
    except Exception as e:
        lines.append(f"⚠️ 抓取失敗：{e}\n")
    return "\n".join(lines)


def get_institutional_investors():
    lines = [section("🏦  外資投信買賣超"), ""]
    try:
        url = f"{TWSE_BASE}/fund/T86?date={TODAY}&selectType=ALL"
        data = requests.get(url, headers=HEADERS, timeout=15).json()
        if data.get("stat") == "OK" and data.get("data"):
            rows = data["data"]
            def parse_int(s):
                try: return int(str(s).replace(",","").replace("+",""))
                except: return 0

            lines.append("【 外資買超 Top 10 】")
            for r in sorted(rows, key=lambda r: parse_int(r[4]), reverse=True)[:10]:
                lines.append(f"  {r[0]} {r[1]:<8}  {r[4]} 張")
            lines.append("")
            lines.append("【 外資賣超 Top 10 】")
            for r in sorted(rows, key=lambda r: parse_int(r[4]))[:10]:
                lines.append(f"  {r[0]} {r[1]:<8}  {r[4]} 張")
            lines.append("")
            lines.append("【 投信買超 Top 5 】")
            for r in sorted(rows, key=lambda r: parse_int(r[7]), reverse=True)[:5]:
                lines.append(f"  {r[0]} {r[1]:<8}  {r[7]} 張")
            lines.append("")
            lines.append("【 投信賣超 Top 5 】")
            for r in sorted(rows, key=lambda r: parse_int(r[7]))[:5]:
                lines.append(f"  {r[0]} {r[1]:<8}  {r[7]} 張")
            lines.append("")
        else:
            lines.append("⚠️ 三大法人資料尚未公布\n")
    except Exception as e:
        lines.append(f"⚠️ 抓取失敗：{e}\n")
    return "\n".join(lines)


def get_sector_performance():
    lines = [section("📈  類股漲跌排行"), ""]
    try:
        url = f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={TODAY}&type=IND"
        data = requests.get(url, headers=HEADERS, timeout=15).json()
        if data.get("stat") == "OK":
            for tbl in data.get("tables", []):
                if tbl.get("title", "").startswith("各類指數"):
                    def parse_pct(s):
                        try: return float(str(s).replace("+","").replace("%","").replace(",",""))
                        except: return 0
                    rows = tbl.get("data", [])
                    rows_sorted = sorted(rows, key=lambda r: parse_pct(r[3] if len(r)>3 else 0), reverse=True)
                    lines.append("【 強勢類股 Top 8 】")
                    for r in rows_sorted[:8]:
                        lines.append(f"  {r[0]:<10}  {r[1]:>8}  ({r[3]}%)")
                    lines.append("")
                    lines.append("【 弱勢類股 Bottom 5 】")
                    for r in rows_sorted[-5:][::-1]:
                        lines.append(f"  {r[0]:<10}  {r[1]:>8}  ({r[3]}%)")
                    lines.append("")
                    break
        else:
            lines.append("⚠️ 類股資料暫時無法取得\n")
    except Exception as e:
        lines.append(f"⚠️ 抓取失敗：{e}\n")
    return "\n".join(lines)


def get_hot_stocks():
    import re as _re
    lines = [section("🔥  當日熱門個股（成交量前15）"), ""]
    try:
        url = f"{TWSE_BASE}/afterTrading/MI_INDEX20?date={TODAY}"
        data = requests.get(url, headers=HEADERS, timeout=15).json()
        if data.get("stat") == "OK" and data.get("data"):
            for r in data["data"][:15]:
                if len(r) >= 9:
                    rank, sym, name = r[0], r[2], r[3]
                    close = _re.sub(r'<[^>]+>', '', str(r[8]))
                    chg   = _re.sub(r'<[^>]+>', '', str(r[9] if len(r)>9 else "N/A"))
                    vol   = _re.sub(r'<[^>]+>', '', str(r[7] if len(r)>7 else "N/A"))
                    arrow = "▲" if "+" in chg or (chg not in ("N/A","0") and not chg.startswith("-")) else "▼"
                    lines.append(f"  {rank:>2}. {sym} {name}")
                    lines.append(f"      收：{close}　漲跌：{arrow}{chg}　量：{vol}")
                    lines.append("")
        else:
            lines.append("⚠️ 資料暫時無法取得\n")
    except Exception as e:
        lines.append(f"⚠️ 抓取失敗：{e}\n")
    return "\n".join(lines)


def get_mops_announcements():
    lines = [section("📢  公開資訊觀測站重大訊息"), ""]
    try:
        url = "https://mops.twse.com.tw/mops/web/ajax_t05sr01"
        payload = {
            "encodeURIComponent":"1","step":"1","firstin":"1","off":"1",
            "keyword4":"","code1":"","TYPEK2":"","checkbtn":"",
            "queryName":"co_id","inpuType":"co_id","TYPEK":"all","isnew":"true",
        }
        resp = requests.post(url, data=payload, headers={**HEADERS,
            "Referer":"https://mops.twse.com.tw/mops/web/t05sr01"}, timeout=15)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", class_="hasBorder") or soup.find("table")

        if table:
            count = 0
            for row in table.find_all("tr")[1:16]:
                cols = row.find_all("td")
                if len(cols) >= 4:
                    time_str = cols[0].get_text(strip=True)
                    company = cols[1].get_text(strip=True)
                    subject = cols[3].get_text(strip=True)[:45]
                    lines.append(f"⏰ {time_str}  {company}")
                    lines.append(f"   📌 {subject}")
                    lines.append("")
                    count += 1
            if count == 0:
                lines.append("今日暫無重大訊息\n")
        else:
            lines.append("⚠️ 解析失敗，請直接查閱：")
            lines.append("🔗 https://mops.twse.com.tw/mops/web/t05sr01\n")
    except Exception as e:
        lines.append(f"⚠️ 抓取失敗：{e}\n")
    return "\n".join(lines)


def main():
    print(f"\n{'='*50}")
    print(f"🌆 Evening Report {datetime.datetime.now():%Y-%m-%d %H:%M}")

    today = datetime.date.today()
    now = datetime.datetime.now()

    header = (
        "╔══════════════════════╗\n"
        "║  🇹🇼  台股盤後日報  ║\n"
        "╚══════════════════════╝\n"
        f"📅  {today.strftime('%Y / %m / %d')}"
    )

    footer = (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕖 更新於 {now.strftime('%H:%M')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )

    fetch_list = [
        ("大盤指數",   get_market_index),
        ("融資融券",   get_margin_trading),
        ("外資投信",   get_institutional_investors),
        ("類股排行",   get_sector_performance),
        ("熱門個股",   get_hot_stocks),
        ("重大訊息",   get_mops_announcements),
    ]

    messages = []
    current = header

    for name, func in fetch_list:
        print(f"⏳ 抓取 {name}...")
        try:
            content = func()
        except Exception as e:
            content = f"⚠️ {name} 發生例外：{e}"
        if len(current) + len(content) > 4500:
            messages.append(current)
            current = content
        else:
            current += "\n\n" + content

    current += "\n\n" + footer
    messages.append(current)

    for i, msg in enumerate(messages, 1):
        print(f"📤 推播第 {i}/{len(messages)} 則...")
        push_text(msg)

    print("✅ Evening Report 完成\n")


if __name__ == "__main__":
    main()
