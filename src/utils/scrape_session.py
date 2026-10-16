"""
Cloudflare-clearance session helper for the batdongsan.com.vn scrapers.

batdongsan.com.vn now fronts requests with Cloudflare's managed JS challenge
("Just a moment...", `cf-mitigated: challenge` response header) -- curl_cffi's
TLS-fingerprint spoofing (impersonate="chrome124") alone no longer clears it,
since the challenge also runs a JS-based automation check. Plain Playwright
doesn't help either: it always sets `navigator.webdriver = True`, which is
exactly what that check looks for. `patchright` (a stealth-patched Playwright
build) hides that flag and clears the challenge; `headless=True` still gets
detected on other signals, so the browser has to run headed -- pushed
off-screen (`--window-position`) so it doesn't pop up a visible window. This
only works because these scrapers run on the maintainer's own Mac
(launchd/bare-metal), which has a real GUI session to open a window in.

The resulting `cf_clearance` cookie is valid site-wide (confirmed against
both listing pages and the `/Product/ProductSearch/*` API endpoints), so the
browser only needs to run once per TTL window -- every fast curl_cffi
request for the rest of a crawl just reuses the cached cookie.
"""
import concurrent.futures
import json
import os
import tempfile
import time

from curl_cffi import requests as curl_requests

from src.utils.common_tools import setup_logging

logger = setup_logging()

CACHE_PATH = os.path.join("data", "cf_session_cache.json")
TTL_SECONDS = int(os.getenv("CF_SESSION_TTL_SECONDS", "1200"))
WARM_URL = "https://batdongsan.com.vn/"

DEFAULT_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
DEFAULT_ACCEPT_LANGUAGE = "en-US,en;q=0.9"


def _read_cache():
    if not os.path.exists(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _write_cache(session_data):
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(session_data, f)


def _is_fresh(session_data, ttl_seconds=TTL_SECONDS):
    return session_data is not None and time.time() - session_data.get("warmed_at", 0) < ttl_seconds


def _warm_up():
    """Solve Cloudflare's managed challenge in a real, off-screen Chrome and
    return {"cookies": {...}, "user_agent": "...", "warmed_at": <epoch>}."""
    from patchright.sync_api import sync_playwright  # only the warm-up path needs a browser

    logger.info("Cloudflare session missing/stale -- warming up via off-screen Chrome...")
    with sync_playwright() as p:
        profile_dir = tempfile.mkdtemp(prefix="bds_cf_profile_")
        ctx = p.chromium.launch_persistent_context(
            profile_dir,
            headless=False,
            no_viewport=True,
            args=["--window-position=-2400,-2400", "--window-size=1280,800"],
        )
        try:
            page = ctx.new_page()
            user_agent = page.evaluate("navigator.userAgent")  # grab before navigating away
            page.goto(WARM_URL, wait_until="domcontentloaded", timeout=30000)
            for _ in range(15):
                if "Just a moment" not in page.title():
                    break
                page.wait_for_timeout(1000)
            else:
                raise RuntimeError("Cloudflare challenge did not clear within 15s")
            cookies = {c["name"]: c["value"] for c in ctx.cookies()}
        finally:
            ctx.close()

    if "cf_clearance" not in cookies:
        raise RuntimeError("Warm-up finished without obtaining a cf_clearance cookie")

    logger.info("Cloudflare clearance cookie obtained.")
    return {"cookies": cookies, "user_agent": user_agent, "warmed_at": time.time()}


def _warm_up_in_thread():
    """Run _warm_up() on a fresh thread. patchright's sync API refuses to run
    on a thread that already has an asyncio event loop active, which every
    call site here does (all 4 scrapers run inside asyncio.run()) -- a plain
    worker thread has no loop of its own, so this sidesteps that restriction
    without having to turn get_session()/callers into async code."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(_warm_up).result()


def get_session(force_refresh: bool = False):
    """
    Return (headers, cookies) for curl_cffi requests to batdongsan.com.vn,
    reusing the cached Cloudflare clearance cookie (data/cf_session_cache.json)
    while it's still fresh (CF_SESSION_TTL_SECONDS, default 1200s/20min).

    Pass force_refresh=True after a request comes back 403 mid-run (the
    cached cookie went stale before its soft TTL, or was never valid).
    """
    session_data = None if force_refresh else _read_cache()

    if not _is_fresh(session_data):
        # Re-check right before warming up: a sibling coroutine/process may have
        # refreshed it moments ago -- avoid opening a second browser for nothing.
        session_data = _read_cache()
        if not _is_fresh(session_data, ttl_seconds=60):
            session_data = _warm_up_in_thread()
            _write_cache(session_data)

    headers = {
        "User-Agent": session_data["user_agent"],
        "Accept": DEFAULT_ACCEPT,
        "Accept-Language": DEFAULT_ACCEPT_LANGUAGE,
    }
    return headers, session_data["cookies"]


def request_with_cf_bypass(url, **kwargs):
    """Sync GET via curl_cffi, attaching a Cloudflare session and retrying
    once with a freshly-warmed one if the first attempt comes back 403."""
    headers, cookies = get_session()
    response = curl_requests.get(url, headers=headers, cookies=cookies, impersonate="chrome124", **kwargs)
    if response.status_code == 403:
        logger.warning(f"403 for {url}, refreshing Cloudflare session and retrying once")
        headers, cookies = get_session(force_refresh=True)
        response = curl_requests.get(url, headers=headers, cookies=cookies, impersonate="chrome124", **kwargs)
    return response


async def async_get_with_cf_bypass(session, url, **kwargs):
    """Async GET via an existing curl_cffi AsyncSession (expected to already
    carry a warmed Cloudflare session as its default headers/cookies), retrying
    once with a freshly-warmed session if the first attempt comes back 403."""
    response = await session.get(url, impersonate="chrome124", **kwargs)
    if response.status_code == 403:
        logger.warning(f"403 for {url}, refreshing Cloudflare session and retrying once")
        headers, cookies = get_session(force_refresh=True)
        response = await session.get(url, headers=headers, cookies=cookies, impersonate="chrome124", **kwargs)
    return response
