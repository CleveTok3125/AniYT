import os
import shutil
import subprocess
from setuptools import Extension, setup

print("Building Go binary...")
go_executable = shutil.which("go")
if go_executable:
    repo_root = os.path.dirname(os.path.abspath(__file__))
    go_source_dir = os.path.join(repo_root, "src", "ani_tracker")
    output_dir = os.path.join(repo_root, "bin")
    output_path = os.path.join(output_dir, "ani-tracker")

    try:
        os.makedirs(output_dir, exist_ok=True)
        # Execute the Go build command
        subprocess.check_call(
            [go_executable, "build", "-ldflags=-s -w", "-o", output_path, "."],
            cwd=go_source_dir,
        )
        print(f"Go binary successfully built at: {output_path}")
    except Exception as e:
        print(f"ERROR: Go build failed: {e}")
else:
    print("WARNING: 'go' command not found. Skipping Go binary build.")

print("Configuring extensions...")
try:
    from Cython.Build import cythonize
    USE_CYTHON = True
    ext_suffix = ".pyx"
    print("Cython detected. Using .pyx sources.")
except ImportError:
    USE_CYTHON = False
    ext_suffix = ".c"
    print("Cython not found. Using pre-compiled .c sources.")

query_ext_source = os.path.join("src", "ani_yt", "_internal", "_query" + ext_suffix)

extensions = [
    Extension(
        name="ani_yt._internal._query",
        sources=[query_ext_source],
    )
]

if USE_CYTHON:
    extensions = cythonize(extensions)

print("Running setup()...")
setup(
    ext_modules=extensions,
)
