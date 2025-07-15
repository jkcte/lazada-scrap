from playwright.sync_api import sync_playwright
import time

# 🔗 Lazada product page to test
PRODUCT_URL = "https://www.lazada.com.ph/products/pdp-i5127296455.html"

USER_DATA_DIR = r"C:\Users\Owner\AppData\Local\Google\Chrome\User Data"

with sync_playwright() as p:
    browser_context = p.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        headless=False,
        viewport={"width": 1280, "height": 800},
        slow_mo=100,
    )
    page = browser_context.new_page()

    print(f"🌐 Visiting: {PRODUCT_URL}")
    page.goto(PRODUCT_URL, timeout=60000)

    time.sleep(5)
    page.keyboard.press("PageDown")
    time.sleep(4)

    # CAPTCHA detection
    if "punish" in page.url:
        print("🚧 CAPTCHA detected. Solve it in browser, then press Enter here to continue…")
        input()

    # Scroll to reviews section
    page.evaluate("document.querySelector('#block-HvK2CIMcYsU')?.scrollIntoView()")
    time.sleep(4)

    # Close modal if it appears
    modal_close = page.query_selector(".baxia-dialog-close")
    if modal_close and modal_close.is_visible():
        print("ℹ️ Closing modal dialog.")
        modal_close.click()
        time.sleep(2)

    page_number = 1
    while True:
        print(f"\n🩺 Checking reviews on page {page_number}…")

        try:
            page.wait_for_selector(".item-top", timeout=15000)
            review_items = page.query_selector_all(".item-top")
            print(f"✅ Found {len(review_items)} review(s) on page {page_number}.")
        except:
            print(f"❌ No reviews found on page {page_number}.")
            break

        # Print pagination DOM
        pagination_dom = page.query_selector(".review-pagination")
        if pagination_dom:
            html = pagination_dom.inner_html()
            print(f"\n📄 Pagination DOM on page {page_number}:\n{'-'*40}\n{html}\n{'-'*40}")
        else:
            print("❌ No .review-pagination container found on page.")

        # Check Next button using new structure
        next_li = page.query_selector("li.iweb-pagination-next")

        if not next_li:
            print("❌ Next button container NOT found. Stopping.")
            break

        is_disabled = next_li.get_attribute("aria-disabled") == "true"
        if is_disabled:
            print("⚠️ Next button is disabled — last page.")
            break

        next_button = next_li.query_selector("button.iweb-pagination-item-link")
        if next_button:
            print("✅ Next button is enabled — clicking to next page.")
            next_button.click()
            page_number += 1
            time.sleep(5)  # wait for next page to load
        else:
            print("❌ Next button element not found inside container.")
            break

    print("\n🎯 Diagnostics complete.")
    input("Press Enter to close browser…")

    browser_context.close()
