# Using Your Own Page Template with MD2BSP

*Draft. Written for campuses that want to use MD2BSP with their own Brightspace page template.*

MD2BSP builds the content of a page for you: headings, links, accordions, videos, callouts. Then it drops that content into a wrapper file, your **page template**. The wrapper is where your campus look lives: your banner, your footer, your colors, your help links.

This page tells you what the template needs so MD2BSP can fill it. It's short. There are only three slots.

## The three slots

Put these in your template file exactly as written, with double curly braces and no spaces.

| Slot | Where it goes | What MD2BSP puts there |
|---|---|---|
| `{{TITLE}}` | Inside `<title>` in the head | The text of the page's first H1. If the page has no H1, it falls back to "Untitled Page". The text is HTML-escaped for you. |
| `{{BANNER_SRC}}` | The `src` of the banner `<img>` | The banner's full path: your banner folder plus the picked file name. |
| `{{CONTENT}}` | Inside the column where page content belongs | The converted body of the page. |

In the GCC template, they sit like this:

```html
<title>{{TITLE}}</title>
...
<p><img src="{{BANNER_SRC}}" alt="" title="" data-d2l-editor-default-img-style="true" style="max-width: 100%;"></p>
...
<div class="col-sm-10 offset-sm-1">
    {{CONTENT}}
</div>
```

## Rules of the road

- **Spell the slots exactly.** MD2BSP swaps the text with a plain find-and-replace. A typo like `{{ CONTENT }}` or `{{Content}}` is not found, and nothing warns you. The page just comes out without your content.
- **Use each slot at least once.** Every copy of a slot gets replaced, so `{{TITLE}}` can appear in more than one place if you need it to.
- **Keep the slots in plain markup.** Don't put one inside a script or a comment.
- **The first H1 becomes your page title.** MD2BSP also puts the "time on task" list right after the first `</h1>`, so that list lands directly under your page title. That list is added to the content before it goes into your template. It isn't a slot, and you don't need to add anything for it.
- **Banner alt text is empty on purpose.** The banner is decoration, so GCC's template uses `alt=""`.

## What is GCC-specific (change these for your campus)

These live in the template file itself, so you can change them without touching the code:

- **The head.** Paths to Bootstrap, Font Awesome, and your campus CSS. The GCC template points at Brightspace's shared template folder.
- **Your colors.** GCC's `<style>` block sets headings, icons, and callout cards to its own blue and gold. Swap in your own.
- **The footer.** GCC's has three help links (Academic Help, Accessibility Help, IT Help) and a logo. Replace them with yours. Keep the link text meaningful and keep the "(opens in a new tab)" hidden text on links that open a new tab.
- **The scripts at the bottom.** Keep the template's scripts, and keep the `<p>` that wraps them.

## What lives in the code (change these in `md2bsp_web.py`)

- `TEMPLATE_FILE`: the name of your template file. The app looks for it next to the program.
- `BANNER_FOLDER`: the folder path written into the downloaded page (your Brightspace banner folder).
- `BANNER_PREVIEW_FOLDER`: the full web address used to show banners in the app's preview. The preview runs outside Brightspace, so it needs a real URL.
- `DEFAULT_BANNER_FILE`: the banner used when none is picked.
- `BANNER_CHOICES`: the banner menu. It's a list of groups, each with (file name, description) pairs.

## The preview is a simulation

Your template's styles only exist inside Brightspace, so the app's Preview step imitates the look. It doesn't load your template. The Download step does use your template. Check a downloaded page in a real course before you hand it to anyone.

## Quick test

1. Download a page from a short sample.
2. Open the file in a text editor and search for `{{`. Nothing should be left. If you find one, a slot is misspelled.
3. Check that the title, banner, and content all showed up.
4. Upload it to a Brightspace test course and look at it there.

## Need help?

Open an issue in this repository, or tell us what your campus changed. We'd like to see how other campuses make it theirs.
