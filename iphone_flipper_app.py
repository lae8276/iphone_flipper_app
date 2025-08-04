# iphone_flipper_app.py

import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time

BASE_URL = "https://www.ebay.co.uk"
SEARCH_URL = "https://www.ebay.co.uk/sch/i.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (CodeCopilot/1.0)"}

def build_query_url(query="iphone", page=1):
    params = {
        "_nkw": query,
        "_sacat": "0",
        "LH_Sold": "1",
        "LH_Auction": "1",
        "_ipg": "100",
        "_pgn": str(page),
        "rt": "nc"
    }
    return f"{SEARCH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

def extract_listing_data(item):
    try:
        title_tag = item.select_one(".s-item__title")
        if not title_tag or "Shop on eBay" in title_tag.text:
            return None
        title = title_tag.text.strip()

        model_match = re.search(r"iPhone\s?[\d\s\w\+]+", title, re.IGNORECASE)
        storage_match = re.search(r"(\d{2,4})\s?GB", title, re.IGNORECASE)

        model = model_match.group().strip() if model_match else "Unknown"
        storage = storage_match.group(1) + "GB" if storage_match else "Unknown"

        price_tag = item.select_one(".s-item__price")
        price = price_tag.text.replace("\u00a3", "").strip() if price_tag else "Unknown"

        bids_tag = item.select_one(".s-item__bids")
        bids = bids_tag.text.strip().split()[0] if bids_tag else "0"

        cond_tag = item.select_one(".SECONDARY_INFO")
        condition = cond_tag.text.strip() if cond_tag else "Unknown"

        loc_tag = item.select_one(".s-item__location.s-item__itemLocation")
        location = loc_tag.text.replace("Located in:", "").strip() if loc_tag else "Unknown"

        link_tag = item.select_one(".s-item__link")
        url = link_tag['href'] if link_tag else "Unknown"

        return {
            "Model": model,
            "Storage": storage,
            "Condition": condition,
            "Sold Price (GBP)": price,
            "Bids": bids,
            "Location": location,
            "Listing URL": url
        }

    except:
        return None

def scrape_ebay_auctions(query="iphone", pages=3, delay=1):
    results = []
    for page in range(1, pages + 1):
        url = build_query_url(query, page)
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")
        items = soup.select(".s-item")
        for item in items:
            data = extract_listing_data(item)
            if data:
                results.append(data)
        time.sleep(delay)
    return pd.DataFrame(results)

# --- Streamlit App ---
st.set_page_config(page_title="eBay iPhone Resale Scraper", layout="wide")
st.title("\ud83d\udcf1 iPhone Resale Auction Scanner (eBay UK)")

query = st.text_input("Search term", "iphone")
pages = st.slider("How many pages to scan?", 1, 10, 3)

if st.button("\ud83d\udd0d Scrape Listings"):
    with st.spinner("Scraping..."):
        df = scrape_ebay_auctions(query, pages)
        if not df.empty:
            st.success(f"Found {len(df)} listings.")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("\ud83d\udcc5 Download CSV", data=csv, file_name="iphone_auctions.csv", mime="text/csv")
        else:
            st.warning("No results found.")
