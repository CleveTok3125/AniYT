try:
    from importlib.metadata import PackageNotFoundError, version

    __version__ = version("AniYT")
except PackageNotFoundError:
    __version__ = "0.0.0"
