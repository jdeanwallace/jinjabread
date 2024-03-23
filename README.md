# Jinjabread

[![CircleCI](https://img.shields.io/circleci/build/gh/jdeanwallace/jinjabread)](https://circleci.com/gh/jdeanwallace/jinjabread)
[![GitHub release](https://img.shields.io/github/v/release/jdeanwallace/jinjabread)](https://github.com/jdeanwallace/jinjabread/releases)
[![PyPI downloads](https://img.shields.io/pypi/dm/jinjabread)](https://pypi.org/project/jinjabread/)
[![License](https://img.shields.io/:license-mit-blue.svg)](LICENSE)

**WORK IN PROGRESS**

A Python-based static site generator using Jinja templates.

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
python -m build
```

### Release

```bash
export TWINE_USERNAME='__token__'
export TWINE_PASSWORD='secret-token'
python -m twine upload dist/*
```
