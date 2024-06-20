from os import environ

__version__ = (
    "1.0.0" if "VERSION" not in environ
    else environ["VERSION"]
)
