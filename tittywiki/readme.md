# setup

## quick start

1. put `index.html` in a folder with some `.md` files
2. create `index.json` listing your page names, e.g. `["home", "about", "notes"]`
3. deploy (or open `index.html` locally with a local server)

done. that's it.

## file structure

```
your-wiki/
  index.html      ← the wiki engine (this file)
  index.json      ← list of page names
  home.md         ← your first page
  about.md        ← another page
  ...
```

## writing pages

pages are standard markdown. use `[[page name]]` to link to other pages. the slug is generated automatically from the name (lowercase, hyphens).

```
# my page

this links to [[another page]] and [[yet another]].

## code blocks

```python
print("hello")
\```
```

## local development

open with any local server:
```
python3 -m http.server
```

then visit `http://localhost:8000`. you can't use `file://` directly because the browser blocks cross-origin fetches.

## deploying to github pages

1. create a repo
2. push your files (including `index.html` and `index.json`)
3. enable github pages from the main branch

done. your wiki is live at `yourname.github.io/repo-name`.

## deploying to neocities

drag and drop. literally. neocities supports static sites with no build step.

## advanced

- **custom themes**: edit the `<style>` block in `index.html`
- **adding pages**: edit `index.json`, add the `.md` file, push
- **page list generation**: you can script the `index.json` generation from a directory listing

## limitations

- no real-time collaboration — it's a static site
- no version history in the ui (use git for that)
- markdown rendering is minimal — headings, links, lists, code, blockquotes
- no image support yet
