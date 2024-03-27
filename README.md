# Jinjabread

[![CircleCI](https://img.shields.io/circleci/build/gh/jdeanwallace/jinjabread)](https://circleci.com/gh/jdeanwallace/jinjabread)
[![GitHub release](https://img.shields.io/github/v/release/jdeanwallace/jinjabread)](https://github.com/jdeanwallace/jinjabread/releases)
[![PyPI downloads](https://img.shields.io/pypi/dm/jinjabread)](https://pypi.org/project/jinjabread/)
[![License](https://img.shields.io/:license-mit-blue.svg)](LICENSE)

A Python-based static site generator using Jinja templates.

Inspired by [`staticjinja`](https://github.com/staticjinja/staticjinja), [`jekyll`](https://github.com/jekyll/jekyll), and [`hugo`](https://github.com/gohugoio/hugo).

## Install

```bash
pip install jinjabread
```

## Usage

### Create new site project

```bash
python -m jinjabread new mysite
```

### Build site

```bash
python -m jinjabread build mysite
```

### Preview site locally

```bash
python -m jinjabread serve mysite
# Visit http://127.0.0.1:8000 in your browser.
```

## Features

- Write pages in Markdown, HTML, or text.
- Use Jinja2 templating language in Markdown, HTML, or text.
- Supports YAML metadata in Markdown pages.
- Keep static media alongside static pages.
- Index pages (i.e., `index.html`) can list all other pages in the same directory.
- Preview your static site locally with a built-in web server.
- Prettify all generated HTML (because why not?)

## File structure

### Important files and directories

| Name              | Description                                                     | Example path |
| ---               | ---                                                             | --- |
| Project directory | The project root                                                | `mysite` |
| Content directory | Contains site content where each file becomes a site page       | `mysite/content` |
| Layouts directory | Contains page layouts that gets used by the site content        | `mysite/layouts` |
| Static directory  | Contains static media that gets copied to the output directory  | `mysite/static` |
| Output directory  | The complete generated site, ready to be hosted                 | `mysite/public` |
| Config file       | Custom site configurations in TOML format                       | `mysite/jinjabread.toml` |

### Example: Site project structure

```
mysite/
├── content
│   ├── about.html
│   ├── index.html
│   └── posts
│       ├── index.html
│       ├── my-journey
│       │   ├── index.html
│       │   └── profile-photo.jpg
│       └── my-story.html
├── jinjabread.toml
├── layouts
│   └── markdown.html
├── public
│   ├── about.html
│   ├── index.html
│   ├── posts
│   │   ├── index.html
│   │   ├── my-journey
│   │   │   ├── index.html
│   │   │   └── profile-photo.jpg
│   │   └── my-story.html
│   └── static
│       └── style.css
└── static
    └── style.css
```

### Example: File to URL translation

| File path                                     | URL path |
| ---                                           |----------|
| `public/index.html`                           | `/` |
| `public/about.html`                           | `/about` |
| `public/posts/index.html`                     | `/posts/` |
| `public/posts/my-story.html`                  | `/posts/my-story` |
| `public/posts/my-journey/index.html`          | `/posts/my-journey/` |
| `public/posts/my-journey/profile-photo.jpg`   | `/posts/my-journey/profile-photo.jpg` |
| `public/static/style.css`                     | `/static/style.css` |


## Site config

### Default config

```toml
content_dir = "content"
layouts_dir = "layouts"
static_dir = "static"
output_dir = "public"
prettify_html = true

[context]

[[pages]]
  type = "jinjabread.MarkdownPage"
  glob_pattern = "**/*.md"
  layout_name = "markdown.html"

[[pages]]
  type = "jinjabread.Page"
  glob_pattern = "**/*"
```

### Custom config

#### Change output directory

```toml
# jinjabread.toml
output_dir = "dist"
```

#### Add global Jinja context variables

```toml
# jinjabread.toml
[context]
  site_name = "My site"
  url_origin = "https://mysite.com"
```

#### Change Markdown layout file

```toml
# jinjabread.toml
[[pages]]
  type = "jinjabread.MarkdownPage"
  glob_pattern = "**/*.md"
  layout_name = "post.html"

[[pages]]
  type = "jinjabread.Page"
  glob_pattern = "**/*"
```

#### Add page-specific Jinja context variables

```toml
# jinjabread.toml
[[pages]]
  type = "jinjabread.MarkdownPage"
  glob_pattern = "**/*.md"
  layout_name = "markdown.html"

[[pages]]
  type = "jinjabread.Page"
  glob_pattern = "**/*.txt"

  [pages.context]
    foo = "bar"

[[pages]]
  type = "jinjabread.Page"
  glob_pattern = "**/*"
```

## Pages types

| Page type | Keyword arguments |
| --- | --- |
| [`jinjabread.Page`](jinjabread/base.py#L71) | - `glob_pattern` |
| [`jinjabread.MarkdownPage`](jinjabread/base.py#L136) | - `glob_pattern` <br> - `layout_name` |

### Markdown pages

Markdown content supports [full YAML metadata](https://github.com/sivakov512/python-markdown-full-yaml-metadata).

For example, given the following content and layout:

```yaml
---
# content/my-blog-post.md
title: My blog post
author: John Smith
description: A very nice story.
keywords:
  - thrilling
  - must-read
---
It was a cold stormy night...
```

```html
<!-- layouts/markdown.html -->
<h1>{{ title }}</h1>
<h2>{{ description }}</h2>
<h3>Written by {{ author }}</h3>
<p>{{ content }}</p>
```

Results in the following output:

```html
<!-- public/my-blog-post.html -->
<h1>
  My blog post
</h1>
<h2>
  A very nice story.
</h2>
<h3>
  Written by John Smith
</h3>
<p>
  <p>
    It was a cold stormy night...
  </p>
</p>
```

## Context variables

### Default variables

All pages have these context variables:

| Name | Description | Example value |
| --- | --- | --- |
| `url_path` | The URL path of the current page | `/` |
| `file_path` | The file path of the current page, relative to the output directory | `index.html` |

### Variable precedence

Page-specific context variables override global site context variables.

For example:
```toml
# jinjabread.toml
[context]
  fee = "fie"
  foe = "fum"

[[pages]]
  type = "jinjabread.Page"
  glob_pattern = "**/*.txt"

  [pages.context]
    foe = "foo"

[[pages]]
  type = "jinjabread.Page"
  glob_pattern = "**/*.html"

  [pages.context]
    foe = "bar"
```

* `.txt` pages will have the following extra context variables:
  ```toml
  fee = "fie"
  foe = "foo"
  ```
* `.html` pages have the following extra context variables:
  ```toml
  fee = "fie"
  foe = "bar"
  ```

### Index pages

All index pages (i.e., `index.*`) has an extra context variable named `pages` which is list of dictionaries of context variables from its sibling files.

For example, given the following file structure:
```
mysite/content/posts/
├── index.html
├── post1.md
└── post2.md
```

You can list all the pages in the `posts` directory using:

```html
<!-- mysite/content/posts/index.html -->
{% for page in pages %}
<a href="{{ page.url_path }}">
  {{ page.url_path.split('/') | last | title }}
</a>
{% endfor %}
```

Resulting in:

```html
<!-- mysite/public/posts/index.html -->
<a href="/posts/post1">
  Post1
</a>
<a href="/posts/post2">
  Post2
</a>
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
