MD2BSP - Markdown to Brightspace
Loy Gross


PURPOSE

MD2BSP turns Word doc or HTML into plain markdown text, which then gets
converted into a Brightspace web page, following the standard GCC template. 

Faculty paste their content into a web page. The tool splits it into boxes 
(one per heading, paragraph, list, or video), shows each box the way it will 
look on the finished page, and lets the instructor fix labels, typos, links 
without descriptive text. 

Additionally, faculty can dress each box as callouts, accordions, and videos. 
A last screen collects the best-practice extras that belong at the top and 
bottom of every page. Then the instructor downloads a finished page, ready 
to upload directly to Brightspace.

The goal is consistent, standardized pages free of extraneous clutter and 
easily dressed as key points or logical organizations rather than one-off 
copy-and-pasted conversions. Students get pages built consistently, and 
instructors / instructional designers get a quick path to making them.


HOW TO RUN IT

Live version (nothing to install): https://effierover.github.io/md2bsp/

1. Paste: paste your content into the box and click "Chunk it." Imports are 
   converted to markdown first (if not already markdown). A video link on a
   line by itself becomes a Video box.
   
2. Organize: check the boxes and the preview. Use the dropdowns to relabel a
   box, add a callout, or mark accordion titles and accordion content, and the
   pencil to fix text. For a video, fill in the title and length (the title is
   looked up for you when the browser allows it). Clear the "Needed Repairs"
   list. Click "Next: Finishing Touches."
   
3. Finishing Touches: fill in only what applies (reading, video, and activity
   minutes; before you start; materials needed; key terms; guiding questions;
   working toward; Week, Unit, or Module and its number). The video minutes are
   added up from your video lengths; change them if they are wrong. Click
   "Next: Preview."
   
4. Preview: look over the simulated page. Accordions show open. Click
   "Download," then upload the file to Brightspace.


FILES

index.html           the web page (the four screens)
style.css            how the page looks; uses Lato
main.py              the web page's behavior (buttons, boxes, screens, download)
md2bsp_web.py        the engine: cleaning, chunking, boxes, HTML, issues, page
pyscript.toml        tells PyScript where to find md2bsp_web.py and the template
template_gcc.html    the GCC page template the finished page is built in
preview_banner.jpg   a stand-in banner image used only in the preview
fonts/               Lato web fonts and its license (SIL Open Font License)
LICENSE              MIT license, with a note about the GCC template and branding
README               this file
Not in the repo: input.md (test input)


KNOWN ISSUES

1. Tabs, tables, blockquotes, and images are not built yet. Formatting from
   Word or a web page is not converted; paste plain text or markdown.
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
9. "Needed Repairs" checks link text that is empty or only the site name or web
   address; accordions (every title needs content, every content needs a
   title); and videos (every video needs a title and a length).
10. If an accordion is munged, the whole accordion exports as plain boxes
    until the repairs are made. The preview shows accordions open and cannot
    show how they open and close.
11. A video's title is looked up from YouTube or Vimeo when the browser allows
    it; otherwise type it. Lengths are always typed. Panopto links are
    recognized only on panopto.com addresses and have no title lookup.
12. The preview is a close simulation, not a copy of Brightspace. 
13. A downloaded page, a callout, an accordion, and a YouTube video have been
    checked in a live Brightspace course. Vimeo and Panopto videos and the
    rest of the page have not been checked everywhere.
14. The "Last published" date comes from the browser's clock.
15. The web page needs an internet connection (PyScript, Font Awesome, the
    fonts, and the video title lookup load from the web).


CHANGES FROM PLAN

- Added: the Organize screen with a type dropdown, a live preview, and an
  Edit/Done button on each box, plus the "Needed Repairs" list, which stays in
  view as you scroll.
- Added: a callout dropdown. A callout dresses up an existing box (a list stays
  a list) in a blue card with an icon, picked from eight choices.
- Added: accordions. The same dropdown marks a heading as an accordion title
  and a box as accordion content; marking a title marks the next box as its
  content. Neighbors form one accordion.
- Added: videos (YouTube, Vimeo, Panopto) as a box type, with title, length,
  and language fields, an automatic title when possible, and video minutes
  added up on Finishing Touches.
- Added: a Finishing Touches screen for the top-of-page items (time, before
  you start, materials needed, key terms, guiding questions, working toward)
  and the bottom-of-page line (Week/Unit/Module and Last published).
- Added: Preview (with a stand-in banner and the template's margins) and
  Download.
- Changed: a bare link used to become "missing text." It now becomes the site
  name, and the tool flags it until a human writes better words.
- Changed: headings stop at H4. Deeper headings become H4.
- Changed: typed-out no-break spaces (&nbsp;) are removed from pasted text.
- Not yet done from the plan: tabs, tables, blockquotes, images, file upload,
  and converting pasted Word or web formatting.


LIBRARIES AND OTHER MATERIALS

- Python standard library: asyncio, datetime, html, math, os, sys, urllib.parse
- PyScript (Pyodide), release 2025.10.3, runs the Python in the browser; its
  pyfetch function looks up video titles
- Font Awesome 5.9.0 (free), loaded from cdnjs, for the link, callout, video,
  and page-detail icons
- Lato font (SIL Open Font License), served from the fonts/ folder
