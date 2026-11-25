# MD2BSP - Markdown to Brightspace

Loy Gross

## Purpose

MD2BSP turns a Word doc or web page into plain markdown text, which then gets converted into a Brightspace web page that follows the standard GCC template.

Faculty paste their content into a web page. The tool splits it into boxes (one per heading, paragraph, list, or video), shows each box the way it will look on the finished page, and lets the instructor fix labels, typos, and links without descriptive text.

Faculty can also dress each box up as a callout, an accordion, or a video. A last screen collects the best-practice extras that belong at the top and bottom of every page. Then the instructor downloads a finished page, ready to upload directly to Brightspace.

The goal is consistent, standardized pages free of clutter, easily dressed up as key points or logical organizations, instead of one-off copy-and-pasted conversions. Students get pages built the same way every time, and instructors and instructional designers get a quick path to making them. Other campuses can adapt the tool to their own template (see TEMPLATE_VARIABLES.md).

Words this project uses

Chunk: a piece of the raw text (a heading, a paragraph, a list).
Box: a chunk after the program has decided what it is and labeled it. This is what you see and fix on the Organize screen.
Dressing: something a box wears: a callout, or an accordion title or accordion content. The box underneath stays what it was (a list stays a list); the dressing only changes how it is shown.
Needed Repairs: the list of things the tool thinks you should fix before you download.

How it works

Phase 1: pull the pasted text apart into chunks and put each chunk in a labeled box. The instructor can relabel boxes, fix typos and links, dress a box up as a callout, mark boxes as accordion titles and accordion content, and turn a video link into a video box. A Finishing Touches screen collects reading, video, and activity minutes, materials needed, key terms, guiding questions, and Week/Unit/Module.
Phase 2: convert the boxes into HTML.
Phase 3: drop the HTML into the template file and save it. On the web page, Download does this.
How to use it

## Live version (nothing to install): https://effierover.github.io/md2bsp/

Paste: paste your content into the box and click "Chunk it." You can copy straight from Word, Google Docs, or a web page; headings, paragraphs, lists, bold, italic, and links come across, and everything else is dropped. Imports are converted to markdown first (if not already markdown). A video link on a line by itself becomes a Video box.
Organize: check the boxes and the preview. Use the dropdowns to relabel a box, add a callout, or mark accordion titles and accordion content. The pencil icon allows editing; the trash can deletes a box, and an undo link appears in the gap where it was. For a video, fill in the title and length (the title is looked up for you when the browser allows it). Clear the "Needed Repairs" list. Click "Next: Finishing Touches."
Finishing Touches: fill in only what applies (reading, video, and activity minutes; before you start; materials needed; key terms; guiding questions; working toward; Week, Unit, or Module and its number). The video minutes are added up from your video lengths; change them if they are wrong. Click "Next: Preview."
Preview: look over the simulated page. Accordions show open. Pick a banner from the Banner menu in the right-hand column. Click "Download," then upload the file to Brightspace. The file name starts with W, U, or M and the number if you chose a Week, Unit, or Module (W11-title-of-page.html).
What "Needed Repairs" checks
Links: text that is empty, only the site name or web address, a vague phrase ("click here," "here," "read more"), or only a number like [1]. A bare web address becomes a site-name placeholder, and the tool flags it until a human writes better words.
Headings: no Heading 1, more than one Heading 1, and skipped levels (a Heading 2 followed by a Heading 4).
Bold lines that look like headings: a paragraph that is nothing but one bold phrase.
Accordions: every title needs content, and every content box needs a title.
Videos: every video needs a title and a length typed like 3:29.
Running the engine from the command line

Only the engine runs this way, not the web page.

Keep template_gcc.html in the same folder as md2bsp_web.py.
Keep input.md in the same folder as md2bsp_web.py.
Run: python md2bsp_web.py
Open output.html and look inside it.

## Files

index.html: the web page (the four screens)
style.css: how the page looks; uses Lato
main.py: the web page's behavior (buttons, boxes, screens, download)
md2bsp_web.py: the engine: cleaning, chunking, boxes, HTML, issues, page
pyscript.toml: tells PyScript where to find md2bsp_web.py and the template
template_gcc.html: the GCC page template the finished page is built in
TEMPLATE_VARIABLES.md: what a template must contain, for campuses that want to use their own
preview_banner.jpg: a stand-in banner image used only if the real banners can't be loaded
fonts/: Lato web fonts and its license (SIL Open Font License)
gcc_banners/: temporary repository of GCC images
.nojekyll: tells GitHub Pages to publish the files as they are
LICENSE: MIT license, with a note about the GCC template and branding
README.md: this file, and the one place the project is documented
Not in the repo: input.md (test input)

## Known issues

Tabs, tables, blockquotes, and images are not built yet. Pasting from Word, Google Docs, or a web page keeps only headings, paragraphs, lists, bold, italic, and http/https links. Colors, fonts, and sizes are dropped. Images are left out (the tool says so). Tables become one paragraph per row, with | between cells. Bold and italic together comes out bold only. Copying from a code editor is left as plain text.
Clicking Back to step 1 and chunking again rebuilds the boxes from the original pasted text, so relabels and edits made on the Organize screen are lost. (Going back from Preview or Finishing Touches keeps them.)
Numbered lists must start with "1. " and bulleted lists with "- " or "* ". Nested lists are not supported (indentation is flattened).
Links inside headings are not turned into links or checked.
Only http:// and https:// links are recognized, and a web address that ends with ")" can be cut short.
A heading glued to its paragraph with no blank line stays one heading box.
Underscores for italics are not supported (asterisks only).
Headings deeper than H4 (##### and ######) become H4.
Typing both in markdown writes crossed tags that Brightspace quietly corrects.
If an accordion is set up wrongly, the whole accordion exports as plain boxes until the repairs are made. The preview shows accordions open and cannot show how they open and close.
A video's title is looked up from YouTube or Vimeo when the browser allows it; otherwise type it. Lengths are always typed. Panopto links are recognized only on panopto.com addresses and have no title lookup.
The preview is a close simulation, not a copy of Brightspace.
A downloaded page, a callout, an accordion, and a YouTube video have been checked in a live Brightspace course. Vimeo and Panopto videos and the rest of the page have not been checked everywhere. GCC banners are hosted on GitHub for now, and a downloaded page that uses one has not been confirmed to show it in a live Brightspace course.
The "Last published" date comes from the browser's clock.
The web page needs an internet connection (PyScript, Font Awesome, the fonts, and the video title lookup load from the web).
The command-line run only reads and writes fixed file names (template_gcc.html, input.md, output.html).

Planned

Campus codes, so another campus can open index.html?campus=gcc (or its own code) and get its own template. What happens when the code is missing or unknown has not been decided.
Tabs, blockquotes, tables, and images (with an image alt text check), and file upload.
Recognizing a Word document whose headings are numbered ("1. Some topic," "2. Another topic") and suggesting an accordion.
More Needed Repairs checks: missing closings, a heading with nothing under it, an accordion lead-in, the same link text pointing to different addresses, typed bullets that should be real lists, large blocks of text, and email addresses typed as plain text.
A suggestion engine that suggests callouts, accordions, and tabs.
Carrying relabels and edits back when the instructor goes Back to step 1.
A generic template for people outside GCC.

Changes from plan

Added: the Organize screen with a type dropdown, a live preview, and an Edit/Done button on each box, plus the "Needed Repairs" list, which stays in view as you scroll.
Added: a callout dropdown. A callout dresses up an existing box (a list stays a list) in a blue card with an icon, picked from eight choices.
Added: accordions. The same dropdown marks a heading as an accordion title and a box as accordion content; marking a title marks the next box as its content. Neighbors form one accordion.
Added: videos (YouTube, Vimeo, Panopto) as a box type, with title, length, and language fields, an automatic title when possible, and video minutes added up on Finishing Touches.
Added: a Finishing Touches screen for the top-of-page items (time, before you start, materials needed, key terms, guiding questions, working toward) and the bottom-of-page line (Week/Unit/Module and Last published).
Added: Preview (with a stand-in banner and the template's margins) and Download.
Added: paste conversion. Copied Word, Google Docs, and web content becomes markdown before it is chunked.
Added: a delete button on each box, with a one-level Undo delete.
Added: a banner menu on Preview, with groups for SUNY defaults and GCC banners. The download uses the one you pick.
Added: the downloaded file name starts with W, U, or M and the number (W11-, M02-) when a Week, Unit, or Module is chosen.
Added: more Needed Repairs checks (vague and numbered link text, heading structure, bold lines that look like headings).
Changed: a bare link used to become "missing text." It now becomes the site name, and the tool flags it until a human writes better words.
Changed: headings stop at H4. Deeper headings become H4.
Changed: typed-out no-break spaces ( ) are removed from pasted text.
Not yet done from the plan: tabs, tables, blockquotes, images, and file upload.

## Libraries and other materials

Python standard library: asyncio, datetime, html, math, os, re, sys, urllib
Banner images are temporarily hosted by GitHub
PyScript (Pyodide), release 2025.10.3, runs the Python in the browser; its pyfetch function looks up video titles
Font Awesome 5.9.0 (free), loaded from cdnjs, for the link, callout, video, and page-detail icons
Lato font (SIL Open Font License), served from the fonts/ folder
The finished page also needs Bootstrap 4.3.1 and Font Awesome 5.9 (see TEMPLATE_VARIABLES.md for the full list)
