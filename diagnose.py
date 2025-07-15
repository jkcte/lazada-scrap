from playwright.sync_api import sync_playwright
import json
import time
import random
from datetime import datetime

PRODUCTS_FILE = 'filtered_data_part1.json'

with open(PRODUCTS_FILE, encoding='utf-8') as f:
    products = json.load(f)

USER_DATA_DIR = r"C:\Users\Owner\AppData\Local\Google\Chrome\User Data"

with sync_playwright() as p:
    browser_context = p.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        headless=False,
        viewport={"width": 1280, "height": 800},
        slow_mo=100,
    )
    page = browser_context.new_page()

    for product in products:
        # 🚦 Skip if reviews already exist
        if "reviews" in product:
            print(f"⏩ Skipping (already processed): {product['link']}")
            continue

        url = product["link"]
        print(f"🌐 Visiting: {url}")
        
        try:
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
        except:
            print(f"❌ Failed to load page: {url}")
            continue

        time.sleep(random.uniform(2, 4))
        page.keyboard.press("PageDown")
        time.sleep(random.uniform(2, 4))

        if "punish" in page.url:
            print(f"🚧 CAPTCHA detected at {page.url}. Solve manually and press Enter to continue...")
            input()

        # 📋 Scrape other product fields
        brand_el = page.query_selector(".pdp-product-brand__brand-link")
        avg_rating_el = page.query_selector(".score-average")
        ratings_count_el = page.query_selector(".count")
        highlights_els = page.query_selector_all(".pdp-product-highlights ul li")
        description_el = page.query_selector(".pdp-product-detail .detail-content")
        specs_el = page.query_selector(".pdp-product-specification")

        product["brand"] = brand_el.inner_text().strip() if brand_el else None
        product["avg_rating"] = avg_rating_el.inner_text().strip() if avg_rating_el else None
        product["ratings_count"] = ratings_count_el.inner_text().strip() if ratings_count_el else None
        product["highlights"] = [el.inner_text().strip() for el in highlights_els] if highlights_els else []
        product["description"] = description_el.inner_text().strip() if description_el else None
        product["specifications"] = specs_el.inner_text().strip() if specs_el else None

        # Scroll to reviews section
        page.evaluate("document.querySelector('#block-HvK2CIMcYsU')?.scrollIntoView()")
        time.sleep(2)

        # Detect if no reviews exist
        mod_empty = page.query_selector(".mod-empty")
        if mod_empty:
            print("❌ No reviews found on this product page (mod-empty detected).")
            product["reviews"] = []
            with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            continue

        try:
            page.wait_for_selector(".item-top", timeout=15000)
            print("✅ Reviews found.")
        except:
            print("❌ Reviews not found within 15s. Skipping product.")
            product["reviews"] = []
            with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            continue

        reviews = []
        page_num = 1

        while True:
            print(f"🔎 Scraping reviews page {page_num}...")
            review_items = page.query_selector_all(".item-top")

            if not review_items:
                print("⚠️ No reviews found on this page.")
                break

            for idx, review_top in enumerate(review_items):
                review_container = review_top.evaluate_handle("el => el.closest('.item') || el")

                reviewer_el = review_container.query_selector(".item-top .reviewer")
                date_el = review_container.query_selector(".item-top .time")
                stars = len(review_container.query_selector_all(".item-middle .container-star .star"))
                sku_info_el = review_container.query_selector(".skuInfo-value")
                text_el = review_container.query_selector(".item-content-main-content-reviews-item span")

                review_data = {
                    "reviewer": reviewer_el.inner_text().strip() if reviewer_el else None,
                    "date": date_el.inner_text().strip() if date_el else None,
                    "rating": stars,
                    "sku_info": sku_info_el.inner_text().strip() if sku_info_el else None,
                    "text": text_el.inner_text().strip() if text_el else None,
                    "scraped_at": datetime.now().isoformat()
                }

                print(f"    {review_data}")
                reviews.append(review_data)

            # Pagination
            next_li = page.query_selector("ul.iweb-pagination.review-pagination li.iweb-pagination-next")
            if next_li:
                is_disabled = next_li.get_attribute("aria-disabled")
                if is_disabled == "true":
                    print("✅ No more review pages.")
                    break
                else:
                    next_button = next_li.query_selector("button.iweb-pagination-item-link")
                    if next_button:
                        print("➡️ Moving to next page of reviews...")
                        next_button.click()
                        time.sleep(random.uniform(3, 5))
                        page_num += 1
                    else:
                        print("⚠️ Next button not found.")
                        break
            else:
                print("✅ No pagination element found — done.")
                break

        product["reviews"] = reviews

        with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
            json.dump(products, f, indent=2, ensure_ascii=False)

        print(f"📦 Finished scraping {len(reviews)} reviews for: {product['link']}")
        time.sleep(random.uniform(5, 10))

    browser_context.close()

print("🎉 All products scraped.")
