from flask import Flask, request, jsonify
import pandas as pd
from deep_translator import GoogleTranslator

app = Flask(__name__)

# Load dataset
books_df = pd.read_excel("Books.xlsx")

# --------------------------
# Translation
# --------------------------
def translate_to_english(text: str) -> (str, str):
    """Translate text to English and detect language."""
    try:
        translated = GoogleTranslator(source="auto", target="en").translate(text)
        detected_lang = GoogleTranslator(source="auto", target="en").source
        return translated, detected_lang
    except Exception as e:
        print(f"[ERROR] Translation to English failed: {e}")
        return text, "en"

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

    #Translate to English
    translated_query, detected_lang = translate_to_english(corrected_query)

    #Debug log
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
        response_text = "Goodbye! Happy reading 📚"

    # ----------------------
    # Intent: search_book
    # ----------------------
    elif intent == "search_book":
        title = str(params.get("book_title", "")).lower()
        if title:
            match = books_df[books_df["title"].str.lower().str.contains(title, na=False)]
            if not match.empty:
                row = match.iloc[0]
                response_text = f"""I found '{row['title']}' by Author: {row['author']} 
                Genre: {row['genre']}
                Publisher: {row['publisher']}
                Publish Date: {row['publish_date']}
                Pages: {row['pages']}
                Average Rating: {row['average_rating']}
                Description:{row['description']}
                Thumbnail: {row['thumbnail']}"""
            else:
                row = books_df.sample(1).iloc[0]
                response_text = f"Sorry, I couldn’t find a book titled '{title}'. How about '{row['title']}' by {row['author']}?"
        else:
            row = books_df.sample(1).iloc[0]
            response_text = f"I recommend '{row['title']}' by {row['author']} (Genre: {row['genre']})."

    # ----------------------
    # Intent: search_author
    # ----------------------
    elif intent == "search_author":
        author = str(params.get("author", "")).lower()
        if author:
            match = books_df[books_df["author"].str.lower().str.contains(author, na=False)]
            if not match.empty:
                titles = ", ".join(match["title"].tolist()[:5])
                response_text = f"Books by {author.title()}: {titles}"
            else:
                response_text = f"Sorry, I couldn’t find books from {author}."
        else:
            response_text = "Please provide an author name."

    # ----------------------
    # Intent: book_page
    # ----------------------
    elif intent == "book_page":
        title = str(params.get("book_title", "")).lower()
        match = books_df[books_df["title"].str.lower().str.contains(title, na=False)]
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
        match = books_df[books_df["genre"].str.lower().str.contains(genre, na=False)]
        if not match.empty:
            titles = ", ".join(match["title"].tolist()[:5])
            response_text = f"Here are some {genre.title()} books: {titles}"
        else:
            response_text = f"Sorry, I couldn’t find books in the {genre} genre."

    # ----------------------
    # Intent: get_book_genre
    # ----------------------
    elif intent == "get_book_genre":
        title = str(params.get("book_title", "")).lower()
        match = books_df[books_df["title"].str.lower().str.contains(title, na=False)]
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
        match = books_df[books_df["title"].str.lower().str.contains(title, na=False)]
        if not match.empty:
            row = match.iloc[0]
            response_text = f"'{row['title']}' description: {row['description']}"
        else:
            response_text = f"Sorry, I couldn’t find a description for '{title}'."

    # ----------------------
    # Intent: publish_date
    # ----------------------
    elif intent == "publish_date":
        title = str(params.get("book_title", "")).lower()
        match = books_df[books_df["title"].str.lower().str.contains(title, na=False)]
        if not match.empty:
            row = match.iloc[0]
            response_text = f"'{row['title']}' was published on {row['publish_date']}."
        else:
            response_text = f"Sorry, I couldn’t find the publish date for '{title}'."

    # ----------------------
    # Intent: publisher
    # ----------------------
    elif intent == "publisher":
        title = str(params.get("book_title", "")).lower()
        match = books_df[books_df["title"].str.lower().str.contains(title, na=False)]
        if not match.empty:
            row = match.iloc[0]
            response_text = f"The publisher of '{row['title']}' is {row['publisher']}."
        else:
            response_text = f"Sorry, I couldn’t find the publisher for '{title}'."

    # ----------------------
    # Intent: averate_rating
    # ----------------------
    elif intent == "averate_rating":
        title = str(params.get("book_title", "")).lower()
        match = books_df[books_df["title"].str.lower().str.contains(title, na=False)]
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
        match = books_df[books_df["title"].str.lower().str.contains(title, na=False)]
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

    #Translate back to user’s language
    response_text = translate_back(response_text, detected_lang)

    print(f"[DEBUG] Final response (before sending): {response_text}\n")

    return jsonify({"fulfillmentText": response_text})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


