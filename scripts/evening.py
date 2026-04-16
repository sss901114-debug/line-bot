"""
evening.py — 每天 19:00 推播
內容：台股盤後報告
  1. 融資融券增減前10名
  2. 外資投信買賣超前20名
  3. 大盤、櫃買指數
  4. 類股漲跌排行
  5. 當日熱門個股
  6. 公開資訊觀測站重大訊息
"""
import os
import sys
import datetime
import requests
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from line_push import push_text

load_dotenv()

TWSE_BASE = "https://www.twse.com.tw/rwd/zh"
MOPS_BASE = "https://mops.twse.com.tw"
TODAY = datetime.date.today().strftime("%Y%m%d")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.twse.com.tw/",
}


# ── 1. 大盤 & 櫃買指數 ────────────────────────────────
def get_market_index():
    lines = ["📊 大盤指數\n" + "─"*30]
    # 加權指數
    try:
        url = f"{TWSE_BASE}/afterTrading/STOCK_DAY_AVG?date={TODAY}&stockNo=0000"
        # 使用 twse 首頁 API
        url2 = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_t00.tw"
        resp = requests.get(url2, headers=HEADERS, timeout=10)
        data = resp.json()
        if data.get("msgArray"):
            info = data["msgArray"][0]
            name = info.get("n", "加權指數")
            z = float(info.get("z", 0) or 0)
            y = float(info.get("y", 0) or 0)
            chg = z - y
            pct = chg / y * 100 if y else 0
            arrow = "▲" if chg >= 0 else "▼"
            sign = "+" if chg >= 0 else ""
            lines.append(
                f"{arrow} 加權指數\n"
                f"   收盤：{z:,.2f}\n"
                f"   漲跌：{sign}{chg:,.2f} ({sign}{pct:.2f}%)"
            )
    except Exception as e:
        lines.append(f"加權指數抓取失敗：{e}")

    # 櫃買指數
    try:
        url_otc = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=otc_o00.tw"
        resp2 = requests.get(url_otc, headers=HEADERS, timeout=10)
        data2 = resp2.json()
        if data2.get("msgArray"):
            info2 = data2["msgArray"][0]
            z2 = float(info2.get("z", 0) or 0)
            y2 = float(info2.get("y", 0) or 0)
            chg2 = z2 - y2
            pct2 = chg2 / y2 * 100 if y2 else 0
            arrow2 = "▲" if chg2 >= 0 else "▼"
            sign2 = "+" if chg2 >= 0 else ""
            lines.append(
                f"{arrow2} 櫃買指數\n"
                f"   收盤：{z2:,.2f}\n"
                f"   漲跌：{sign2}{chg2:,.2f} ({sign2}{pct2:.2f}%)"
            )
    except Exception as e:
        lines.append(f"櫃買指數抓取失敗：{e}")

    return "\n".join(lines)


# ── 2. 融資融券增減前10名 ─────────────────────────────
def get_margin_trading():
    lines = ["\n📋 融資融券增減 Top 10\n" + "─"*30]
    try:
        # 融資餘額變動
        url = f"{TWSE_BASE}/marginTrading/TWT93U?date={TODAY}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        data = resp.json()

        if data.get("stat") == "OK" and data.get("data"):
            rows = data["data"]
            # 欄位：代號, 名稱, 融資買進, 融資賣出, 融資現償, 融資餘額, 融資增減, ...
            # 依融資增減排序
            try:
                rows_sorted = sorted(
                    rows,
                    key=lambda r: int(r[6].replace(",", "").replace("+", "") or 0),
                    reverse=True,
                )
                top_buy = rows_sorted[:5]
                top_sell = sorted(
                    rows,
                    key=lambda r: int(r[6].replace(",", "").replace("+", "") or 0),
                )[:5]

                lines.append("【融資增加最多（買超）】")
                for r in top_buy:
                    sym, name, chg = r[0], r[1], r[6]
                    lines.append(f"  {sym} {name}：{chg} 張")

                lines.append("\n【融資減少最多（賣超）】")
                for r in top_sell:
                    sym, name, chg = r[0], r[1], r[6]
                    lines.append(f"  {sym} {name}：{chg} 張")
            except Exception:
                lines.append("⚠️ 排序解析失敗，資料格式可能已更新")
        else:
            lines.append("⚠️ 融資資料今日尚未公布（盤後約17:30後才完整）")

    except Exception as e:
        lines.append(f"融資融券資料抓取失敗：{e}")

    return "\n".join(lines)


# ── 3. 外資投信買賣超前20名 ──────────────────────────
def get_institutional_investors():
    lines = ["\n🏦 外資投信買賣超 Top 20\n" + "─"*30]
    try:
        # 三大法人買賣超
        url = f"{TWSE_BASE}/fund/T86?date={TODAY}&selectType=ALL"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        data = resp.json()

        if data.get("stat") == "OK" and data.get("data"):
            rows = data["data"]
            # 欄位：代號, 名稱, 外資買, 外資賣, 外資淨, 投信買, 投信賣, 投信淨, 自營淨, 合計
            try:
                # 依外資淨買超排序
                def parse_int(s):
                    try:
                        return int(str(s).replace(",", "").replace("+", ""))
                    except Exception:
                        return 0

                rows_sorted = sorted(rows, key=lambda r: parse_int(r[4]), reverse=True)
                top20_buy = rows_sorted[:10]
                top20_sell = sorted(rows, key=lambda r: parse_int(r[4]))[:10]

                lines.append("【外資買超前10】（張數）")
                for r in top20_buy:
                    sym, name, net = r[0], r[1], r[4]
                    lines.append(f"  {sym} {name}：{net}")

                lines.append("\n【外資賣超前10】（張數）")
                for r in top20_sell:
                    sym, name, net = r[0], r[1], r[4]
                    lines.append(f"  {sym} {name}：{net}")

                # 投信
                rows_sit_buy = sorted(rows, key=lambda r: parse_int(r[7]), reverse=True)[:5]
                rows_sit_sell = sorted(rows, key=lambda r: parse_int(r[7]))[:5]

                lines.append("\n【投信買超前5】")
                for r in rows_sit_buy:
                    lines.append(f"  {r[0]} {r[1]}：{r[7]}")

                lines.append("\n【投信賣超前5】")
                for r in rows_sit_sell:
                    lines.append(f"  {r[0]} {r[1]}：{r[7]}")

            except Exception as ex:
                lines.append(f"⚠️ 資料解析失敗：{ex}")
        else:
            lines.append("⚠️ 三大法人資料今日尚未公布")

    except Exception as e:
        lines.append(f"外資投信資料抓取失敗：{e}")

    return "\n".join(lines)


# ── 4. 類股漲跌排行 ──────────────────────────────────
def get_sector_performance():
    lines = ["\n📈 類股漲跌排行\n" + "─"*30]
    try:
        url = f"{TWSE_BASE}/afterTrading/BWIBBU_d?date={TODAY}&selectType=ALL"
        # 改用大盤統計API（類股分類）
        url2 = "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=" + TODAY + "&type=IND"
        resp = requests.get(url2, headers=HEADERS, timeout=15)
        data = resp.json()

        if data.get("stat") == "OK":
            # 找到類股的 tables
            tables = data.get("tables", [])
            for tbl in tables:
                if tbl.get("title", "").startswith("各類指數"):
                    rows = tbl.get("data", [])
                    # 欄位：類別, 收盤, 漲跌, 漲跌%, ...
                    def parse_pct(s):
                        try:
                            return float(str(s).replace("+", "").replace("%", "").replace(",", ""))
                        except Exception:
                            return 0

                    rows_sorted = sorted(rows, key=lambda r: parse_pct(r[3] if len(r) > 3 else 0), reverse=True)
                    lines.append("【強勢類股（漲幅前8）】")
                    for r in rows_sorted[:8]:
                        name = r[0]
                        chg_pct = r[3] if len(r) > 3 else "N/A"
                        close = r[1] if len(r) > 1 else "N/A"
                        lines.append(f"  {name}：{close}（{chg_pct}%）")

                    lines.append("\n【弱勢類股（跌幅前5）】")
                    for r in rows_sorted[-5:][::-1]:
                        name = r[0]
                        chg_pct = r[3] if len(r) > 3 else "N/A"
                        close = r[1] if len(r) > 1 else "N/A"
                        lines.append(f"  {name}：{close}（{chg_pct}%）")
                    break
            else:
                lines.append("⚠️ 類股資料尚未更新")
        else:
            lines.append("⚠️ 類股資料暫時無法取得")

    except Exception as e:
        lines.append(f"類股資料抓取失敗：{e}")

    return "\n".join(lines)


# ── 5. 當日熱門個股 ──────────────────────────────────
def get_hot_stocks():
    lines = ["\n🔥 當日熱門個股（成交量前15）\n" + "─"*30]
    try:
        url = f"{TWSE_BASE}/afterTrading/MI_INDEX20?date={TODAY}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        data = resp.json()

        if data.get("stat") == "OK" and data.get("data"):
            rows = data["data"][:15]
            for r in rows:
                if len(r) >= 9:
                    rank = r[0]
                    sym = r[2]
                    name = r[3]
                    close = r[8]
                    chg = r[9] if len(r) > 9 else "N/A"
                    vol = r[7] if len(r) > 7 else "N/A"
                    lines.append(f"  {rank}. {sym} {name}  收：{close}  漲跌：{chg}  量：{vol}")
        else:
            lines.append("⚠️ 熱門個股資料暫時無法取得")

    except Exception as e:
        lines.append(f"熱門個股抓取失敗：{e}")

    return "\n".join(lines)


# ── 6. 公開資訊觀測站重大訊息 ────────────────────────
def get_mops_announcements():
    lines = ["\n📢 公開資訊觀測站重大訊息（今日）\n" + "─"*30]
    try:
        # MOPS 即時重大訊息 API
        url = "https://mops.twse.com.tw/mops/web/ajax_t05sr01"
        payload = {
            "encodeURIComponent": "1",
            "step": "1",
            "firstin": "1",
            "off": "1",
            "keyword4": "",
            "code1": "",
            "TYPEK2": "",
            "checkbtn": "",
            "queryName": "co_id",
            "inpuType": "co_id",
            "TYPEK": "all",
            "isnew": "true",
        }
        resp = requests.post(
            url,
            data=payload,
            headers={**HEADERS, "Referer": "https://mops.twse.com.tw/mops/web/t05sr01"},
            timeout=15,
        )
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", class_="hasBorder")
        if not table:
            # 嘗試另一個結構
            table = soup.find("table")

        if table:
            rows = table.find_all("tr")[1:16]  # 取前15筆
            count = 0
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 4:
                    time_str = cols[0].get_text(strip=True)
                    company = cols[1].get_text(strip=True)
                    subject = cols[3].get_text(strip=True)[:50]
                    lines.append(f"⏰ {time_str} │ {company}\n   └ {subject}")
                    count += 1
            if count == 0:
                lines.append("⚠️ 今日暫無重大訊息")
        else:
            lines.append("⚠️ MOPS 資料解析失敗，請直接查閱：")
            lines.append("🔗 https://mops.twse.com.tw/mops/web/t05sr01")

    except Exception as e:
        lines.append(f"MOPS 重大訊息抓取失敗：{e}")
        lines.append("🔗 https://mops.twse.com.tw/mops/web/t05sr01")

    return "\n".join(lines)


# ── 主程式 ───────────────────────────────────────────
def main():
    print(f"\n{'='*50}")
    print(f"🌆 Evening Report 開始執行 {datetime.datetime.now():%Y-%m-%d %H:%M}")
    print(f"{'='*50}")

    sections = [
        ("大盤指數", get_market_index),
        ("融資融券", get_margin_trading),
        ("外資投信", get_institutional_investors),
        ("類股排行", get_sector_performance),
        ("熱門個股", get_hot_stocks),
        ("重大訊息", get_mops_announcements),
    ]

    messages = []
    header = (
        f"🇹🇼 台股盤後日報\n"
        f"📅 {datetime.date.today().strftime('%Y/%m/%d')}\n"
        f"{'═'*30}"
    )
    current_msg = header

    for section_name, func in sections:
        print(f"⏳ 抓取 {section_name}...")
        try:
            content = func()
        except Exception as e:
            content = f"\n⚠️ {section_name} 發生例外：{e}"

        # 超過4800字就分段推播
        if len(current_msg) + len(content) > 4800:
            messages.append(current_msg)
            current_msg = content
        else:
            current_msg += "\n" + content

    if current_msg:
        current_msg += f"\n\n🕖 更新時間：{datetime.datetime.now():%Y/%m/%d %H:%M}"
        messages.append(current_msg)

    # 逐則推播
    for i, msg in enumerate(messages, 1):
        print(f"\n📤 推播第 {i}/{len(messages)} 則訊息...")
        push_text(msg)

    print("✅ Evening Report 完成\n")


if __name__ == "__main__":
    main()
