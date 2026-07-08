import streamlit as st
import sys
import asyncio
from playwright.sync_api import sync_playwright

st.title("Playwright Streamlit Test")

domain = st.text_input("Domain", "virtualemployee.com")

if st.button("Check Trustpilot"):
    try:
        # We need a proper way to run Playwright in Streamlit
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context()
            page = context.new_page()
            page.goto(f"https://www.trustpilot.com/review/{domain}", timeout=15000)
            
            st.success(f"Title: {page.title()}")
            browser.close()
    except Exception as e:
        st.error(f"Error: {type(e).__name__}: {str(e)}")
