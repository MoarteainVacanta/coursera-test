# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository overview

This is a GitHub Pages site with default, unmodified scaffolding. It contains no
custom content, application code, build scripts, or tests — just:

- `README.md` — the default GitHub Pages README (unedited boilerplate).
- `_config.yml` — Jekyll configuration; sets `theme: jekyll-theme-cayman`.

There is no `Gemfile`, no `_layouts`/`_includes`/`_posts` directories, and no CI
configuration. GitHub Pages builds this site automatically with Jekyll on every
push to the default branch — there is no local build, lint, or test command to
run.

## Working in this repository

Since the repo is currently just theme scaffolding, most tasks will involve
adding actual site content (Markdown pages, `_config.yml` settings, layouts,
posts, etc.) rather than modifying existing structure. When adding Jekyll
content, follow standard Jekyll conventions (e.g. `_posts/YYYY-MM-DD-title.md`
for posts, front matter blocks at the top of Markdown files) since none of
that structure exists yet in this repo to infer conventions from.
