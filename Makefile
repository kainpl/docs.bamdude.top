.PHONY: install serve build clean

install:
	pip install -r requirements.txt

# Live-reload dev server on http://127.0.0.1:8000/
serve:
	mkdocs serve

# Static build into ./site/. Use `--strict` to catch broken cross-links.
build:
	mkdocs build --strict

clean:
	rm -rf site/
