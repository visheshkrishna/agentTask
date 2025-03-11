# verify_total_customers.py
import os
import sys
import time
import traceback
from playwright.sync_api import sync_playwright

def main():
    print("=== VERIFY TOTAL CUSTOMERS TEST START ===")
    url = os.environ.get("TEST_URL", "https://qacrmdemo.netlify.app")
    headless = False

    try:
        with sync_playwright() as pw:
            print("[Playwright initialized]")
            browser = pw.chromium.launch(headless=headless, args=["--start-maximized"])
            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            print("[New page created]")

            # Go to the dashboard and get the total count
            page.goto(url)
            page.wait_for_load_state("networkidle")
            print("[Dashboard loaded]")

            try:
                total_card = page.locator("h3:text('Total Customers')").locator("xpath=../..")
                page.wait_for_timeout(1000)
                dashboard_total = int(total_card.locator(".text-4xl").text_content(timeout=10000).strip())
                print(f"[Dashboard reports total customers: {dashboard_total}]")
            except Exception as e:
                print("[Error] 'Total Customers' element not found within the timeout period.")
                raise e

            # Now go to the customers page
            page.goto(f"{url}/customers")
            page.wait_for_load_state("networkidle")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)

            total_counted = 0
            while True:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1000)
                rows = page.locator("table tbody tr")
                row_count = rows.count()
                total_counted += row_count
                print(f"[Found {row_count} customers on current page, total so far: {total_counted}]")

                next_span = page.locator("nav[aria-label='pagination'] span:text('Next')")
                if next_span.count() == 0:
                    print("[Next button span not found]")
                    break

                next_button = next_span.first.locator("xpath=..")

                try:
                    if next_button.get_attribute("aria-disabled") == "true":
                        print("[Reached last page - next button disabled]")
                        break

                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(1000)

                    parent = next_button
                    parent.click(timeout=10000)
                    print("[Navigated to the next page]")
                    page.wait_for_timeout(2000)
                except Exception as click_error:
                    print(f"[Next button is not interactable, ending pagination] - {click_error}")
                    break

            browser.close()
            print(f"[Total customers counted via pagination: {total_counted}]")

            if total_counted == dashboard_total:
                print("[SUCCESS] Customer count matches dashboard!")
                return 0
            else:
                print(f"[FAIL] Count mismatch: Dashboard={dashboard_total}, Counted={total_counted}")
                return 1

    except Exception as e:
        print(f"[Test error] {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
