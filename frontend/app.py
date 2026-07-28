"""
Flask frontend server for the Portfolio Manager application.

Serves HTML pages that call the FastAPI backend (running separately on
port 8000) via client-side JavaScript.
"""

from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def portfolio():
    """
    Browse portfolio page. (Person A)
    """

    return render_template("portfolio.html")


@app.route("/performance")
def performance():
    """
    Portfolio performance page with summary totals and a chart. (Person B)
    """

    return render_template("performance.html")


@app.route("/add")
def add_holding():
    """
    Add holding form page. (Person C)
    """

    return render_template("add_holding.html")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
