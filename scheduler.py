"""
scheduler.py — 主排程器
本機執行時使用此腳本，24小時持續運行
部署到雲端時建議改用 GitHub Actions（見 .github/workflows/）
"""
import os
import sys
import time
import datetime
import schedule
import logging

# 設定 log
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scheduler.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "scripts")
sys.path.insert(0, SCRIPTS_DIR)


def run_morning():
    log.info("🌅 執行 Morning Report（07:00）")
    try:
        import importlib
        import morning
        importlib.reload(morning)
        morning.main()
    except Exception as e:
        log.error(f"Morning Report 失敗：{e}")


def run_afternoon():
    log.info("☀️ 執行 Afternoon Report（15:00）")
    try:
        import importlib
        import afternoon
        importlib.reload(afternoon)
        afternoon.main()
    except Exception as e:
        log.error(f"Afternoon Report 失敗：{e}")


def run_evening():
    log.info("🌆 執行 Evening Report（19:00）")
    try:
        import importlib
        import evening
        importlib.reload(evening)
        evening.main()
    except Exception as e:
        log.error(f"Evening Report 失敗：{e}")


# ── 排程設定（台灣時間 UTC+8）────────────────────────
schedule.every().day.at("07:00").do(run_morning)
schedule.every().day.at("15:00").do(run_afternoon)
schedule.every().day.at("19:00").do(run_evening)


def main():
    log.info("=" * 50)
    log.info("🤖 LINE Bot 排程器啟動")
    log.info(f"📅 當前時間：{datetime.datetime.now():%Y-%m-%d %H:%M:%S}")
    log.info("📋 排程計劃：")
    log.info("   07:00 美股/商品/走勢圖/供需新聞")
    log.info("   15:00 Google 熱搜 Top 10")
    log.info("   19:00 台股盤後完整報告")
    log.info("=" * 50)

    # 可選：啟動時立即執行一次（測試用，正式部署請注解掉）
    # run_morning()
    # run_afternoon()
    # run_evening()

    while True:
        schedule.run_pending()
        time.sleep(30)  # 每30秒檢查一次排程


if __name__ == "__main__":
    main()
