"""
morning.py — 每天 07:00 推播（優化排版版）
內容：美股四大指數、大宗商品、近3個月走勢圖、供需新聞
"""
import os
import sys
import datetime
import warnings
import tempfile

import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from line_push import push_text, push_image

warnings.filterwarnings("ignore")
load_dotenv()

TICKERS = {
    "道瓊 DJI":    "^DJI",
    "Nasdaq":       "^IXIC",
    "S&P 500":      "^GSPC",
    "費城半導體":   "^SOX",
}

COMMODITIES = {
    "黃金":     "GC=F",
    "銅":       "HG=F",
    "WTI 油價": "CL=F",
    "比特幣":   "BTC-USD",
    "美元指數": "DX-Y.NYB",
}

CHART_TICKERS = {
    "黃金（現貨）":   "GC=F",
    "銅（期貨）":     "HG=F",
    "比特幣（USD）":  "BTC-USD",
    "WTI 原油":       "CL=F",
    "美元指數（DXY）":"DX-Y.NYB",
}

SUPPLY_KEYWORDS = [
    "供不應求","供給吃緊","需求強烈","需求大增","缺貨","短缺",
    "搶購","產能不足","tight supply","supply shortage","strong demand","supply crunch",
]


def fmt_chg(chg, pct):
    arrow = "▲" if chg >= 0 else "▼"
    sign = "+" if chg >= 0 else ""
    return arrow, sign, f"{sign}{chg:,.2f}", f"{sign}{pct:.2f}%"


def get_us_markets():
    today = datetime.date.today()
    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("🇺🇸  美股收盤行情")
    lines.append(f"📅  {today.strftime('%Y / %m / %d')}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")

    for name, sym in TICKERS.items():
        try:
            hist = yf.Ticker(sym).history(period="2d")
            if len(hist) < 2:
                lines.append(f"⚠️ {name}：資料不足")
                continue
            prev, last = hist["Close"].iloc[-2], hist["Close"].iloc[-1]
            chg = last - prev
            pct = chg / prev * 100
            arrow, sign, chg_str, pct_str = fmt_chg(chg, pct)
            lines.append(f"{arrow} {name}")
            lines.append(f"    收盤  {last:>12,.2f}")
            lines.append(f"    漲跌  {chg_str:>10}  ({pct_str})")
            lines.append("")
        except Exception as e:
            lines.append(f"⚠️ {name} 抓取失敗")
            lines.append("")

    return "\n".join(lines)


def get_commodities():
    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("🛢  大宗商品 / 加密貨幣")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")

    for name, sym in COMMODITIES.items():
        try:
            hist = yf.Ticker(sym).history(period="2d")
            if len(hist) < 2:
                lines.append(f"⚠️ {name}：資料不足")
                continue
            prev, last = hist["Close"].iloc[-2], hist["Close"].iloc[-1]
            chg = last - prev
            pct = chg / prev * 100
            arrow, sign, chg_str, pct_str = fmt_chg(chg, pct)
            lines.append(f"{arrow} {name}")
            lines.append(f"    現價  {last:>12,.2f}")
            lines.append(f"    漲跌  {chg_str:>10}  ({pct_str})")
            lines.append("")
        except Exception as e:
            lines.append(f"⚠️ {name} 抓取失敗")
            lines.append("")

    return "\n".join(lines)


def generate_trend_chart():
    # 設定中文字型（Windows 微軟正黑體，macOS / Linux 備援）
    import matplotlib.font_manager as fm
    sys_fonts = [f.name for f in fm.fontManager.ttflist]
    if "Microsoft JhengHei" in sys_fonts:
        plt.rcParams["font.family"] = "Microsoft JhengHei"
    elif "PingFang TC" in sys_fonts:
        plt.rcParams["font.family"] = "PingFang TC"
    elif "Noto Sans CJK TC" in sys_fonts:
        plt.rcParams["font.family"] = "Noto Sans CJK TC"
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(3, 2, figsize=(14, 16))
    fig.patch.set_facecolor("#0d1117")
    axes_flat = axes.flatten()
    items = list(CHART_TICKERS.items())

    for idx, (name, sym) in enumerate(items):
        ax = axes_flat[idx]
        ax.set_facecolor("#161b22")
        try:
            df = yf.download(sym, period="3mo", interval="1d", progress=False)
            if df.empty:
                ax.text(0.5, 0.5, "No Data", transform=ax.transAxes, ha="center", color="#8b949e")
            else:
                closes = df["Close"].squeeze()
                color = "#3fb950" if closes.iloc[-1] >= closes.iloc[0] else "#f85149"
                ax.plot(df.index, closes, color=color, linewidth=1.5)
                ax.fill_between(df.index, closes, closes.min(), alpha=0.15, color=color)
                ax.set_title(name, color="#e6edf3", fontsize=11, pad=8)
                ax.tick_params(colors="#8b949e", labelsize=8)
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
                for spine in ax.spines.values():
                    spine.set_edgecolor("#30363d")
                last_val = closes.iloc[-1]
                ax.annotate(f"{last_val:,.2f}", xy=(df.index[-1], last_val),
                            xytext=(-40, 8), textcoords="offset points",
                            color=color, fontsize=9, fontweight="bold")
        except Exception as e:
            ax.text(0.5, 0.5, f"Error", transform=ax.transAxes, ha="center", color="#f85149")

    for idx in range(len(items), len(axes_flat)):
        axes_flat[idx].set_visible(False)

    fig.suptitle(f"大宗商品近3個月走勢  {datetime.date.today().strftime('%Y/%m/%d')}",
                 color="#e6edf3", fontsize=14, y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    plt.savefig(tmp.name, dpi=130, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return tmp.name


def get_supply_demand_news():
    found = []
    queries = ["供不應求 OR 缺貨 OR 供給吃緊 OR 需求大增",
               "supply shortage OR supply crunch OR strong demand"]
    for query in queries:
        try:
            url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
            resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(resp.content, "xml")
            for item in soup.find_all("item")[:6]:
                title = item.find("title")
                pub = item.find("pubDate")
                source = item.find("source")
                if title:
                    t = title.get_text(strip=True)
                    if any(kw.lower() in t.lower() for kw in SUPPLY_KEYWORDS):
                        s = source.get_text(strip=True) if source else ""
                        p = pub.get_text(strip=True)[:16] if pub else ""
                        found.append((t, s, p))
        except Exception:
            pass

    seen, unique = set(), []
    for item in found:
        key = item[0][:40]
        if key not in seen:
            seen.add(key)
            unique.append(item)
        if len(unique) >= 6:
            break

    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("📦  供需相關新聞（24h內）")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    if not unique:
        lines.append("今日暫無符合條件的新聞")
    else:
        for i, (title, source, pub) in enumerate(unique, 1):
            lines.append(f"【{i}】{title}")
            lines.append(f"      📰 {source}  {pub}")
            lines.append("")
    return "\n".join(lines)


def get_us_stock_news():
    try:
        url = "https://news.google.com/rss/search?q=stock+market+today&hl=en-US&gl=US&ceid=US:en"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item")[:5]
        lines = []
        lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("📰  美股市場熱門新聞")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")
        for i, item in enumerate(items, 1):
            title = item.find("title")
            source = item.find("source")
            if title:
                t = title.get_text(strip=True)
                s = source.get_text(strip=True) if source else ""
                lines.append(f"【{i}】{t}")
                lines.append(f"      📰 {s}")
                lines.append("")
        return "\n".join(lines)
    except Exception:
        return "📰 美股新聞抓取失敗"


def main():
    print(f"\n{'='*50}")
    print(f"🌅 Morning Report {datetime.datetime.now():%Y-%m-%d %H:%M}")

    now_str = datetime.datetime.now().strftime('%H:%M')

    # 組合各區塊
    header = (
        "╔══════════════════════╗\n"
        "║  🌅  每日早報  ║\n"
        "╚══════════════════════╝"
    )

    sections = [
        header,
        get_us_markets(),
        get_commodities(),
        get_supply_demand_news(),
        get_us_stock_news(),
        f"━━━━━━━━━━━━━━━━━━━━━━\n🕖 更新於 {now_str}\n━━━━━━━━━━━━━━━━━━━━━━",
    ]

    # 分批推播（LINE每則上限4800字）
    current = ""
    messages = []
    for sec in sections:
        if len(current) + len(sec) > 4500:
            messages.append(current)
            current = sec
        else:
            current = current + "\n" + sec if current else sec

    if current:
        messages.append(current)

    for i, msg in enumerate(messages, 1):
        print(f"📤 推播第 {i}/{len(messages)} 則...")
        push_text(msg)

    # 走勢圖
    try:
        chart_path = generate_trend_chart()
        push_image(chart_path, alt_text="大宗商品近3個月走勢圖")
        os.unlink(chart_path)
    except Exception as e:
        push_text(f"⚠️ 走勢圖產生失敗：{e}")

    print("✅ Morning Report 完成\n")


if __name__ == "__main__":
    main()
