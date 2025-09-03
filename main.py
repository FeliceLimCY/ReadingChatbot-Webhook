from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

# Load your dataset (Books.xlsx must be uploaded to Render along with this file)
books_df = pd.read_excel("Books.xlsx")

#Health check endpoint for browser and verification
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    return "Webhook endpoint is live! Please use POST requests for Dialogflow.", 200

#Main webhook endpoint that now MATCHES Dialogflow settings
@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json(force=True)
    intent = req.get("queryResult", {}).get("intent", {}).get("displayName", "")
    params = req.get("queryResult", {}).get("parameters", {})

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
            #Search for specific books
            match = books_df[books_df["title"].str.lower().str.contains(title, na=False)]
            if not match.empty:
                row = match.iloc[0]
                response_text = f"I found '{row['title']}' by {row['author']} (Genre: {row['genre']})."
            else:
                #If book not found, recommend random book
                row = books_df.sample(1).iloc[0]
                response_text = f"Sorry, I couldn’t find a book titled '{title}'. How about '{row['title']}' by {row['author']}?"
        else:
            #No title provided = recommend random book
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
    # Intent: feedback
    # ----------------------
    elif intent == "feedback":
        response_text = "Thanks for your feedback! Your opinion helps me recommend better books."

    # ----------------------
    # Intent: bot_challenge
    # ----------------------
    elif intent == "bot_challenge":
        response_text = "I’m a book assistant bot 🤖, here to help you discover books!"

    return jsonify({"fulfillmentText": response_text})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
