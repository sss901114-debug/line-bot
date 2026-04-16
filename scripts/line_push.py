"""
line_push.py — LINE Messaging API 推播工具
"""
import os
import requests
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
TARGET_IDS = [t.strip() for t in os.getenv("LINE_TARGET_IDS", "").split(",") if t.strip()]

# Cloudinary 設定（用於上傳走勢圖）
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
}


def push_text(message: str, target_ids: list = None):
    """推播純文字訊息"""
    ids = target_ids or TARGET_IDS
    for uid in ids:
        payload = {
            "to": uid,
            "messages": [{"type": "text", "text": message}],
        }
        resp = requests.post(
            "https://api.line.me/v2/bot/message/push",
            headers=HEADERS,
            json=payload,
            timeout=10,
        )
        if resp.status_code == 200:
            print(f"✅ 推播成功 → {uid}")
        else:
            print(f"❌ 推播失敗 → {uid}：{resp.text}")


def push_image(image_path: str, alt_text: str = "走勢圖", target_ids: list = None):
    """上傳圖片到 Cloudinary，再推播圖片訊息"""
    ids = target_ids or TARGET_IDS
    # 上傳圖片
    result = cloudinary.uploader.upload(image_path, folder="line_bot")
    image_url = result["secure_url"]
    print(f"📤 圖片已上傳：{image_url}")

    for uid in ids:
        payload = {
            "to": uid,
            "messages": [
                {
                    "type": "image",
                    "originalContentUrl": image_url,
                    "previewImageUrl": image_url,
                }
            ],
        }
        resp = requests.post(
            "https://api.line.me/v2/bot/message/push",
            headers=HEADERS,
            json=payload,
            timeout=10,
        )
        if resp.status_code == 200:
            print(f"✅ 圖片推播成功 → {uid}")
        else:
            print(f"❌ 圖片推播失敗 → {uid}：{resp.text}")


def push_flex(flex_contents: dict, alt_text: str, target_ids: list = None):
    """推播 Flex Message（可做更漂亮的排版）"""
    ids = target_ids or TARGET_IDS
    for uid in ids:
        payload = {
            "to": uid,
            "messages": [
                {
                    "type": "flex",
                    "altText": alt_text,
                    "contents": flex_contents,
                }
            ],
        }
        resp = requests.post(
            "https://api.line.me/v2/bot/message/push",
            headers=HEADERS,
            json=payload,
            timeout=10,
        )
        if resp.status_code == 200:
            print(f"✅ Flex 推播成功 → {uid}")
        else:
            print(f"❌ Flex 推播失敗 → {uid}：{resp.text}")


def push_multiple_messages(messages: list, target_ids: list = None):
    """一次推播多則訊息（LINE 限制每次最多5則）"""
    ids = target_ids or TARGET_IDS
    # 每批最多5則
    for i in range(0, len(messages), 5):
        batch = messages[i:i+5]
        for uid in ids:
            payload = {"to": uid, "messages": batch}
            resp = requests.post(
                "https://api.line.me/v2/bot/message/push",
                headers=HEADERS,
                json=payload,
                timeout=10,
            )
            if resp.status_code != 200:
                print(f"❌ 批次推播失敗 → {uid}：{resp.text}")
