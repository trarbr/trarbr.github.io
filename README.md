# README

This is my personal tech blog. It is generated with
[Pelican](https://getpelican.com/) and hosted on GitHub pages.

## Setup

Run the following commands to setup a Python environment with all the required
dependencies:

```sh
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

## Running it locally

Run the following command to serve the site locally with incremental and
automatic rebuilds:

```sh
pelican -lr
```

## Publihsing

The content of the `gh-pages` branch is what is used on the actual website.
Run the following commands to publish a new version of the website:

```sh
pelican --settings publishconf.py
ghp-import output -b gh-pages -m "Build site"
git push origin gh-pages
```
