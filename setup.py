from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        name="ani_yt._query",
        sources=["src/ani_yt/_query.pyx"],
    )
]

setup(
    name="AniYT",
    ext_modules=cythonize(extensions, language_level=3),
    package_dir={"": "src"},
)
