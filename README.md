# jinjabread

**WORK IN PROGRESS**

An Python-based static site generator using Jinja templates.

Inspired by [`staticjinja`](https://github.com/staticjinja/staticjinja) and [`hugo`](https://github.com/gohugoio/hugo).

## Build

```bash
python -m venv venv && \
  . venv/bin/activate && \
  pip install pip pip-tools --upgrade && \
  pip-sync requirements.txt
```

## Test

```bash
python -m unittest jinjabread.tests
```
