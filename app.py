# python3 app.py

import json
from flask import Flask, render_template

app = Flask(__name__)
with open("static/apartments.json") as f:
    apartments = json.load(f)
# apartments = {a["id"]: a for a in apartments}

@app.route("/")
def map():
    return render_template("map.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/review")
def review():
    return render_template("review.html")

# @app.route("/apartment/<id>")
# def apartment(id):
#     return render_template("apartment.html", detail=apartments[int(id)])

if __name__ == "__main__":

    # development, https://getoffgrounds.com:5000
    # app.run(debug=True, host="0.0.0.0", port=5000, ssl_context=("/etc/letsencrypt/live/getoffgrounds.com/fullchain.pem", "/etc/letsencrypt/live/getoffgrounds.com/privkey.pem"))

    # production, use nginx to handle SSL and redirect HTTP to HTTPS
    from waitress import serve
    serve(app, port=5000)
