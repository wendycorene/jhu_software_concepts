from flask import Flask
from homePage import pages


def create_app():
    app = Flask(
        __name__,
        template_folder="homePage/templates",
        static_folder="homePage/static",
    )

    app.register_blueprint(pages.bp)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)