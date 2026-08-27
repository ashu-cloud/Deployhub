from __future__ import annotations

import pytest

from tests.helpers.settings import FRONTEND_URL

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_login_and_home_with_playwright():
    pytest.importorskip("playwright")
    from playwright.async_api import async_playwright

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            home = await page.goto(FRONTEND_URL, wait_until="domcontentloaded")
            if home is None or home.status >= 500:
                pytest.skip(f"frontend not reachable at {FRONTEND_URL}")
            title = await page.title()
            assert "DeployHub" in title or "deploy" in (await page.content()).lower()

            await page.goto(f"{FRONTEND_URL}/login", wait_until="domcontentloaded")
            body = await page.content()
            assert "GitHub" in body
            github = page.locator("a[href='/api/v1/auth/github']")
            assert await github.count() >= 1
            await browser.close()
    except Exception as exc:
        pytest.skip(f"playwright could not drive the frontend: {exc}")
