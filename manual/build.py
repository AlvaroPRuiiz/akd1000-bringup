"""Build the manual with XeLaTeX and BibTeX on Windows or Linux."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def main() -> None:
    source = Path(__file__).resolve().parent
    output = source / "AKD1000_Bringup_Guide.pdf"
    for executable in ("xelatex", "bibtex"):
        if shutil.which(executable) is None:
            raise SystemExit(f"Required executable not found: {executable}")

    # Compile a clean copy so a failed IDE run (for example, pdfLaTeX leaving
    # a partial main.aux) cannot block XeLaTeX or alter the editable sources.
    with tempfile.TemporaryDirectory(prefix="akd1000-manual-") as temporary:
        work_root = Path(temporary)
        build_dir = work_root / "manual"
        ignored = shutil.ignore_patterns(
            "*.aux", "*.fdb_latexmk", "*.fls", "*.log", "*.out", "*.toc",
            "*.lof", "*.lot", "*.bbl", "*.blg", "*.pdf", "*.xdv", "*.synctex.gz",
        )
        shutil.copytree(source, build_dir, ignore=ignored)
        assets = source.parent / "docs" / "assets"
        if assets.is_dir():
            shutil.copytree(assets, work_root / "docs" / "assets")

        command = [
            "xelatex", "-no-shell-escape", "-interaction=nonstopmode",
            "-halt-on-error", "-file-line-error", "main.tex",
        ]
        subprocess.run(command, cwd=build_dir, check=True)
        environment = os.environ.copy()
        environment["BIBINPUTS"] = str(build_dir) + os.pathsep + environment.get("BIBINPUTS", "")
        subprocess.run(["bibtex", "main"], cwd=build_dir, env=environment, check=True)

        for _ in range(5):
            subprocess.run(command, cwd=build_dir, check=True)
            log = (build_dir / "main.log").read_text(encoding="utf-8", errors="replace")
            if not any(message in log for message in (
                "Rerun to get", "Rerun LaTeX", "Please (re)run", "undefined references"
            )):
                break
        else:
            raise SystemExit("Cross-references did not converge; inspect the LaTeX source.")

        if not (build_dir / "main.pdf").is_file():
            raise SystemExit("XeLaTeX completed without producing main.pdf.")
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(build_dir / "main.pdf", output)

    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
