MD2BSP - Markdown to Brightspace
Loy Gross

PURPOSE
MD2BSP turns plain markdown text into a Brightspace web page that follows
the standard GCC template. Faculty paste their content into a web page, the
tool splits it into boxes (one per heading, paragraph, or list), shows each
box the way it will look on the finished page, and lets the instructor fix
labels, fix typos, and fix links that don't say where they go. The goal is
consistent, standardized pages instead of one-off copy-and-pasted Word
conversions. Students get pages built the same way every time, and
instructors get a quick path to making them.

HOW TO RUN IT
Live version (nothing to install):
    https://effierover.github.io/md2bsp/
    1. Paste markdown into the box and click "Chunk it."
    2. Check the boxes, the preview, and the "Things to fix" list.

Engine only, from the command line:
    1. Put template.html and input.md in the same folder as md2bsp_web.py.
       (template.html is not in the public repo because it contains GCC
       branding.)
    2. Run: python md2bsp_web.py
    3. Open output.html.
    Python version tested: [fill in, e.g. 3.12]

SAMPLE RUN
Pasted into the web page:

    # Welcome

    Visit https://www.genesee.edu/blah/page.html for info.

    - First item
    - Second item with https://example.com/a

After "Chunk it" the tool shows three boxes: Heading 1, Paragraph, and
Bulleted list. Each bare web address became a link whose text is the site
name (genesee.edu and example.com). The "Things to fix" list says:

    Box 2: link (https://www.genesee.edu/blah/page.html) is missing
    descriptive text.
    Box 3: link (https://example.com/a) is missing descriptive text.

Clicking the pencil on box 2, changing "genesee.edu" to real words, and
clicking the check mark removes that line from the list. When both links are
fixed, the list says "Nothing to fix."
[Replace with output from your own run.]

FILES
    index.html       the web page (paste screen, organize screen)
    style.css        how the page looks; uses Lato
    main.py          the web page's behavior (buttons, boxes, preview)
    md2bsp_web.py    the engine: cleaning, chunking, boxes, HTML, issues
    pyscript.toml    tells PyScript where to find md2bsp_web.py
    fonts/           Lato web fonts and its license (SIL Open Font License)
    LICENSE          MIT license, with a note excluding GCC template
                     and branding
    README           this file
    Not in the repo: template.html and input.md (GCC branding / test input)

KNOWN ISSUES
    1. HTML preview and the download link are not built yet. Today the tool
       gets as far as the Organize screen.
    2. Callouts, accordions, tabs, and the top-of-page and bottom-of-page
       items (before you start, materials, week/unit/module) are not built.
    3. Clicking Back and chunking again rebuilds the boxes from the
       original pasted text, so relabels and edits made on the Organize
       screen are lost.
    4. Numbered lists must start with "1. " and bulleted lists with "- " or
       "* ". Nested lists are not supported (indentation is flattened).
    5. Links inside headings are not turned into links or checked.
    6. Only http:// and https:// links are recognized, and a web address
       that ends with ")" can be cut short.
    7. A heading glued to its paragraph with no blank line stays one
       heading box.
    8. Underscores for italics are not supported (asterisks only).
    9. "Things to fix" checks one thing so far: link text that is empty or
       only the site name or web address.
    10. Heading sizes H4 to H6 in the preview are my estimates. The preview
        is a close simulation, not a copy of Brightspace.
    11. Not yet checked inside a live Brightspace course.
    12. The web page needs an internet connection (PyScript and Font Awesome
        load from the web).

CHANGES FROM PLAN
    - Now: the same engine
      also runs in the browser through PyScript on GitHub Pages, so
      instructors need no setup.
    - Words: "block" became "chunk" (a raw piece of text) and "box" (a
      chunk after it has been labeled), because block and box were
      confusing.
    - Added: the Organize screen with type dropdowns, a live preview, an
      Edit/Done button on each box, and the "Things to fix" list.
    - Changed: a bare link used to become [missing text](url). It now
      becomes the site name, and the tool flags it until a human writes
      better words.
    - Not yet done from the plan: callouts, page header items, HTML
      preview, and download.

LIBRARIES AND OTHER MATERIALS
    - Python standard library: html, math, os, sys, urllib.parse
    - PyScript (Pyodide), release 2025.10.3, runs the Python in the browser
    - Font Awesome 5.9.0 (free), loaded from cdnjs, for the link
