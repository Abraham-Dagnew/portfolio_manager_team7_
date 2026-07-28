from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
@app.route("/portfolio")
def portfolio():
    return render_template("portfolio.html")

@app.route("/performance")
def performance():
    return render_template("performance.html")

@app.route("/add")
def add_holding():
    return render_template("add_holding.html")

if __name__ == "__main__":
    app.run(port=5000, debug=True)