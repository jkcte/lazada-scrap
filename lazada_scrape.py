# Lazada Scraper - Product Names, Links, Price, and Sold Count using Playwright (Python) with Pagination

from playwright.sync_api import sync_playwright
import json
import time

base_url = "https://www.lazada.com.ph"
search_url = f"{base_url}/tag/notebook-tablet/?q=notebook%20tablet"

all_products = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=100)
    context = browser.new_context()
    page = context.new_page()

    print(f"Navigating to {search_url}...")
    page.goto(search_url)

    while True:
        page.wait_for_selector('[data-qa-locator="product-item"]')

        print("Extracting products...")
        products = page.eval_on_selector_all(
            '[data-qa-locator="product-item"]',
            "els => els.map(el => {const name = el.querySelector('a[title]')?.getAttribute('title') || null;const link = el.querySelector('a')?.href || null;const price = el.querySelector('span.ooOxS')?.innerText || null;const sold = el.querySelector('span._1cEkb span')?.innerText || null;return { name, link, price, sold };})"
        )

        all_products.extend(products)
        print(f"Total collected: {len(all_products)}")

        try:
            next_locator = page.locator("li.ant-pagination-next button")
            if next_locator.is_enabled():
                next_locator.click()
                page.wait_for_selector('[data-qa-locator="product-item"]')
                time.sleep(1.5)
            else:
                print("No more pages or next button disabled.")
                break
        except Exception as e:
            print("Error during pagination:", e)
            break

    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)

    browser.close()
