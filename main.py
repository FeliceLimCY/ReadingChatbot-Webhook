from flask import Flask, request, jsonify
import pandas as pd
from deep_translator import GoogleTranslator
from langdetect import detect
import re

app = Flask(__name__)

# ----------------------
# Helper: Clean dates
# ----------------------
def clean_date(value):
    """Convert Excel serial or datetime to string, keep text unchanged."""
    try:
        if isinstance(value, (float, int)):  
            # Convert Excel serial numbers to proper date
            return pd.to_datetime(value, origin="1899-12-30", unit="D").strftime("%d/%m/%Y")
        elif pd.api.types.is_datetime64_any_dtype(type(value)):  
            # If it's already a datetime object
            return pd.to_datetime(value).strftime("%d/%m/%Y")
        else:
            # Keep as string if already like '2005' or '2000-09'
            return str(value)
    except:
        return str(value)

# ----------------------
# Load dataset
# ----------------------
books_df = pd.read_excel("Books.xlsx", dtype={"published_date": str})

# Apply cleaning to published_date column
if "published_date" in books_df.columns:
    books_df["published_date"] = books_df["published_date"].apply(clean_date)

# -------------
# Translation
# -------------
def translate_to_english(text: str) -> str:
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except Exception as e:
        print(f"[ERROR] Translation to English failed: {e}")
        return text

def translate_back(text: str, target_lang: str) -> str:
    try:
        if target_lang != "en":
            return GoogleTranslator(source="en", target=target_lang).translate(text)
        return text
    except Exception as e:
        print(f"[ERROR] Back translation failed: {e}")
        return text

# --------------------------
# Safe language detection
# --------------------------
def safe_detect_language(text: str) -> str:
    try:
        lang = detect(text)
        if lang != "en":
            if re.fullmatch(r"[A-Za-z0-9\s\?\!\'\,\.]+", text):
                print(f"[DEBUG] Overriding langdetect result ({lang}) -> en")
                return "en"
        return lang
    except:
        return "en"

# --------------------------
# Health check endpoint
# --------------------------
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    return "Webhook endpoint is live! Please use POST requests for Dialogflow.", 200

# --------------------------
# Main webhook endpoint
# --------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json(force=True)
    query_text = req.get("queryResult", {}).get("queryText", "")
    intent = req.get("queryResult", {}).get("intent", {}).get("displayName", "")
    params = req.get("queryResult", {}).get("parameters", {})

    detected_lang = safe_detect_language(query_text)
    translated_query = translate_to_english(query_text)

    print("\n[DEBUG] -------------------------")
    print(f"Original query   : {query_text}")
    print(f"Translated query : {translated_query}")
    print(f"Detected lang    : {detected_lang}")
    print(f"Intent           : {intent}")
    print("-------------------------------\n")

    response_text = "Sorry, I didn’t get that."

    # ----------------------
    # Intent: greet
    # ----------------------
    if intent == "greet":
        response_text = "Hello! How can I help you with books today?"

    # ----------------------
    # Intent: goodbye
    # ----------------------
    elif intent == "goodbye":
        response_text = "Goodbye! Happy reading 📖"

    # ----------------------
    # Intent: search_book
    # ----------------------
    elif intent == "search_book":
        title = str(params.get("book_title", "")).lower()
        if title:
            safe_title = re.escape(title)
            match = books_df[books_df["title"].str.lower().str.contains(safe_title, na=False, regex=True)]
            if not match.empty:
                row = match.iloc[0]
                response_text = f"""I found a book 📕 for you!            
Title: {row['title']}
Author: {row['author']}
Genre: {row['genre']}
Publisher: {row['publisher']}
Published Date: {row['published_date']}
Pages: {row['pages']}
Average Rating: {row['average_rating']}
Description: {row['description']}
Thumbnail: {row['thumbnail']}"""            
            else:
                row = books_df.sample(1).iloc[0]
                response_text = f"""Sorry, I couldn’t find a book titled '{title}'. 
How about this one instead?
Title: {row['title']}
Author: {row['author']}
Publisher: {row['publisher']}
Published Date: {row['published_date']}
Pages: {row['pages']}
Average Rating: {row['average_rating']}
Description: {row['description']}
Thumbnail: {row['thumbnail']}"""  
        else:                
            row = books_df.sample(1).iloc[0]
            response_text = f"""I recommend this book for you:
Title: {row['title']}
Author: {row['author']}
Genre: {row['genre']}
Publisher: {row['publisher']}
Published Date: {row['published_date']}
Pages: {row['pages']}
Average Rating: {row['average_rating']}
Description: {row['description']}
Thumbnail: {row['thumbnail']}"""

    # ----------------------
    # Intent: published_date
    # ----------------------
    elif intent == "published_date":
        title = str(params.get("book_title", "")).lower()
        safe_title = re.escape(title)
        match = books_df[books_df["title"].str.lower().str.contains(safe_title, na=False, regex=True)]
        if not match.empty:
            row = match.iloc[0]
            response_text = f"'{row['title']}' was published on {row['published_date']}."
        else:
            response_text = f"Sorry, I couldn’t find the published date for '{title}'."

    # ----------------------
    # Intent: other handlers (author, genre, etc.)
    # ----------------------
    # ... keep your other intents (search_author, search_by_genre, etc.) unchanged ...

    response_text = translate_back(response_text, detected_lang)

    print(f"[DEBUG] Final response (before sending): {response_text}\n")

    return jsonify({"fulfillmentText": response_text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
