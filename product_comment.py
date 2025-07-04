# Lazada Product Detail Scraper - Retry Until All Products Are Scraped

from playwright.sync_api import sync_playwright
import json
import time
import random
import math
import os

# Load product links
with open("products.json", "r", encoding="utf-8") as f:
    full_product_list = json.load(f)

# Load existing data if present
if os.path.exists("product_details.json"):
    with open("product_details.json", "r", encoding="utf-8") as f:
        detailed_data = json.load(f)
else:
    detailed_data = []

# Load skipped links if present
if os.path.exists("skipped_links.json"):
    with open("skipped_links.json", "r", encoding="utf-8") as f:
        skipped_links = json.load(f)
else:
    skipped_links = []

# Extract links already processed
processed_links = {d.get("link") for d in detailed_data}

# Retry loop: continue until there are no more unprocessed links
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=100)

    while True:
        remaining_products = [p for p in full_product_list if p.get("link") not in processed_links and p.get("link") not in skipped_links]
        if not remaining_products:
            print("All products processed. Exiting loop.")
            break

        print(f"Remaining to process: {len(remaining_products)}")
        rotation_limit = 50
        rotation_count = 0

        while rotation_count * rotation_limit < len(remaining_products):
            start = rotation_count * rotation_limit
            end = min(start + rotation_limit, len(remaining_products))
            context = browser.new_context()
            print(f"\n--- Rotation {rotation_count + 1}: Processing products {start + 1} to {end} ---\n")

            for idx in range(start, end):
                product = remaining_products[idx]
                link = product.get("link")
                if not link:
                    continue

                try:
                    page = context.new_page()
                    print(f"Visiting: {link}")
                    page.goto(link, timeout=30000)

                    if "/punish?" in page.url or "x5secdata" in page.url or "Just a moment" in page.title():
                        print(f"Blocked by CAPTCHA at {link}, skipping.")
                        skipped_links.append(link)
                        page.close()
                        continue

                    try:
                        page.wait_for_selector(".pdp-mod-product-badge-title", timeout=10000)
                    except:
                        print(f"Product title not found at {link}, skipping.")
                        skipped_links.append(link)
                        page.close()
                        continue

                    brand = None
                    if page.locator(".pdp-product-brand__brand-link").is_visible():
                        brand = page.locator(".pdp-product-brand__brand-link").inner_text()
                    product["brand"] = brand

                    try:
                        for _ in range(10):
                            page.mouse.wheel(0, 500)
                            time.sleep(0.5)
                            if page.locator(".mod-reviews").is_visible():
                                break
                        page.wait_for_selector(".mod-reviews", timeout=10000)
                    except:
                        print("Review section did not load.")
                        product["comments"] = []
                        detailed_data.append(product)
                        processed_links.add(link)
                        page.close()
                        time.sleep(random.expovariate(1/6) + 4)
                        continue

                    comments = []
                    review_items = page.locator(".mod-reviews .item")
                    count = review_items.count()

                    for i in range(min(5, count)):
                        try:
                            item = review_items.nth(i)
                            stars = item.locator(".container-star.starCtn.left .star").count()
                            comment = item.locator(".item-content .content").inner_text()
                            comments.append({"stars": stars, "comment": comment})
                        except Exception as e:
                            print("Review extraction error:", e)
                            continue

                    product["comments"] = comments
                    detailed_data.append(product)
                    processed_links.add(link)
                    page.close()
                    time.sleep(random.expovariate(1/6) + 4)

                except Exception as e:
                    print(f"Error processing {link}: {e}")
                    skipped_links.append(link)
                    time.sleep(random.expovariate(1/6) + 4)
                    continue

            context.close()
            rotation_count += 1

        with open("product_details.json", "w", encoding="utf-8") as f:
            json.dump(detailed_data, f, ensure_ascii=False, indent=2)

        with open("skipped_links.json", "w", encoding="utf-8") as f:
            json.dump(skipped_links, f, ensure_ascii=False, indent=2)

    browser.close()
