from os import environ


__version__ = (
    environ["VERSION"] if "VERSION" in environ
    else "1.0.0.PRE"
)
