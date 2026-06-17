import sys
import json
import re
from playwright.sync_api import sync_playwright

def check(platform, target):
    platform = platform.lower()
    
    result = {
        "exists": False,
        "url": "",
        "verification_status": "checked",
        "rating": None,
        "review_count": None,
        "error_message": ""
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()

            try:
                if platform == "trustpilot":
                    clean_domain = target.replace("www.", "")
                    url = f"https://www.trustpilot.com/review/{clean_domain}"
                    result["url"] = url
                    page.goto(url, timeout=30000)
                    
                    try:
                        page.wait_for_function('() => !document.title.includes("Verifying Connection")', timeout=15000)
                        page.wait_for_timeout(2000)
                    except Exception:
                        pass

                    title = page.title()
                    if "Trustpilot" in title or "Reviews" in title:
                        result["exists"] = True
                        text = page.content()
                        rating_match = re.search(r'"ratingValue"\s*:\s*"?([\d.]+)"?', text)
                        if rating_match:
                            try: result["rating"] = float(rating_match.group(1))
                            except ValueError: pass
                                
                        count_match = re.search(r'"reviewCount"\s*:\s*"?(\d+)"?', text)
                        if count_match:
                            try: result["review_count"] = int(count_match.group(1))
                            except ValueError: pass

                elif platform == "clutch":
                    # target is the slug (e.g. valuecoders)
                    slug = target.lower().replace(" ", "-").replace(".", "-")
                    url = f"https://clutch.co/profile/{slug}"
                    result["url"] = url
                    
                    # Bypass CF
                    page.goto(url, timeout=30000)
                    try:
                        page.wait_for_function('() => !document.title.includes("Just a moment")', timeout=15000)
                        page.wait_for_timeout(2000)
                    except Exception:
                        pass
                        
                    text = page.content()
                    if "clutch" in text.lower() and "review" in text.lower():
                        result["exists"] = True
                        rating_match = re.search(r'"ratingValue"\s*:\s*"?([\d.]+)"?', text)
                        if rating_match:
                            try: result["rating"] = float(rating_match.group(1))
                            except ValueError: pass

                elif platform == "g2":
                    slug = target.lower().replace(" ", "-")
                    url = f"https://www.g2.com/products/{slug}/reviews"
                    result["url"] = url
                    
                    # Bypass CF
                    page.goto(url, timeout=30000)
                    try:
                        page.wait_for_function('() => !document.title.includes("Just a moment")', timeout=15000)
                        page.wait_for_timeout(2000)
                    except Exception:
                        pass
                        
                    if "g2.com" in page.url:
                        text = page.content()
                        if "review" in text.lower():
                            result["exists"] = True
                            rating_match = re.search(r'"ratingValue"\s*:\s*"?([\d.]+)"?', text)
                            if rating_match:
                                try: result["rating"] = float(rating_match.group(1))
                                except ValueError: pass

                elif platform == "google_business":
                    from urllib.parse import quote
                    url = f"https://www.google.com/maps/search/{quote(target)}"
                    result["url"] = url
                    
                    page.goto(url, timeout=30000)
                    page.wait_for_timeout(3000)
                    
                    text = page.content()
                    if "Directions" in text and "Save" in text:
                        result["exists"] = True
                        
                        # Try a couple of common regexes for rating (optional)
                        rating_match = re.search(r'aria-label="([\d\.]+)\s*stars[\s\S]{1,50}?([\d\,]+)\s*Reviews"', text)
                        if rating_match:
                            try: result["rating"] = float(rating_match.group(1))
                            except ValueError: pass
                            try: result["review_count"] = int(rating_match.group(2).replace(",", ""))
                            except ValueError: pass

            except Exception as e:
                result["verification_status"] = "error"
                result["error_message"] = str(e)[:150]
            finally:
                browser.close()
    except Exception as e:
        result["verification_status"] = "error"
        result["error_message"] = str(e)[:150]
        
    print(json.dumps(result))

if __name__ == "__main__":
    if len(sys.argv) > 2:
        check(sys.argv[1], sys.argv[2])
