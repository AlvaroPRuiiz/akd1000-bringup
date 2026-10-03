"""Build the Spanish and English manuals with XeLaTeX and BibTeX."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def build_language(manual: Path, language: str) -> None:
    output = manual / f"AKD1000_Bringup_Guide_{language}.pdf"
    # A clean temporary copy keeps stale auxiliary files out of both builds.
    with tempfile.TemporaryDirectory(prefix="akd1000-manual-") as temporary:
        work_root = Path(temporary)
        build_root = work_root / "manual"
        ignored = shutil.ignore_patterns(
            "*.aux", "*.fdb_latexmk", "*.fls", "*.log", "*.out", "*.toc",
            "*.lof", "*.lot", "*.bbl", "*.blg", "*.pdf", "*.xdv", "*.synctex.gz",
            "*.bcf", "*.run.xml", "__pycache__",
        )
        shutil.copytree(manual, build_root, ignore=ignored)
        shutil.copytree(manual.parent / "docs" / "assets", work_root / "docs" / "assets")
        build_dir = build_root if language == "ES" else build_root / "en"
        command = [
            "xelatex", "-no-shell-escape", "-interaction=nonstopmode",
            "-halt-on-error", "-file-line-error", "main.tex",
        ]
        subprocess.run(command, cwd=build_dir, check=True)
        environment = os.environ.copy()
        environment["BIBINPUTS"] = os.pathsep.join(
            (str(build_dir), str(build_root), environment.get("BIBINPUTS", ""))
        )
        subprocess.run(["bibtex", "main"], cwd=build_dir, env=environment, check=True)

        for _ in range(5):
            subprocess.run(command, cwd=build_dir, check=True)
            log = (build_dir / "main.log").read_text(encoding="utf-8", errors="replace")
            if not any(message in log for message in (
                "Rerun to get", "Rerun LaTeX", "Please (re)run", "undefined references"
            )):
                break
        else:
            raise SystemExit(f"{language}: cross-references did not converge.")

        if any(message in log for message in (
            "undefined", "multiply defined", "Missing character", "LaTeX Error"
        )):
            raise SystemExit(f"{language}: unresolved references, citations, labels or glyphs.")
        if not (build_dir / "main.pdf").is_file():
            raise SystemExit(f"{language}: XeLaTeX did not produce main.pdf.")
        shutil.copyfile(build_dir / "main.pdf", output)
    print(f"Saved: {output}")


def main() -> None:
    manual = Path(__file__).resolve().parent
    for executable in ("xelatex", "bibtex"):
        if shutil.which(executable) is None:
            raise SystemExit(f"Required executable not found: {executable}")
    for language in ("ES", "EN"):
        build_language(manual, language)


if __name__ == "__main__":
    main()
