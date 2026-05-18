from app import create_app
from app.config import Config
import os

Config.validate()
app = create_app()

if __name__ == "__main__":
    app.run()
