"""
登录辅助脚本 —— 手动登录一次后保存浏览器状态
用法: python login.py

注意: 登录后页面会自动跳转，脚本自动检测并保存状态
"""
import time
from playwright.sync_api import sync_playwright
import config


def is_logged_in(page) -> bool:
    """通过检查登录按钮是否消失来判断是否已登录"""
    try:
        return not page.get_by_text("登录 / 注册", exact=False).first.is_visible(timeout=1000)
    except Exception:
        return True


def main():
    print("=" * 60)
    print("  智谱AI GLM Coding 登录助手")
    print("=" * 60)
    print()
    print("正在打开浏览器...")
    print("【操作步骤】")
    print("  1. 浏览器打开后，点击「登录/注册」按钮")
    print("  2. 用手机号/邮箱登录 或 扫码登录")
    print("  3. 登录成功后页面会自动跳回首页")
    print("  4. 脚本会自动检测到登录状态并保存")
    print("  (最多等待 5 分钟)")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            viewport=config.VIEWPORT,
            user_agent=config.USER_AGENT,
        )
        page = context.new_page()
        page.goto("https://bigmodel.cn", timeout=60000)
        time.sleep(2)

        if is_logged_in(page):
            print("[*] 检测到已登录，直接跳转目标页面")
        else:
            print("[*] 请点击「登录/注册」按钮并完成登录...")
            for i in range(300, 0, -1):
                if is_logged_in(page):
                    print("\n[*] 检测到登录成功！")
                    break
                if i % 30 == 0:
                    print(f"[*] 等待中... 剩余 {i//60} 分 {i%60} 秒")
                time.sleep(1)
            else:
                print("\n[!] 登录等待超时，请重新运行脚本")
                browser.close()
                return

        page.goto(config.TARGET_URL, timeout=60000)
        time.sleep(3)

        context.storage_state(path=config.AUTH_STATE_FILE)
        print(f"[OK] 登录状态已保存到: {config.AUTH_STATE_FILE}")
        browser.close()


if __name__ == "__main__":
    main()
