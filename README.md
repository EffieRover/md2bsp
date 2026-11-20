MD2BSP - Markdown to Brightspace
Loy Gross


PURPOSE

MD2BSP turns plain markdown text into a Brightspace web page that follows the
standard GCC template. Faculty paste their content into a web page. The tool
splits it into boxes (one per heading, paragraph, or list), shows each box the
way it will look on the finished page, and lets the instructor fix labels, fix
typos, fix links that don't say where they go, and add callouts. A last screen
collects the extras that belong at the top and bottom of every page. Then the
instructor downloads a finished page, ready to upload to Brightspace.

The goal is consistent, standardized pages instead of one-off copy-and-pasted
Word conversions. Students get pages built the same way every time, and
instructors get a quick path to making them.


HOW TO RUN IT

Live version (nothing to install): https://effierover.github.io/md2bsp/

1. Paste: paste markdown into the box and click "Chunk it."
2. Organize: check the boxes and the preview. Use the dropdowns to relabel a
   box or add a callout, and the pencil to fix text. Clear the "Needed Repairs"
   list. Click "Next: Finishing Touches."
3. Finishing Touches: fill in only what applies (reading, video, and activity
   minutes; before you start; materials needed; key terms; guiding questions;
   working toward; Week, Unit, or Module and its number). Click "Next: Preview."
4. Preview: look over the simulated page. Click "Download," then upload the
   file to Brightspace.

Engine only, from the command line:
1. Put template_gcc.html and input.md in the same folder as md2bsp_web.py.
   (template_gcc.html is in the public repo and carries GCC branding; see the
   LICENSE file. input.md is not in the repo.)
2. Run: python md2bsp_web.py
3. Open output.html.
Python version tested: [fill in, e.g. 3.12]


SAMPLE RUN

Pasted into the web page:

# Welcome

Visit https://www.genesee.edu/blah/page.html for info.

- First item
- Second item with https://example.com/a

After "Chunk it" the tool shows three boxes: Heading 1, Paragraph, and Bulleted
list. Each bare web address became a link whose text is the site name
(genesee.edu and example.com). "Needed Repairs" says:

Box 2: link (https://www.genesee.edu/blah/page.html) is missing descriptive text.
Box 3: link (https://example.com/a) is missing descriptive text.

Clicking the pencil on box 2, changing "genesee.edu" to real words, and
clicking the check mark removes that line from the list. When both links are
fixed, the list says "Nothing to fix."

On Finishing Touches, typing 10 in "External reading" and "Read chapter 1" in
"Before you start" adds those two items to the gold box under the title. The
Preview and the downloaded page both show it.
[Replace with output from your own run.]


FILES

index.html           the web page (the four screens)
style.css            how the page looks; uses Lato
main.py              the web page's behavior (buttons, boxes, screens, download)
md2bsp_web.py        the engine: cleaning, chunking, boxes, HTML, issues, page
pyscript.toml        tells PyScript where to find md2bsp_web.py and the template
template_gcc.html    the GCC page template the finished page is built in
fonts/               Lato web fonts and its license (SIL Open Font License)
LICENSE              MIT license, with a note about the GCC template and branding
README               this file
Not in the repo: input.md (test input)


KNOWN ISSUES

1. Accordions, tabs, videos, tables, and blockquotes are not built yet.
2. Clicking Back to step 1 and chunking again rebuilds the boxes from the
   original pasted text, so relabels and edits made on the Organize screen are
   lost. (Going back from Preview or Finishing Touches keeps them.)
3. Numbered lists must start with "1. " and bulleted lists with "- " or "* ".
   Nested lists are not supported (indentation is flattened).
4. Links inside headings are not turned into links or checked.
5. Only http:// and https:// links are recognized, and a web address that ends
   with ")" can be cut short.
6. A heading glued to its paragraph with no blank line stays one heading box.
7. Underscores for italics are not supported (asterisks only).
8. Headings deeper than H4 (##### and ######) become H4.
9. "Needed Repairs" checks one thing so far: link text that is empty or only
   the site name or web address.
10. The preview is a close simulation, not a copy of Brightspace. The gold box
    colors, the callout border, and the way "Guiding questions" is laid out
    are my estimates.
11. A downloaded page and a callout have been checked in a live Brightspace
    course. The rest of the page has not been checked everywhere.
12. The "Last published" date comes from the browser's clock.
13. The web page needs an internet connection (PyScript, Font Awesome, and the
    fonts load from the web).


CHANGES FROM PLAN

- Now: the same engine also runs in the browser through PyScript on GitHub
  Pages, so instructors need no setup.
- Words: "block" became "chunk" (a raw piece of text) and "box" (a chunk after
  it has been labeled), because block and box were confusing.
- Added: the Organize screen with a type dropdown, a live preview, and an
  Edit/Done button on each box, plus the "Needed Repairs" list.
- Added: a callout dropdown. A callout dresses up an existing box (a list stays
  a list) in a blue card with an icon, picked from eight choices.
- Added: a Finishing Touches screen for the top-of-page items (time, before
  you start, materials needed, key terms, guiding questions, working toward)
  and the bottom-of-page line (Week/Unit/Module and Last published).
- Added: Preview and Download.
- Changed: the screens went from two to four.
- Changed: a bare link used to become "missing text." It now becomes the site
  name, and the tool flags it until a human writes better words.
- Changed: headings stop at H4. Deeper headings become H4.
- Not yet done from the plan: accordions, tabs, videos, and file upload.


LIBRARIES AND OTHER MATERIALS

- Python standard library: datetime, html, math, os, sys, urllib.parse
- PyScript (Pyodide), release 2025.10.3, runs the Python in the browser
- Font Awesome 5.9.0 (free), loaded from cdnjs, for the link, callout, and
  page-detail icons
- Lato font (SIL Open Font License), served from the fonts/ folder
