import subprocess

import griffe


def test_diff_griffe():
    latest_tag = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"]).decode("utf8").strip()
    griffe_stable = griffe.load_git("griffe", latest_tag, search_paths=["src"])
    griffe_latest = griffe.load("griffe")
    breaking = list(griffe.find_breaking_changes(griffe_stable, griffe_latest))
    for breakage in breaking:
        print(breakage.explain())
    assert not breaking
