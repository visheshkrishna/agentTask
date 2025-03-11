# -*- coding: utf-8 -*-
import os
import sys
import time
import traceback
from playwright.sync_api import sync_playwright

def main():
    print("=== CUSTOMER FORM TEST START ===")
    url = os.environ.get("TEST_URL", "https://qacrmdemo.netlify.app")
    headless = False

    customer_name = f"Test Customer {int(time.time())}"
    success = False

    try:
        with sync_playwright() as pw:
            print("[Playwright initialized]")
            browser = pw.chromium.launch(headless=headless, args=["--start-maximized"])
            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            print("[New page created]")

            page.goto(f"{url}/customers")
            page.wait_for_load_state("networkidle")
            print("[Navigated to /customers]")

            page.locator("text=Add Customer").first.click()
            print("[Clicked 'Add Customer' button]")

            page.locator("form input").nth(0).wait_for(timeout=5000)
            print("[Form loaded]")

            inputs = page.locator("form input")
            fields = [
                customer_name,
                f"{int(time.time())}@test.com",
                "1234567890",
                "QA Co.",
                "REG12345",
                "VAT98765",
                "123 Automation Street",
                "54321",
                "Testville",
                "Testland"
            ]
            for i, value in enumerate(fields):
                inputs.nth(i).fill(value)
                print(f"[Field {i+1} filled: {value}]")
                time.sleep(1)

            print("[All form fields filled]")
            page.locator("button[type='submit']").click()
            print("[Form submitted]")
            page.wait_for_timeout(3000)

            print("[Scrolling to bottom to reveal pagination]")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)

            # Ensure pagination is visible
            pagination_selector = "nav[aria-label='pagination']"
            try:
                page.wait_for_selector(pagination_selector, state="visible", timeout=10000)
                print("[Pagination found]")
            except:
                print("[Pagination not found]")
                return 1

            # Paginate and search
            while True:
                page.wait_for_timeout(1000)
                if page.locator(f"text={customer_name}").first.is_visible():
                    print(f"[Customer '{customer_name}' found on the current page!]")
                    success = True
                    break

                next_button = page.locator("nav[aria-label='pagination'] >> text=Next")
                if not next_button or next_button.is_disabled():
                    print(f"[Customer '{customer_name}' not found after pagination.]")
                    break

                next_button.click()
                print("[Navigated to the next page]")
                page.wait_for_timeout(2000)

            browser.close()
            print("[Browser closed]")

    except Exception as e:
        print(f"[Test error] {str(e)}")
        traceback.print_exc()

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
