# tittywiki

a single html file that turns a folder of markdown notes into a wiki.

## what it is

tittywiki is a zero-dependency, single-file wiki engine. drop `index.html` into any folder of `.md` files, deploy, and you have a navigable wiki with [[crosslinks]], backlinks, and search.

no build step. no server. no framework. just markdown and a browser.

## how it works

1. add `.md` files to a folder
2. create an `index.json` listing your page names (or use `pages.json`)
3. drop in `index.html`
4. deploy anywhere — github pages, neocities, a usb stick

the wiki reads your markdown, renders it to html, and automatically resolves [[wikilinks]] to other pages. backlinks appear at the bottom of every page. search across all pages happens in the browser.

## features

- **[[wikilinks]]** — link to any page by name. missing pages show as dashed links
- **backlinks** — every page shows what links to it
- **search** — type in the sidebar to filter pages
- **dark theme** — easy on the eyes, works on mobile
- **no dependencies** — one file, vanilla javascript
- **github pages ready** — deploy in 30 seconds

## why the name

it started as a joke. it stayed because it's memorable.

## getting started

see the [[readme]] for setup instructions.
