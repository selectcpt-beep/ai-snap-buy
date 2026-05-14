"""
智普 GLM Coding 自动抢购脚本
用法:
  1. 先运行 login.py 完成登录
  2. 再运行 python snap_buy.py 开始监控抢购

核心策略:
  - 持续刷新页面检测购买按钮状态
  - 发现可购买时立即自动点击
  - 模拟真人操作节奏，降低反爬检测风险
"""
import os
import sys
import time
import random
import subprocess
from datetime import datetime

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

import config


def log(msg: str, level: str = "INFO") -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")


def play_sound() -> None:
    """播放系统提示音"""
    if not config.ENABLE_SOUND:
        return
    try:
        subprocess.run(["afplay", "/System/Library/Sounds/Ping.aiff"], check=False)
    except Exception:
        pass


def human_delay(min_ms: int = 200, max_ms: int = 800) -> None:
    """随机延迟，模拟人类操作"""
    time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))


def find_buy_button(page):
    """在页面上搜索购买/订阅按钮，返回 (状态, 按钮元素或None)

    状态: 'available' | 'sold_out' | 'too_many' | 'not_found'
    """
    for keyword in config.BUY_BUTTON_KEYWORDS:
        try:
            btn = page.get_by_text(keyword, exact=False).first
            if btn.is_visible():
                text = btn.text_content() or ""
                log(f"发现按钮: '{text.strip()}' (匹配关键词: '{keyword}')")

                for sold_keyword in config.SOLD_OUT_KEYWORDS:
                    if sold_keyword.lower() in text.lower():
                        return "sold_out", btn

                for too_keyword in config.TOO_MANY_KEYWORDS:
                    if too_keyword.lower() in text.lower():
                        return "too_many", btn

                return "available", btn
        except Exception:
            continue

    for selector in ["button", "a.btn", "a.button", "[role='button']", ".buy-btn", ".subscribe-btn"]:
        try:
            elements = page.locator(selector).all()
            for el in elements:
                if el.is_visible():
                    text = (el.text_content() or "").strip()
                    for keyword in config.BUY_BUTTON_KEYWORDS:
                        if keyword.lower() in text.lower():
                            log(f"通过选择器 '{selector}' 发现按钮: '{text}'")

                            for sold_keyword in config.SOLD_OUT_KEYWORDS:
                                if sold_keyword.lower() in text.lower():
                                    return "sold_out", el

                            for too_keyword in config.TOO_MANY_KEYWORDS:
                                if too_keyword.lower() in text.lower():
                                    return "too_many", el

                            return "available", el
        except Exception:
            continue

    return "not_found", None


def check_page_text(page) -> dict:
    """检查页面文本，返回状态摘要"""
    try:
        body_text = page.text_content("body") or ""
    except Exception:
        body_text = ""

    result = {
        "has_sold_out": False,
        "has_too_many": False,
        "has_buy": False,
    }

    lower = body_text.lower()
    for kw in config.SOLD_OUT_KEYWORDS:
        if kw.lower() in lower:
            result["has_sold_out"] = True
            break
    for kw in config.TOO_MANY_KEYWORDS:
        if kw.lower() in lower:
            result["has_too_many"] = True
            break
    for kw in config.BUY_BUTTON_KEYWORDS:
        if kw.lower() in lower:
            result["has_buy"] = True
            break

    return result


def attempt_purchase(page, button) -> bool:
    """尝试点击购买按钮并完成后续流程"""
    try:
        log(">>> 开始尝试购买...", "ACTION")

        page.evaluate("""(el) => {
            el.scrollIntoView({behavior: 'smooth', block: 'center'});
        }""", button)
        human_delay(300, 600)

        button.click(force=True)
        human_delay(500, 1000)

        log("已点击购买按钮，等待页面响应...", "ACTION")
        page.wait_for_timeout(3000)

        page_text = page.text_content("body") or ""

        if any(kw.lower() in page_text.lower() for kw in ["确认", "提交", "支付", "付款"]):
            log("检测到确认/支付页面，尝试点击确认...", "ACTION")

            for confirm_keyword in ["确认", "提交", "支付", "确定", "立即支付", "确认支付"]:
                try:
                    confirm_btn = page.get_by_text(confirm_keyword, exact=False).first
                    if confirm_btn.is_visible():
                        human_delay(200, 500)
                        confirm_btn.click(force=True)
                        log(f"已点击 '{confirm_keyword}' 按钮", "SUCCESS")
                        page.wait_for_timeout(3000)
                        break
                except Exception:
                    continue

            log("!!! 购买流程已执行完毕，请检查是否成功 !!!", "SUCCESS")
            return True

        elif any(kw.lower() in page_text.lower() for kw in ["成功", "完成", "恭喜"]):
            log("!!! 检测到成功提示，购买可能已完成 !!!", "SUCCESS")
            return True

        else:
            log("购买按钮已点击，后续页面需要人工确认（请查看浏览器）", "WARN")
            return True

    except Exception as e:
        log(f"购买操作失败: {e}", "ERROR")
        return False


def main():
    print("=" * 60)
    print("  智普 GLM Coding 自动抢购工具")
    print("=" * 60)
    print()

    if not os.path.exists(config.AUTH_STATE_FILE):
        log("未找到登录状态文件！请先运行: python login.py", "ERROR")
        sys.exit(1)

    log(f"目标网址: {config.TARGET_URL}")
    log(f"检测间隔: {config.CHECK_INTERVAL_SECONDS}s (普通) / {config.FAST_CHECK_INTERVAL_SECONDS}s (快速)")
    log(f"无头模式: {'开启' if config.HEADLESS else '关闭（可观察浏览器操作）'}")
    log("开始监控...按 Ctrl+C 停止\n")

    start_time = time.time()
    attempt_count = 0
    fast_mode = False

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=config.HEADLESS,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )
        context = browser.new_context(
            viewport=config.VIEWPORT,
            user_agent=config.USER_AGENT,
            storage_state=config.AUTH_STATE_FILE,
        )

        page = context.new_page()
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
            window.chrome = { runtime: {} };
        """)

        page.goto(config.TARGET_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        try:
            while True:
                attempt_count += 1

                if config.MAX_RUNTIME_SECONDS > 0:
                    elapsed = time.time() - start_time
                    if elapsed > config.MAX_RUNTIME_SECONDS:
                        log(f"已达到最大运行时间 {config.MAX_RUNTIME_SECONDS}s，停止监控", "INFO")
                        break

                log(f"第 {attempt_count} 次检测...", "INFO")

                state_summary = check_page_text(page)

                if not state_summary["has_buy"]:
                    log("当前页面未检测到购买相关文本，刷新页面...")
                    page.reload(wait_until="domcontentloaded")
                    page.wait_for_timeout(2000 + random.randint(0, 1000))
                    fast_mode = False
                else:
                    if state_summary["has_sold_out"]:
                        log("状态: 已售罄 | 刷新中...")
                        page.reload(wait_until="domcontentloaded")
                        page.wait_for_timeout(1000 + random.randint(0, 500))
                        fast_mode = True
                    elif state_summary["has_too_many"]:
                        log("状态: 人数过多/稍后再试 | 快速刷新中...")
                        page.reload(wait_until="domcontentloaded")
                        page.wait_for_timeout(1000 + random.randint(0, 500))
                        fast_mode = True
                    else:
                        status, button = find_buy_button(page)
                        log(f"检测结果: {status}")

                        if status == "available":
                            log("!!! 发现可购买！立即执行购买操作 !!!", "ACTION")
                            play_sound()
                            play_sound()

                            success = attempt_purchase(page, button)
                            if success:
                                log("购买流程已触发，请检查浏览器确认结果", "SUCCESS")
                                play_sound()
                                play_sound()
                                play_sound()
                                time.sleep(10)
                                break
                            else:
                                log("购买尝试失败，继续监控...", "WARN")

                        elif status == "not_found":
                            log("未找到购买按钮，刷新页面...")
                            page.reload(wait_until="domcontentloaded")
                            page.wait_for_timeout(1500 + random.randint(0, 1000))

                        else:
                            log(f"当前不可购买 (状态: {status})，刷新中...")
                            page.reload(wait_until="domcontentloaded")
                            page.wait_for_timeout(1000 + random.randint(0, 500))

                interval = config.FAST_CHECK_INTERVAL_SECONDS if fast_mode else config.CHECK_INTERVAL_SECONDS
                jitter = random.uniform(0, 0.5)
                time.sleep(interval + jitter)

        except KeyboardInterrupt:
            log("\n用户中断，停止监控", "INFO")
        finally:
            browser.close()

    log("程序结束", "INFO")


if __name__ == "__main__":
    main()
