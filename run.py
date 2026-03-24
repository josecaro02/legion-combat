#!/usr/bin/env python3
"""Entry point for the Flask application."""

import os
import sys

# Add the project directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.config import get_config


# Create application with appropriate configuration
config = get_config()
app = create_app(config)


if __name__ == '__main__':
    app.run(
        host=os.environ.get('FLASK_HOST', '0.0.0.0'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
        debug=config.DEBUG if hasattr(config, 'DEBUG') else False
    )
