# Contributing

Keep changes small and state what each measurement covers:

1. Do not replace validated FBZ or result files without recording their complete SHA-256.
2. Do not describe API power as total platform consumption or host-observed latency as pure
   on-chip latency.
3. Do not add application-specific decoding to the command-line tool.
4. Add tests for changes to input loading, artifact checks or runtime behavior.
5. Run `python -m unittest discover -s tests -v` and `python -m ruff check .` before opening a pull request.
6. Hardware results must include host, OS, Python/SDK version, device version, model hash,
   CPU governor, ClockMode, MapMode, warm-up, repetitions and measurement boundary.

Do not post proprietary SDK code, private datasets, credentials or local user paths in issues.
