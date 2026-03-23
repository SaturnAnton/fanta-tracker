from flask import Flask, render_template, url_for
from endpoints import api_bp


app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static",
)

app.register_blueprint(api_bp)


@app.get("/")
def home():
    """Render the home page with search functionality."""
    return render_template("index.html")


@app.get("/player/<player_name>")
def player_details(player_name: str):
    """Render the player details page."""
    return render_template("player.html", player_name=player_name)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    