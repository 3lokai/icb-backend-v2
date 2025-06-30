import os


def list_tree(
    base=".",
    ignore=(
        "__pycache__",
        ".pytest_cache",
        ".git",
        ".venv",
        ".mypy_cache",
        ".ruff_cache",
        "cache",
        "data",
        "docs",
        "venv",
        "tests",
    ),
):
    with open("structure_clean.txt", "w") as f:
        for root, dirs, files in os.walk(base):
            if any(ig in root for ig in ignore):
                continue
            level = root.replace(base, "").count(os.sep)
            indent = " " * 4 * level
            f.write(f"{indent}{os.path.basename(root)}/\n")
            for file in files:
                f.write(f"{indent}    {file}\n")


list_tree()
