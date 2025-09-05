from flask import Flask, request, jsonify
import pandas as pd
from deep_translator import GoogleTranslator
from langdetect import detect
import re
from datetime import datetime, timedelta

app = Flask(__name__)

# --------------------------
# Excel Date Fix Function
# --------------------------
def excel_date_to_str(value) -> str:
    """Convert Excel cell values into readable dates or keep original text/year."""
    try:
        # If it's empty or NaN
        if pd.isna(value):
            return ""

        # Already string → keep as-is (covers '2000-09', '2005', '04/03/2013')
        if isinstance(value, str):
            return value.strip()

        # If it's a number (int/float)
        if isinstance(value, (int, float)):
            num = int(value)

            # If it's clearly a year (1000–2100) → keep as year
            if 1000 <= num <= 2100:
                return str(num)

            # If it's within Excel serial date range
            if 30 < num < 60000:
                base_date = datetime(1899, 12, 30)
                fixed_date = base_date + timedelta(days=num)
                return fixed_date.strftime("%d/%m/%Y")

            return str(num)  # fallback

        # If it's a datetime object
        if isinstance(value, datetime):
            return value.strftime("%d/%m/%Y")

        return str(value)

    except Exception:
        return str(value)
        
# --------------------------
# Load dataset
# --------------------------
books_df = pd.read_excel("Books.xlsx", dtype=str)

# Fix published_date column
if "published_date" in books_df.columns:
    books_df["published_date"] = books_df["published_date"].apply(excel_date_to_str)

# -------------
# Translation
# -------------
def translate_to_english(text: str) -> str:
    """Translate text to English."""
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except Exception as e:
        print(f"[ERROR] Translation to English failed: {e}")
        return text

def translate_back(text: str, target_lang: str) -> str:
    """Translate English response back to original language."""
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
    """Detect language, force English if only ASCII letters/punctuation are found."""
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

    # Detect user language
    detected_lang = safe_detect_language(query_text)

    # Translate to English
    translated_query = translate_to_english(query_text)

    # Debug log
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
    # Intent: search_author
    # ----------------------
    elif intent == "search_author":
        author = str(params.get("author", "")).lower()
        if author:
            safe_author = re.escape(author)
            match = books_df[books_df["author"].str.lower().str.contains(safe_author, na=False, regex=True)]
            if not match.empty:
                titles = "\n".join(match["title"].tolist()[:5])
                response_text = f"Books by {author.title()}:\n{titles}"
            else:
                response_text = f"Sorry, I couldn’t find books from {author}."
        else:
            response_text = "Please provide an author name."

    # ----------------------
    # Intent: book_page
    # ----------------------
    elif intent == "book_page":
        title = str(params.get("book_title", "")).lower()
        safe_title = re.escape(title)
        match = books_df[books_df["title"].str.lower().str.contains(safe_title, na=False, regex=True)]
        if not match.empty:
            row = match.iloc[0]
            response_text = f"'{row['title']}' has {row['pages']} pages."
        else:
            response_text = f"Sorry, I couldn’t find page count for '{title}'."

    # ----------------------
    # Intent: search_by_genre
    # ----------------------
    elif intent == "search_by_genre":
        genre = str(params.get("genre", "")).lower()
        safe_genre = re.escape(genre)
        match = books_df[books_df["genre"].str.lower().str.contains(safe_genre, na=False, regex=True)]
        if not match.empty:
            titles = "\n".join(match["title"].tolist()[:5])
            response_text = f"Here are some {genre.title()} books:\n{titles}"
        else:
            response_text = f"Sorry, I couldn’t find books in the {genre} genre."

    # ----------------------
    # Intent: get_book_genre
    # ----------------------
    elif intent == "get_book_genre":
        title = str(params.get("book_title", "")).lower()
        safe_title = re.escape(title)
        match = books_df[books_df["title"].str.lower().str.contains(safe_title, na=False, regex=True)]
        if not match.empty:
            row = match.iloc[0]
            response_text = f"'{row['title']}' belongs to the {row['genre']} genre."
        else:
            response_text = f"Sorry, I couldn’t find genre for '{title}'."

    # ----------------------
    # Intent: book_description
    # ----------------------
    elif intent == "book_description":
        title = str(params.get("book_title", "")).lower()
        safe_title = re.escape(title)
        match = books_df[books_df["title"].str.lower().str.contains(safe_title, na=False, regex=True)]
        if not match.empty:
            row = match.iloc[0]
            response_text = f"'{row['title']}' description: {row['description']}"
        else:
            response_text = f"Sorry, I couldn’t find a description for '{title}'."

    # ------------------------
    # Intent: published_date
    # ------------------------
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
    # Intent: publisher
    # ----------------------
    elif intent == "publisher":
        title = str(params.get("book_title", "")).lower()
        safe_title = re.escape(title)
        match = books_df[books_df["title"].str.lower().str.contains(safe_title, na=False, regex=True)]
        if not match.empty:
            row = match.iloc[0]
            response_text = f"The publisher of '{row['title']}' is {row['publisher']}."
        else:
            response_text = f"Sorry, I couldn’t find the publisher for '{title}'."

    # ----------------------
    # Intent: average_rating
    # ----------------------
    elif intent == "average_rating":
        title = str(params.get("book_title", "")).lower()
        safe_title = re.escape(title)
        match = books_df[books_df["title"].str.lower().str.contains(safe_title, na=False, regex=True)]
        if not match.empty:
            row = match.iloc[0]
            response_text = f"'{row['title']}' has an average rating of {row['average_rating']}."
        else:
            response_text = f"Sorry, I couldn’t find ratings for '{title}'."

    # ----------------------
    # Intent: thumbnail
    # ----------------------
    elif intent == "thumbnail":
        title = str(params.get("book_title", "")).lower()
        safe_title = re.escape(title)
        match = books_df[books_df["title"].str.lower().str.contains(safe_title, na=False, regex=True)]
        if not match.empty:
            row = match.iloc[0]
            response_text = f"Here is the cover of '{row['title']}': {row['thumbnail']}"
        else:
            response_text = f"Sorry, I couldn’t find a cover for '{title}'."

    # ----------------------
    # Intent: bot_challenge
    # ----------------------
    elif intent == "bot_challenge":
        response_text = "I’m a book assistant bot 🤖, here to help you discover books!"

    # Translate back to user's language
    response_text = translate_back(response_text, detected_lang)

    print(f"[DEBUG] Final response (before sending): {response_text}\n")

    return jsonify({"fulfillmentText": response_text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


