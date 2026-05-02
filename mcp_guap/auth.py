#!/usr/bin/env python3
"""Playwright-based authentication for GUAP.

This module provides browser automation to get session cookies from pro.guap.ru.
"""

import json
import asyncio
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright

GUAP_URL = "https://pro.guap.ru"
SSO_AUTH_URL = "https://sso.guap.ru/realms/master/protocol/openid-connect/auth"


async def ensure_playwright_browsers() -> bool:
    """Ensure playwright browsers are installed. Install if needed.
    
    Returns:
        True if browsers are available/installed, False otherwise
    """
    import subprocess
    import sys
    
    # Check if chromium is available using async API
    try:
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch()
                await browser.close()
                return True
            except Exception:
                pass
    except Exception:
        pass
    
    # Try to install
    print("🔧 Installing Playwright browsers (this may take 1-2 minutes)...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            print("✅ Playwright browsers installed successfully!")
            return True
        else:
            print(f"❌ Failed to install browsers: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing browsers: {e}")
        return False


async def authenticate_with_browser(
    save_path: Optional[Path] = None,
    timeout: int = 120,
    headless: bool = False,
) -> dict:
    """Authenticate via browser and extract session cookies.
    
    Args:
        save_path: Path to save cookies JSON file (default: cookie.json in package dir)
        timeout: Seconds to wait for user authentication
        headless: Run browser in headless mode (not recommended for auth)
    
    Returns:
        dict with 'success', 'cookies', 'cookie_string', 'save_path'
    """
    if save_path is None:
        save_path = Path(__file__).parent / "cookie.json"
    
    # Ensure browsers are installed
    if not await ensure_playwright_browsers():
        return {
            "success": False,
            "error": "Failed to install Playwright browsers. Please install manually: uvx playwright install chromium"
        }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("="*60)
        print("🔐 Авторизация в ГУАП")
        print("="*60)
        print(f"\nОткрываю {GUAP_URL}...")
        print("Пожалуйста, войдите в систему используя ваши учетные данные.")
        print(f"У вас есть {timeout} секунд на авторизацию.\n")
        
        # Открываем главную страницу
        await page.goto(GUAP_URL)
        
        # Кликаем на вход
        try:
            await page.click('text="Вход в личный кабинет"')
            print("✅ Перехожу на страницу авторизации...")
        except:
            print("⚠️  Не удалось найти кнопку входа, возможно уже на странице SSO")
        
        # Ждём пока URL изменится - это значит что авторизация прошла
        print("⏳ Ожидаю завершения авторизации...")
        print("   (URL должен измениться с sso.guap.ru на pro.guap.ru)")
        
        start_time = asyncio.get_event_loop().time()
        authenticated = False
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            current_url = page.url
            if "pro.guap.ru" in current_url and "sso.guap.ru" not in current_url:
                # Проверяем что мы на profile или другой внутренней странице
                if "/inside/" in current_url or current_url == GUAP_URL + "/":
                    authenticated = True
                    print(f"\n✅ Авторизация успешна!")
                    print(f"   Текущий URL: {current_url}")
                    break
            
            await asyncio.sleep(1)
        
        if not authenticated:
            await browser.close()
            return {
                "success": False,
                "error": f"Timeout: авторизация не завершена за {timeout} секунд",
            }
        
        # Получаем cookies
        cookies = await context.cookies()
        
        # Фильтруем только guap cookies
        guap_cookies = [
            c for c in cookies 
            if "guap.ru" in c.get("domain", "")
        ]
        
        if not guap_cookies:
            await browser.close()
            return {
                "success": False,
                "error": "No cookies found for guap.ru domain",
                "all_cookies": cookies,
            }
        
        # Формируем cookie string для HTTP заголовка
        cookie_parts = []
        for c in guap_cookies:
            cookie_parts.append(f"{c['name']}={c['value']}")
        cookie_string = "; ".join(cookie_parts)
        
        # Сохраняем в JSON
        cookie_data = {
            "url": GUAP_URL,
            "cookies": guap_cookies,
            "cookie_string": cookie_string,
            "domain": ".guap.ru",
        }
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(json.dumps(cookie_data, indent=2, ensure_ascii=False))
        
        print(f"\n🍪 Сохранено {len(guap_cookies)} cookies:")
        for c in guap_cookies:
            value_preview = c['value'][:50] + "..." if len(c['value']) > 50 else c['value']
            print(f"   {c['name']}: {value_preview}")
        
        print(f"\n💾 Cookies сохранены в: {save_path}")
        
        await browser.close()
        
        return {
            "success": True,
            "cookies": guap_cookies,
            "cookie_string": cookie_string,
            "save_path": str(save_path),
        }


def get_saved_cookie(cookie_file: Optional[Path] = None) -> Optional[str]:
    """Get cookie string from saved file.
    
    Args:
        cookie_file: Path to cookie.json file
    
    Returns:
        Cookie string or None if file doesn't exist
    """
    if cookie_file is None:
        # Пробуем разные пути
        for path in [
            Path(__file__).parent / "cookie.json",
            Path(__file__).parent.parent / "cookie.json",
        ]:
            if path.exists():
                cookie_file = path
                break
    
    if not cookie_file or not cookie_file.exists():
        return None
    
    try:
        data = json.loads(cookie_file.read_text())
        return data.get("cookie_string")
    except (json.JSONDecodeError, KeyError):
        # Если файл не JSON, пробуем прочитать как обычный cookie.txt
        return cookie_file.read_text().strip()


async def check_auth(cookie_string: Optional[str] = None) -> dict:
    """Check if current cookies are valid.
    
    Args:
        cookie_string: Cookie string to test. If None, loads from file.
    
    Returns:
        dict with 'valid' (bool) and 'user_info' if valid
    """
    import httpx
    
    if cookie_string is None:
        cookie_string = get_saved_cookie()
    
    if not cookie_string:
        return {"valid": False, "error": "No cookies provided or found"}
    
    try:
        async with httpx.AsyncClient(
            base_url=GUAP_URL,
            headers={
                "Cookie": cookie_string,
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            },
            follow_redirects=True,
            timeout=30,
        ) as client:
            response = await client.get("/inside/profile")
            
            # Проверяем что мы получили профиль, а не страницу логина
            if response.status_code == 200 and "login" not in response.text.lower():
                return {
                    "valid": True,
                    "status_code": response.status_code,
                    "url": str(response.url),
                }
            else:
                return {
                    "valid": False,
                    "status_code": response.status_code,
                    "error": "Invalid or expired cookies",
                }
                
    except Exception as e:
        return {"valid": False, "error": str(e)}


# CLI
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        # Check mode
        result = asyncio.run(check_auth())
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result.get("valid") else 1)
    else:
        # Auth mode
        result = asyncio.run(authenticate_with_browser())
        if result.get("success"):
            print("\n✅ Авторизация успешно завершена!")
            print(f"\nCookie string (для GUAP_COOKIE):")
            print(result["cookie_string"])
        else:
            print(f"\n❌ Ошибка: {result.get('error')}")
            sys.exit(1)
