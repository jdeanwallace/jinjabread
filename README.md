# jinjabread

**WORK IN PROGRESS**

An Python-based static site generator using Jinja templates.

Inspired by [`staticjinja`](https://github.com/staticjinja/staticjinja) and [`hugo`](https://github.com/gohugoio/hugo).

## Install

```bash
pip install jinjabread
```

## Usage

### Create new site project

```bash
python -m jinjabread new mysite
```

### Build site project

```bash
python -m jinjabread build mysite
```

### Run development server

```bash
python -m jinjabread serve mysite
```

## Contributing

### Setup

```bash
python -m venv venv && \
  . venv/bin/activate && \
  pip install pip pip-tools --upgrade && \
  pip-sync requirements.txt
```

### Test

```bash
python -m unittest discover .
```

### Build

```bash
rm -r build dist
python -m build
```

### Release

```bash
python -m twine upload dist/*
```
