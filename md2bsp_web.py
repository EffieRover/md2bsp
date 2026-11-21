"""
md2bsp_web.py -- Builds a finished Brightspace web page, given content pieces

WHAT IT DOES:
    Reads a file of markdown text, and converts that markdown into the appropriate HTML sequences to be included in Brightspace. 
    Then it wraps those sequences in the standard GCC template and Bob's your uncle. Note: it works on a multi-step process 
    because I want the instructor to be able to check some things and clean some things up before it goes out.
    Words I use: a CHUNK is a piece of the raw text (a heading, a paragraph, a list).
                 a BOX is a chunk after the program has decided what it is and labeled it.
                 a DRESSING is something a box wears: a callout, or an accordion title or accordion content. The box
                 underneath stays what it was (a list stays a list); the dressing only changes how it is shown.
    Phase 1: pull apart the input file into chunks and put each chunk in a labeled box
        Phase 1.1 (done, on the web page): the instructor can relabel boxes, fix typos and links, dress a box up as a callout,
            mark boxes as accordion titles and accordion content, and turn a video link into a video box
        Phase 1.2 (done, on the web page): a Finishing Touches screen asks for reading, video, and activity minutes, materials needed, 
            key terms, guiding questions, and Week/Unit/Module (video minutes are added up from the video boxes)
    Phase 2: convert those boxes into HTML
    Phase 3: drop the HTML into the template file and save it (on the web page, Download does this)

    This file is the engine. main.py and index.html run it in the browser through PyScript:
    https://effierover.github.io/md2bsp/

HOW TO RUN IT (engine only, from the command line):
    1. Keep template_gcc.html in the same folder as this file.
    2. Keep input.md in the same folder as this file.
    3. Run: python md2bsp_web.py 
    4. Open output.html and look inside it. 

KNOWN ISSUES:
    1. The command-line run only reads and outputs fixed file names
    2. Numbered lists must start with 1. and a space
    3. Bulleted lists must start with either * or - and a space
    4. Does not manage nested lists
    5. ***both*** writes crossed tags that Brightspace quietly corrects
    6. Headings deeper than H4 (##### and ######) become H4
    7. Links inside headings are not turned into links or checked
    8. Only http:// and https:// links are recognized; a web address ending in ) can be cut short
    9. A heading glued to its paragraph with no blank line stays one heading box
    10. Underscores for italics are not supported (asterisks only)
    11. Going Back to step 1 on the web page erases relabels and edits
    12. If any piece of an accordion is set up wrongly, the whole stretch of accordion boxes comes out as plain boxes
    13. Panopto videos are recognized only on panopto.com addresses; video lengths are always typed, and titles are
        looked up (by main.py) for YouTube and Vimeo only

TODO:
    1. Tabs and blockquotes (dressing up boxes the way callouts and accordions do), then tables and images
    2. Accept uploaded markdown and Word files; convert pasted Word and web formatting (keep headings, paragraphs,
       lists, bold, italic, and links; drop the rest; flatten tables)
    3. Start the suggestion engine ... suggest callouts, accordions, tabs
    4. A Best Practices review step: missing closings, skipped heading levels, image alt text, a heading with nothing under it,
       an accordion lead-in
    5. Carry relabels and edits back when the instructor goes Back to step 1
    6. A generic template for people outside GCC

"""

# --- IMPORTS ---------------------------------------------------------------------------------------------------------

import os                                   # allows us to ask for device folders, for now
import sys                                  # allows us to stop the program with a message
from html import escape                     # make text safe to put inside HTML / sanitize it
import math                                 # cuz we be calculatin' reading time
from datetime import date                   # short date formats ...
from urllib.parse import urlparse, parse_qs # chops a web address into its parts (host, path, etc); parse_qs reads the ?q=stuff part
import re                                   # pattern matching, for reading styles out of pasted HTML
from html.parser import HTMLParser          # reads pasted HTML tag by tag

# --- SETTINGS --------------------------------------------------------------------------------------------------------

TESTING = True                              # print ALL the things!!!! (or false to not)
TEMPLATE_FILE = "template_gcc.html"         # the Brightspace page wrapper
INPUT_FILE = "input.md"                     # the fixed input file, for now
OUTPUT_FILE = "output.html"                 # the fixed output file, for now
WORDS_PER_MINUTE = 200                      # average reading speed, used for time on task calculation

# --- THE BANNERS: ALL LIVE IN ONE SHARED FOLDER INSIDE BRIGHTSPACE; A CHOICE IS JUST A FILE NAME ---
# --- BANNER_CHOICES is a list of groups; each group is (group label, [(file name, what the picture shows), ...]) ---
# --- to add a banner you uploaded to that folder, add one line to a group (or start a new group) ---

BANNER_FOLDER = "/shared/Course File Templates/GNC/pages/../_assets/img/"      # the address the downloaded page uses; Brightspace understands it
BANNER_PREVIEW_FOLDER = "https://mylearning.suny.edu/shared/Course%20File%20Templates/GNC/_assets/img/"   # the same folder as a web address, so the preview can show it from outside Brightspace
DEFAULT_BANNER_FILE = "banner_03.jpg"       # ye olde ubiquitous notebook and teapot file
DEFAULT_PAGE_BANNER = BANNER_FOLDER + DEFAULT_BANNER_FILE

BANNER_CHOICES = [
    ("SUNY defaults", [
        ("banner_01.jpg", "Laptop on a desk, overhead"),
        ("banner_02.jpg", "Coffee and grid notebook"),
        ("banner_03.jpg", "Notebook and teapot"),
        ("banner_04.jpg", "Desk lamp, succulent and iMac"),
        ("banner_05.jpg", "Camera, iPad and plant"),
        ("banner_06.jpg", "Office window with city view"),
        ("banner_07.jpg", "Notebooks and pens"),
        ("banner_08.jpg", "Laptop and coffee cup"),
    ]),
]

JUNK_TO_PLAIN = {                           # get rid of Microsoft "smart" bullshit
    "\u201c": '"',                          # curly open double quote
    "\u201d": '"',                          # curly close double quote
    "\u2018": "'",                          # curly open single quote
    "\u2019": "'",                          # curly close single quote, which is also the curly apostrophe
    "\u2026": "...",                        # the one-character ellipsis
    "\u2013": "-",                          # en dash, as in 10–15
    "\u2014": " - ",                        # em dash; spaces added so the words on either side don't mash together
    "\u00a0": " ",                          # non-breaking space, a classic Word landmine
    "&nbsp;": " ",                          # the same space, spelled out as text (shows up in pasted web and markdown)
    "&#160;": " ",                          # ...and the number versions of it
    "&#xa0;": " ",    
    "\u200b": "",                           # zero-width space, invisible and useless
    "\ufeff": "",                           # byte order mark, sometimes shows up at the start of a file
}

# --- THE BOX TYPES AN INSTRUCTOR CAN PICK FROM IN THE DROPDOWN -------------------------------------------------------
# --- each choice is (the short name we use in code, the words the instructor sees) ---

BOX_TYPE_CHOICES = [
    ("paragraph", "Paragraph"),
    ("h1", "Heading 1"),
    ("h2", "Heading 2"),
    ("h3", "Heading 3"),
    ("h4", "Heading 4"),
    ("ul", "Bulleted list"),
    ("ol", "Numbered list"),
    ("video", "Video"),
]

# --- THE CALLOUT CHOICES: (the short name we use in code, the words the instructor sees, the Font Awesome icon) ---
# --- a box with no callout simply has no "callout" key, or an empty one ---

CALLOUT_CHOICES = [
    ("question", "Callout Question", "fa-question-circle"),
    ("key", "Callout Key idea", "fa-exclamation-circle"),
    ("tip", "Callout Tip", "fa-lightbulb"),
    ("quote", "Callout Quote", "fa-quote-left"),
    ("steps", "Callout Steps", "fa-project-diagram"),
    ("plan", "Callout Plan", "fa-map"),
    ("documents", "Callout Documents", "fa-copy"),
    ("reminder", "Callout Reminder", "fa-bell"),
]

# --- READING THE INPUT FILE ------------------------------------------------------------------------------------------
# --- Read a text file, file_name, and return everything in it as one piece of text ---
# --- with open ... opens the file and closes it when we're done; utf-8 tells py how to read special characters ---

def read_file(file_name):
    try:
        with open(file_name, encoding="utf-8") as file:
            return file.read()

    # --- if the file isn't where we expect it or isn't called what we expect ---
    except FileNotFoundError:
        sys.exit(
            f"Can't find '{file_name}' in {os.getcwd()}.\n"
            "Move the file there, or check spelling."
        )
    # --- if the file is there but in some bizarre format ---
    except UnicodeDecodeError:
        sys.exit(
            f"Can't read '{file_name}' because it isn't UTF-8.\n"
            "Re-save your file as standard UTF-8 encoding or plain text."
        )

# --- CLEANING UP WORD AND WEB JUNK -----------------------------------------------------------------------------------
# --- go through the file while it's still text and remove Microsoft bullshit ---
# --- replace with nice clean characters ---

def clean_text(text):

    for junk, plain in JUNK_TO_PLAIN.items():   # go through the list, swapping each one
        text = text.replace(junk, plain)

    while "  " in text:                         # the em dash swap can leave double spaces; squash them
        text = text.replace("  ", " ")

    return text

# --- PASTE CONVERSION: COPIED WORD / GOOGLE DOCS / WEB STUFF BECOMES MARKDOWN -----------------------------------------
# --- when somebody copies from Word or a web page, the clipboard carries two versions: plain text and HTML ---
# --- the HTML one knows what's a heading, a list, bold, and a link; plain text knows none of that ---
# --- this section reads the HTML and keeps ONLY what our pages can use: headings, paragraphs, lists, bold, italic, links ---
# --- colors, fonts, sizes, spacing and every other bit of wild-ass formatting get dropped on purpose ---

SKIP_TAGS = {"script", "style", "head", "title", "svg", "noscript", "template", "iframe", "object",
             "canvas", "button", "select", "textarea", "xml", "nav"}   # whole elements we throw away, contents and all
VOID_TAGS = {"br", "img", "hr", "meta", "link", "input", "col", "area", "base", "wbr", "source", "embed", "param", "track"}   # tags with no closing partner
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
BLOCK_TAGS = {"p", "div", "section", "article", "header", "footer", "main", "aside", "blockquote", "pre",
              "address", "figure", "figcaption", "dl", "dt", "dd", "center", "form", "fieldset", "body", "html"}   # each one starts a new paragraph
SPACE_TAGS = BLOCK_TAGS | HEADING_TAGS | {"ul", "ol", "li", "tr", "td", "th", "table"}   # inside a table cell these just become a space

# --- DOES THIS CLIPBOARD HTML HAVE REAL STRUCTURE, OR IS IT JUST A CODE EDITOR'S COLORED SPANS? ---
# --- code editors copy colors as HTML but have no headings, lists, or links; for those we leave the plain-text paste alone ---

def html_has_structure(html):
    if re.search(r"<(h[1-6]|p|ul|ol|li|table|b|strong|i|em)(?=[\s>/])", html, re.IGNORECASE):
        return True
    return re.search(r"<a\s[^>]*href", html, re.IGNORECASE) is not None

# --- READ A STYLE ATTRIBUTE FOR BOLD OR ITALIC ---
# --- Google Docs makes bold with a style (font-weight:700), not a <b> tag, and wraps the WHOLE doc in a <b> that says font-weight:normal ---
# --- returns True (yes), False (explicitly not), or None (the style doesn't say) ---
# --- the (?<![\w-]) bit stops us from reading Word's "mso-bidi-font-weight" as if it were the real thing ---

def style_says_bold(style):
    found = re.search(r"(?<![\w-])font-weight\s*:\s*([a-z0-9]+)", style)
    if not found:
        return None
    value = found.group(1)
    if value in ("inherit", "initial", "unset"):
        return None
    if value in ("bold", "bolder"):
        return True
    if value.isdigit():
        return int(value) >= 600
    return False                                # normal, lighter

def style_says_italic(style):
    found = re.search(r"(?<![\w-])font-style\s*:\s*([a-z]+)", style)
    if not found:
        return None
    value = found.group(1)
    if value in ("italic", "oblique"):
        return True
    if value == "normal":
        return False
    return None

# --- CLEAN UP A PASTED LINK; RETURN None IF WE CAN'T USE IT ---
# --- Google Docs and Outlook wrap every link in a redirect; dig out the real address ---
# --- only http/https links survive (our chunker only recognizes those); mailto, #anchors and relative links become plain text ---
# --- spaces and parentheses get encoded because a ")" inside the address would end the markdown link early ---

def clean_pasted_link(href):
    if not href:
        return None
    href = href.strip()
    try:
        parts = urlparse(href)
        host = (parts.hostname or "").lower()
        wrapped = None
        if host.endswith("google.com") and parts.path == "/url":
            wrapped = parse_qs(parts.query).get("q") or parse_qs(parts.query).get("url")
        elif host.endswith("safelinks.protection.outlook.com"):
            wrapped = parse_qs(parts.query).get("url")
        if wrapped:
            href = wrapped[0]
            parts = urlparse(href)
    except ValueError:                          # garbage address, like a broken [ in the host
        return None
    if parts.scheme not in ("http", "https"):
        return None
    return href.replace(" ", "%20").replace("(", "%28").replace(")", "%29")

# --- A RUN IS A PIECE OF TEXT THAT ALL LOOKS THE SAME: (text, bold, italic, link address) ---
# --- turn a pile of runs into one line of markdown ---
# --- spaces stay OUTSIDE the ** and * markers, because our bold/italic code ignores markers hugging spaces ---
# --- bold AND italic comes out bold only; our chunker can't nest them yet ---

def emphasize(text, bold, italic):
    core = text.strip()
    if core == "":
        return text
    lead = text[:len(text) - len(text.lstrip())]
    trail = text[len(text.rstrip()):]
    if bold:
        core = "**" + core + "**"
    elif italic:
        core = "*" + core + "*"
    return lead + core + trail

def render_runs(runs, plain=False):

    pieces = []
    for text, bold, italic, href in runs:
        text = re.sub(r"\s+", " ", text)        # Word wraps its HTML at weird places; every run of whitespace becomes one space
        if text == "":
            continue
        if plain:                               # headings get no bold, italic or links, just words
            bold, italic, href = False, False, None
        if bold:
            italic = False
        pieces.append([text, bold, italic, href])

    merged = []                                 # glue neighbors that look identical
    for piece in pieces:
        if merged and merged[-1][1:] == piece[1:]:
            merged[-1][0] += piece[0]
        else:
            merged.append(piece)

    line = ""
    i = 0
    while i < len(merged):
        href = merged[i][3]
        j = i
        inner = ""
        while j < len(merged) and merged[j][3] == href:     # everything with the same link address is ONE link
            text = merged[j][0]
            if href:
                text = text.replace("[", "").replace("]", "")
            inner += emphasize(text, merged[j][1], merged[j][2])
            j += 1
        if href and inner.strip() != "":
            lead = inner[:len(inner) - len(inner.lstrip())]
            trail = inner[len(inner.rstrip()):]
            inner = lead + "[" + inner.strip() + "](" + href + ")" + trail
        line += inner
        i = j

    return " ".join(line.split())               # squash double spaces and trim both ends

# --- THE READER: WALKS THROUGH THE HTML TAG BY TAG AND PILES UP BLOCKS (HEADINGS, PARAGRAPHS, LISTS) ---
# --- HTMLParser is built into python; it calls handle_starttag / handle_endtag / handle_data as it walks along ---

class PasteReader(HTMLParser):

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []                        # the finished pile: dicts with "t" = heading / para / list
        self.runs = []                          # text we've seen since the last block ended
        self.stack = []                         # open tags, each with its (bold, italic, link) so formatting inherits downward
        self.skip = None                        # [tag, depth, capture]; set while we're inside something we're throwing away
        self.heading = 0                        # which heading level we're inside, 0 for none
        self.list_stack = []                    # open <ul>/<ol> tags
        self.li_depth = 0                       # how many <li> deep we are
        self.group = None                       # the list block currently collecting items
        self.group_id = None                    # Word's own id for its list, so two different lists don't merge
        self.word_item = None                   # set while inside a Word fake-bullet paragraph
        self.table_depth = 0
        self.row = None
        self.images = 0
        self.table_rows = 0
        self.nested = False
        self.high_heading = False

    # --- what formatting are we sitting inside right now? ---
    def current_format(self):
        if self.stack:
            return self.stack[-1][1], self.stack[-1][2], self.stack[-1][3]
        return False, False, None

    def add_space(self):
        self.runs.append((" ", False, False, None))

    def add_para(self, text):
        self.group = None
        self.blocks.append({"t": "para", "text": text})

    def add_heading(self, level, text):
        self.group = None
        if level > 4:                           # our boxes only go to level 4
            level = 4
            self.high_heading = True
        self.blocks.append({"t": "heading", "level": level, "text": text})

    def add_item(self, text, ordered, list_id=None):
        if self.group is None or self.group_id != list_id:
            self.group = {"t": "list", "ordered": ordered, "items": []}
            self.group_id = list_id
            self.blocks.append(self.group)
        self.group["items"].append(text)

    # --- turn the pile of runs into a block, and decide what kind of block it is ---
    def flush(self):
        text = render_runs(self.runs, plain=bool(self.heading))
        self.runs = []
        if text == "":
            return
        if self.heading:
            self.add_heading(self.heading, text)
        elif self.li_depth:
            self.add_item(text, bool(self.list_stack) and self.list_stack[0] == "ol")
        elif self.word_item:
            self.add_item(text, self.word_item["ordered"], self.word_item["id"])
        else:
            self.add_para(text)

    # --- we just finished skipping an element; if it was Word's bullet marker, peek at what it said ---
    def finish_skip(self):
        capture = self.skip[2]
        self.skip = None
        if capture is not None and self.word_item is not None:
            marker = "".join(capture).replace("\xa0", " ").strip()
            # "1." "a." "iv)" are numbers; the dot, the square, the o are bullets
            self.word_item["ordered"] = re.fullmatch(r"\(?[0-9A-Za-z]{1,4}[.)]", marker) is not None

    def handle_starttag(self, tag, attrs):
        attrs = {name: (value or "") for name, value in attrs}
        style = attrs.get("style", "").lower()
        squeezed = style.replace(" ", "")

        if self.skip:                           # still inside a thrown-away element; just keep count of same-name tags
            if tag == self.skip[0] and tag not in VOID_TAGS:
                self.skip[1] += 1
            return

        if tag not in VOID_TAGS:
            if tag in SKIP_TAGS or "display:none" in squeezed or "mso-hide:all" in squeezed:
                self.skip = [tag, 1, None]
                return
            if "mso-list:ignore" in squeezed:   # Word's fake bullet or number; read it, then throw it away
                self.skip = [tag, 1, []]
                return

        if tag == "br":
            self.add_space()
            return
        if tag == "img":
            self.images += 1
            return
        if tag == "hr":
            if not self.table_depth:
                self.flush()
            return
        if tag in VOID_TAGS:
            return

        # --- formatting: tag first, then let the style attribute overrule ---
        bold, italic, href = self.current_format()
        if tag in ("b", "strong"):
            bold = True
        if tag in ("i", "em"):
            italic = True
        says = style_says_bold(style)
        if says is not None:
            bold = says
        says = style_says_italic(style)
        if says is not None:
            italic = says
        if tag == "a":
            href = clean_pasted_link(attrs.get("href"))
        self.stack.append((tag, bold, italic, href))

        # --- tables: flatten them. each row will become one paragraph ---
        if tag == "table":
            if self.table_depth == 0:
                self.flush()
            else:
                self.add_space()
            self.table_depth += 1
            return
        if self.table_depth:
            if self.table_depth == 1 and tag == "tr":
                self.row = []
            elif self.table_depth == 1 and tag in ("td", "th"):
                self.runs = []
            elif tag in SPACE_TAGS:
                self.add_space()
            return

        # --- everything else ---
        if tag in HEADING_TAGS:
            self.flush()
            self.heading = int(tag[1])
        elif tag in ("ul", "ol"):
            self.flush()                        # text sitting in a parent <li> becomes its item first
            if self.list_stack:
                self.nested = True
            else:
                self.group = None               # a brand new list starts a brand new block
            self.list_stack.append(tag)
        elif tag == "li":
            self.flush()
            self.li_depth += 1
        elif tag in BLOCK_TAGS:
            if self.li_depth:                   # Google Docs puts <p> inside <li>; that's the same item, not a new paragraph
                self.add_space()
            else:
                self.flush()
                if tag == "p" and "mso-list" in squeezed and "mso-list:none" not in squeezed:
                    found = re.search(r"mso-list:(l\d+)", squeezed)
                    level = re.search(r"level(\d+)", squeezed)
                    if level and int(level.group(1)) > 1:
                        self.nested = True
                    self.word_item = {"id": found.group(1) if found else "word", "ordered": False}

    def handle_endtag(self, tag):
        if self.skip:
            if tag == self.skip[0]:
                self.skip[1] -= 1
                if self.skip[1] == 0:
                    self.finish_skip()
            return
        if tag in VOID_TAGS:
            if tag == "br":
                self.add_space()
            return

        for i in range(len(self.stack) - 1, -1, -1):    # close this tag, and anything left open inside it
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

        if tag == "table":
            if self.table_depth > 1:
                self.add_space()
            if self.table_depth:
                self.table_depth -= 1
            if self.table_depth == 0:
                self.flush()
            return
        if self.table_depth:
            if self.table_depth == 1 and tag in ("td", "th"):
                cell = render_runs(self.runs)
                self.runs = []
                if cell and self.row is not None:
                    self.row.append(cell)
            elif self.table_depth == 1 and tag == "tr":
                if self.row:
                    self.add_para(" | ".join(self.row))
                    self.table_rows += 1
                self.row = None
            elif tag in SPACE_TAGS:
                self.add_space()
            return

        if tag in HEADING_TAGS:
            self.flush()
            self.heading = 0
        elif tag in ("ul", "ol"):
            self.flush()
            if self.list_stack:
                self.list_stack.pop()
            if not self.list_stack:
                self.group = None
        elif tag == "li":
            self.flush()
            self.li_depth = max(0, self.li_depth - 1)
        elif tag in BLOCK_TAGS:
            if self.li_depth:
                self.add_space()
            else:
                self.flush()
                if tag == "p":
                    self.word_item = None

    def handle_data(self, data):
        if self.skip:
            if self.skip[2] is not None:
                self.skip[2].append(data)
            return
        bold, italic, href = self.current_format()
        self.runs.append((data.replace("\xa0", " "), bold, italic, href))

# --- THE ONE-STOP FUNCTION: HTML IN, (MARKDOWN, NOTES) OUT ---
# --- the notes are plain-English things we dropped or flattened, so the page can tell the person ---
# --- Word and Chrome mark where the copied part starts and ends; everything outside is page furniture ---

def html_to_markdown(html):

    start = html.find("<!--StartFragment-->")
    end = html.find("<!--EndFragment-->")
    if start != -1 and end > start:
        html = html[start + len("<!--StartFragment-->"):end]

    reader = PasteReader()
    reader.feed(html)
    reader.close()
    reader.flush()

    pieces = []
    for block in reader.blocks:
        if block["t"] == "heading":
            pieces.append("#" * block["level"] + " " + block["text"])
        elif block["t"] == "list":
            lines = []
            for number, item in enumerate(block["items"], start=1):
                lines.append(f"{number}. {item}" if block["ordered"] else f"- {item}")
            pieces.append("\n".join(lines))
        else:
            pieces.append(block["text"])

    notes = []
    if reader.images:
        notes.append(f"{reader.images} image(s) left out. Images aren't supported yet, so add them back in Brightspace.")
    if reader.table_rows:
        notes.append(f"A table was flattened into {reader.table_rows} paragraph(s), one per row, with cells separated by |. Check that it still reads right.")
    if reader.nested:
        notes.append("Nested list items were moved up to one level.")
    if reader.high_heading:
        notes.append("A heading below level 4 was made a level 4 heading.")

    return "\n\n".join(pieces), notes

# --- WHAT SHOULD A BARE LINK SAY UNTIL A HUMAN FIXES IT? THE WEB ADDRESS'S SITE NAME ----------------------------------
# --- www.genesee.edu/blah/page.html becomes genesee.edu; subdomains stay (library.genesee.edu) so links are tellable apart ---

def domain_label(url):

    host = urlparse(url).hostname           # hostname is lowercase and has no port; it's None if the url is garbage
    if not host:
        return "link"
    if host.startswith("www."):
        host = host[4:]                     # www tells nobody anything
    return host

# --- SHRINK LINK TEXT DOWN SO WE CAN COMPARE IT TO A WEB ADDRESS -----------------------------------------------------
# --- lowercase, no http(s)://, no www., no slash on the end ---

def plain_link_text(text):

    text = text.strip().lower()
    for prefix in ("https://", "http://"):
        if text.startswith(prefix):
            text = text[len(prefix):]
    if text.startswith("www."):
        text = text[4:]
    return text.rstrip("/")

# --- IS THIS LINK TEXT USELESS TO A HUMAN? ---------------------------------------------------------------------------
# --- yes if it's empty, says "missing text", or is just the site name or web address; that's a link that doesn't say where it goes ---

def link_text_is_weak(text, url):

    plain = plain_link_text(text)
    return plain in ("", "missing text", domain_label(url), plain_link_text(url))

# --- TURN BARE URLS INTO PROPER MARKDOWN LINKS -----------------------------------------------------------------------
# --- finds web addresses sitting loose in the text and wraps them as [site name](url) so every link looks the same ---
# --- the site name is a placeholder: a human has to replace it with real words, and find_issues nags until they do ---
# --- the format [text goes here](url goes here) is standard markdown, and it lets a link say where it goes ---

def structure_bare_urls(text):

    fixed_lines = []                            # initialize, initialize, initialize
    text = text.replace("] (", "](")            # clean up extra spaces
    text = text.replace("( http", "(http")      # clean up moar extra spaces
    text = text.replace(" )", ")")              # clean up the other white spaces

    for line in text.splitlines():              # for each line in the file
        words = line.split(" ")                 # chop the line into words

        for i, word in enumerate(words):        # for each word in the line
            if word.startswith("http://") or word.startswith("https://"):
                trailing = ""                   # initialize punctuation leftovers
                while word and word[-1] in ".,;:!?)\"'":
                    trailing = word[-1] + trailing # if the next character after the url is punctuation, save it in trailing
                    word = word[:-1]            # and peel that punctuation off the original url

                words[i] = f"[{domain_label(word)}]({word})" + trailing   # wrap the bare url, then put the punctuation back on the end
                
        fixed_lines.append(" ".join(words))     # glue the words back into a line

    return "\n".join(fixed_lines)               # glue the lines back into a file

# --- SPLITTING THE MARKDOWN INTO CHUNKS ------------------------------------------------------------------------------
# --- A "chunk" is a run of lines with no blank line inside it: a heading, a paragraph, or a whole list; this ---
# --- function takes a long string of text (the whole file? *Yup*) and splits it into a list of chunk elements ---

def split_into_chunks(markdown_text):
    finished_chunks = []                    # finished stack of taped-together content chunks
    current_chunk = []                      # pile of stuff on the table right now

    for line in markdown_text.splitlines():
        if line.strip() != "":              # if the current line of the file has actual content in it, pile it on the table
            current_chunk.append(line)
        else:                               # ha! we hit an empty line. make the current pile into a finished chunk and reset
            if current_chunk:
                finished_chunks.append("\n".join(current_chunk))
                current_chunk = []
    if current_chunk:
        finished_chunks.append("\n".join(current_chunk))
    return finished_chunks

# --- MAKING THIS A FUNCTION BECAUSE IT'S THE DEFAULT ALL OVER THE PLACE ----------------------------------------------
# --- In each check, if it's not X, then it's a paragraph; make it a one-line function so we don't have to retype ---

def make_paragraph(text):
    return {"kind": "paragraph", "text": text}

# --- IS IT A HEADER? RETURN IT AS SUCH -------------------------------------------------------------------------------
# --- If a chunk starts with a hashtag, it's probably an H1 through H6. Or should be. ---

def chunk_to_header(chunk):

    without_hashes = chunk.lstrip("#")      # Take the hashtags off the front, and see how much shorter it got.
    level = len(chunk) - len(without_hashes)

    # It's a real heading only if a space follows the hashtags, and there are 6 hashtags or fewer.
    if without_hashes.startswith(" ") and level <= 6:
        if level > 4:
            level = 4                        # fuck h5 and h6. Really.
        return {"kind": "heading", "level": level, "text": without_hashes.strip()}

    # Otherwise, it only started with a hashtag (like "#BTS is trending"), so treat it as a paragraph.
    return make_paragraph(chunk)

# --- IS IT A LIST? RETURN IT AS SUCH ---------------------------------------------------------------------------------
# --- bullet lists have lines starting with "- " or "* " numbered lists start with digit, dot, space ---

def chunk_to_list(chunk):

    if chunk.startswith("- ") or chunk.startswith("* "): # are we parsing bullets or numbers?
        ordered = False
    else:                               
        ordered = True
    items = []                          # initialize this puppy

    for line in chunk.splitlines():

        if ordered:                     # need to split at the '. ' to number and then rest of line

            number, dot, actualcontent = line.partition(". ")
            if number.isdigit():
                items.append(actualcontent)
            else:
                items[-1] = items[-1] + " " + line.strip()   # plain character equals a continuation of the previous line: glue it on

        else:                           # this is a bullet list, just split it

            if line.startswith("- ") or line.startswith("* "):
                items.append(line[2:])  # skip the first two characters - the bullet marker and space
            else:
                items[-1] = items[-1] + " " + line.strip()   # plain character equals a continuation of the previous line: glue it on

    return {"kind": "list", "ordered": ordered, "items": items}

# --- WRAP TEXT BETWEEN PAIRS OF MARKERS ------------------------------------------------------------------------------
# --- finds text sitting between two markers (like ** or *) and wraps it in an HTML tag; used for bold and italic ---

def wrap_pairs(text, marker, tag):

    parts = text.split(marker)              # chop at every marker; the odd-numbered pieces (1, 3, 5...) sat between a pair

    if len(parts) % 2 == 0:                 # an even number of pieces means one marker has no partner; leave it all alone
        return text

    finished_text = parts[0]                # initialize the output with the starting text
    for i in range(1, len(parts), 2):       # visit the in-between pieces: 1, 3, 5...
        inside = parts[i]                   # the piece that sat between two markers
        outside = parts[i + 1]              # the piece that comes after it
        if inside == "" or inside.startswith(" ") or inside.endswith(" "):
            finished_text += marker + inside + marker + outside   # doesn't look like real emphasis (like 5 * 3 * 2); put the original back
        else:
            finished_text += f"<{tag}>{inside}</{tag}>" + outside

    return finished_text

# --- TURN [TEXT](URL) INTO A REAL LINK -------------------------------------------------------------------------------
# --- takes a piece of text that has already been escaped and swaps each markdown link for an HTML link ---
# --- every link opens in a new tab, with an icon for sighted users and hidden words for screen readers ---
# --- remember link formats are all [text here](urlhere) at this point ---
# --- also adds bold and italic tags ---

def format_inline(text):

    finished_text = ""

    text = escape(text, quote=False)    # slipping those weird characters in there, were ya?

    text = wrap_pairs(text, "**", "strong") # that's a <strong></strong> pair
    text = wrap_pairs(text, "*", "em")  # that's an <em></em> pair

    rest = text                         # need a place to hold the pieces while we split URL segments

    while True:
        url_seam_position = rest.find("](http") # lookee, we found a link! Maybe?
        if url_seam_position == -1:     # no, no findee
            break

        open_bracket_position = rest.rfind("[", 0, url_seam_position) # from the URL pattern, look backwards to the beginning of the text
        close_paren_position = rest.find(")", url_seam_position) # from the URL pattern, look forwards to the end of the URL

        if open_bracket_position == -1 or close_paren_position == -1:
            finished_text += rest[:url_seam_position + 2] # this is not a link at all, copy it as-is onto the finished pile
            rest = rest[url_seam_position + 2:]   # and keep looking through the rest of the pile
            continue

        visible_link_text = rest[open_bracket_position + 1:url_seam_position].strip()
        url = rest[url_seam_position + 2:close_paren_position].replace('"', "%22")

        if visible_link_text == "":
            visible_link_text = domain_label(url)

        finished_text += rest[:open_bracket_position]
        finished_text += (
            f'<a href="{url}" target="_blank" rel="noopener">{visible_link_text} '
            '<span class="fas fa-external-link-alt fa-xs" aria-hidden="true"></span>'
            '<span class="sr-only">(opens in a new tab)</span></a>'
        )
        rest = rest[close_paren_position + 1:]

    return finished_text + rest

# --- OKAY, WE PARSED IT INTO BOXES; PHASE 2, NOW TURN THE BOXES INTO HTML --------------------------------------------
# --- takes a box and returns a piece of matching HTML ---

def box_to_plain_html(box):

    kind = box["kind"]                  # what kind of critter do we have here?

    if kind == "heading":
        level = box["level"]
        if level == 1:
            alignment = "text-center"   # H1 is always centered
        else:
            alignment = "text-left"     # force all lower headers to the left, cuz I hate what Brightspace does
        tag = "h" + str(level)
        return f'<{tag} class="{alignment}">{escape(box["text"], quote=False)}</{tag}>'
                                        # building correct HTML structures, sample: <h1 class="text-center">content</h1>

    if kind =="list":
        if box["ordered"]:              # remember this was a boolean
            tag = "ol"
        else:
            tag = "ul"                  # I love lists, so simple!

        rows = []                       # initialize, initialize, initialize
        for item in box["items"]:       # for each item in the list, wrap it in list item tags
            rows.append(f"<li>{format_inline(item)}</li>")

        all_rows = "\n".join(rows)      # we'll put line breaks in there in case human eyes have to look at this crap
        return f"<{tag}>\n{all_rows}\n</{tag}>"
                                        # and return something like <ul><li>first</li><li>second</li></ul>

    if kind == "paragraph":
        return f'<p>{format_inline(box["text"])}</p>'

    if kind == "video":
        info = find_video(box["text"])
        if info is None:
            return f'<p>{format_inline(box["text"])}</p>'     # no address left to embed; show the words
        fields = get_video_fields(box)
        return make_video_html(info, fields["title"], fields["length"], fields["language"], "#")
                                        # the "#" is a placeholder; a later step numbers the links in page order
    
    sys.exit(f"What on earth did you send me? We can't convert this {kind}")
                                        # because every type above has a return statement, if we make it here, we done screwed something up

# --- THE BLUE CALLOUT CARD: AN ICON ON THE LEFT, WHATEVER THE BOX SAYS ON THE RIGHT ---
# --- the icon is decoration, so screen readers skip it ---

def wrap_callout(inner_html, icon_class):

    return (
        '<!-- callout begin -->\n'
        '<div class="card card-graphic">\n'
        '<div class="card-body">\n'
        '<div class="card-icon">\n'
        f'<p><span class="fas {icon_class}" aria-hidden="true"></span></p>\n'
        '</div>\n'
        '<div class="card-text">\n'
        f'{inner_html}\n'
        '</div>\n'
        '</div>\n'
        '</div>\n'
        '<!-- callout end -->'
    )

# --- A BOX AS HTML: ITS PLAIN HTML, WRAPPED IN A CALLOUT IF IT HAS ONE (HEADINGS NEVER DO) ---

def box_to_html(box):

    html = box_to_plain_html(box)
    if box["kind"] == "heading":
        return html
    for name, label, icon_class in CALLOUT_CHOICES:
        if box.get("dressing") == name:
            return wrap_callout(html, icon_class)
    return html

# --- SO NOW CALCULATE TIME ON TASK FOR THE POOR STUDENT --------------------------------------------------------------
# --- adds up words not in the title and divides by reading speed ---

def calculate_time_on_task(boxes):

    total_words = 0                     # done initializing, yet? Yeah? Good.

    for box in boxes:

        kind = box["kind"]              # what kind of critter do we have again?

        if kind == "heading":    # reading time typically doesn't include the page title
            if box["level"] != 1:
                total_words += len(box["text"].split())

        elif kind == "list":     # gotta add up all the list items
            for item in box["items"]:
                total_words += len(item.split())

        elif kind == "paragraph":
            total_words += len(box["text"].split())

        elif kind == "video":
            pass                         # a video isn't reading; its length gets counted separately
        
        else:
            sys.exit(f"What have we done? Can't calculate time on task for {kind}")
                                        # because we should be matching the types we created...
    minutes = math.ceil(total_words / WORDS_PER_MINUTE)
    return minutes

# --- PAGE HEADER LIST: TIME ON TASK, MATERIALS, ETC, THAT INSTRUCTOR SHOULD REALLY HAVE ---------------------------------
# --- three small pieces: one makes a single row, one wraps the rows in the gold callout, one decides which rows exist ---
# --- right now only the Time row exists; more rows will plug into make_page_leader as we add them ---

def make_leader_row(icon, label, text):

    return (
        '<li class="d-flex align-items-baseline mb-1">'
        f'<span class="fas {icon} fa-fw mr-3" aria-hidden="true"></span>'  # the icon is its own piece, so long text wraps in a clean column
        f'<span><strong>{escape(label, quote=False)}</strong> {escape(text, quote=False)}</span>'
        '</li>'
    )

def make_leader_list_row(icon, label, lines):       # for guiding questions: the label, then each question on its own line

    escaped_lines = [escape(line, quote=False) for line in lines]
    return (
        '<li class="d-flex align-items-baseline mb-1">'
        f'<span class="fas {icon} fa-fw mr-3" aria-hidden="true"></span>'
        f'<span><strong>{escape(label, quote=False)}</strong> {" ".join(escaped_lines)}</span>'
        '</li>'
    )

# --- A TYPED BOX MIGHT HAVE LINE BREAKS OR EXTRA SPACES IN IT; MAKE IT ONE TIDY LINE ---

def one_line(text):
    return " ".join(text.split())

def wrap_leader_rows(rows):

    all_rows = "\n".join(rows)              # human eyes will read this, so one row per line
    return (
        '<!-- callout begin -->\n'
        '<div class="card card-gold mb-3">\n'
        '<div class="card-body">\n'
        '<ul class="list-unstyled mb-0" style="font-size: 16px;">\n'      # 16px set once, here, for every row
        f'{all_rows}\n'
        '</ul>\n'
        '</div>\n'
        '</div>\n'
        '<!-- callout end -->'
    )

# --- THE WORDS FOR THE TIME ROW: READING ALWAYS, THE OTHERS ONLY IF THE INSTRUCTOR GAVE MINUTES ---

def make_time_text(minutes, details):

    pieces = [f"Reading: {minutes} min"]
    extras = [("external", "External Reading"), ("video", "Video"), ("activity", "Activity")]
    for key, label in extras:
        value = one_line(details.get(key, ""))
        if value.isdigit() and int(value) > 0:    # isdigit keeps out blanks, minus signs, and "abc"
            pieces.append(f"{label}: {int(value)} min")
    return " | ".join(pieces)

# --- THE GOLD CARD UNDER THE H1: A TIME ROW ALWAYS, THEN ONE ROW FOR EACH BOX THE INSTRUCTOR FILLED IN ---

def make_page_leader(minutes, details=None):

    if details is None:                     # the command-line run has no web page to ask, so it passes nothing
        details = {}

    rows = []                               # only the rows that have something to say go in here
    rows.append(make_leader_row("fa-clock", "Time", make_time_text(minutes, details)))

    before = one_line(details.get("before", ""))
    if before != "":
        rows.append(make_leader_row("fa-clipboard-list", "Before you start", before))

    materials = one_line(details.get("materials", ""))
    if materials != "":
        rows.append(make_leader_row("fa-tools", "Materials needed", materials))

    terms = one_line(details.get("terms", ""))
    if terms != "":
        rows.append(make_leader_row("fa-key", "Key terms", terms))

    questions = [one_line(line) for line in details.get("questions", "").splitlines() if one_line(line) != ""]
    if questions:
        rows.append(make_leader_list_row("fa-question-circle", "Guiding questions", questions))

    working = one_line(details.get("working", ""))
    if working != "":
        rows.append(make_leader_row("fa-bullseye", "Working toward", working))

    return wrap_leader_rows(rows)

# --- THE LAST LINE OF THE PAGE: WEEK / UNIT / MODULE AND NUMBER (IF GIVEN), THEN WHEN IT WAS PUBLISHED ---
# --- no number, no Week line; the page still says when it was published ---

def make_page_end(details=None):

    if details is None:                     # the command-line run has no web page to ask, so it passes nothing
        details = {}

    today = date.today()
    published = f"{today.month}/{today.day}/{today.year}"     # short date, no leading zeros: 11/9/2026

    lines = []
    unit_number = one_line(details.get("unit_number", ""))
    if unit_number.isdigit() and int(unit_number) > 0:        # isdigit keeps out blanks, minus signs, and "abc"
        unit_type = one_line(details.get("unit_type", ""))
        if unit_type not in ("Week", "Unit", "Module"):       # anything else falls back to Week
            unit_type = "Week"
        lines.append(f"{unit_type} {int(unit_number)}")
    lines.append(f"Last published: {published}")

    return '<p style="font-size: 16px;">' + "<br>".join(lines) + "</p>"
    

# --- WHICH BANNER FILE DID THE INSTRUCTOR PICK? ---
# --- only names on the list above count; anything else (blank, typo, nothing chosen) quietly means the default ---

def get_banner_file(details):
    chosen = (details or {}).get("banner", "")
    for group_label, banners in BANNER_CHOICES:
        for file_name, description in banners:
            if file_name == chosen:
                return chosen
    return DEFAULT_BANNER_FILE

# --- THE WEB ADDRESS THE PREVIEW LOADS THE BANNER FROM ---

def banner_preview_url(file_name):
    return BANNER_PREVIEW_FOLDER + get_banner_file({"banner": file_name})

# --- IT PUTS THE HTML IN THE TEMPLATE OR ELSE IT GETS THE WONKY FILE AGAIN -------------------------------------------
# --- takes the template text, boxes, content, works out the title, banner, leader ---

def build_page(template, boxes, content, page_leader, details=None):

    # --- find the page title. Will be the H1 tag on the page ---
    page_title = "Untitled Page"        # in case we don't find one
    for box in boxes:
        if box["kind"] == "heading" and box["level"] == 1:
            page_title = box["text"]
            break                       # okay, we found it, stop looking

    # --- the banner the instructor picked (or the default) ---
    banner = BANNER_FOLDER + get_banner_file(details)

    # --- the time list goes right after the H1; the 1 at the end means only the first </h1> ---
    content = content.replace("</h1>", "</h1>\n" + page_leader, 1)

    # --- plug 'em in Charlie ---
    page = template.replace("{{TITLE}}", escape(page_title, quote=False))
                                        # initialize by loading in the template; replace the title while we're at it
    page = page.replace("{{BANNER_SRC}}", banner)
                                        # now load in the top of page banner
    page = page.replace("{{CONTENT}}", content)
                                        # and finally content goes in
    return page

# --- WRITING THE FINISHED FILE ---------------------------------------------------------------------------------------
# --- lots of stuff could go wrong here ---

def write_file(file_name, text):

    try:
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(text)

    except PermissionError:
        sys.exit(
            f"Can't save '{file_name}' due to permissions error.\n"
        )

# --- WHAT TYPE IS THIS BOX RIGHT NOW? RETURN ITS SHORT NAME (SO THE DROPDOWN CAN START ON THE RIGHT CHOICE) ---------

def box_type_name(box):

    kind = box["kind"]

    if kind == "heading":
        return "h" + str(box["level"])      # heading level 2 becomes "h2"

    if kind == "list":
        if box["ordered"]:
            return "ol"
        return "ul"

    if kind == "video":
        return "video"
    
    return "paragraph"                      # everything else is a paragraph

# --- THE INSTRUCTOR PICKED A NEW TYPE: RETURN A NEW BOX WITH THE SAME WORDS, RELABELED ------------------------------
# --- lists keep one item per line; headings and paragraphs get all the words in one piece ---

def get_box_lines(box):
    # a box remembers its original lines, so changing types never loses them
    if "lines" in box:
        return box["lines"]
    if box["kind"] == "list":
        return box["items"]
    return box["text"].splitlines()

# --- TAKE THE ** AND * MARKERS OFF A PIECE OF TEXT ---
# --- a heading is already bold, so when a bold paragraph becomes a heading the ** would just show up as typed characters ---
# --- a lone * with spaces around it (like 5 * 3 * 2) isn't emphasis, so it stays ---

def strip_emphasis(text):
    text = text.replace("**", "")
    text = re.sub(r"\*(\S(?:[^*]*\S)?)\*", r"\1", text)     # *italic* with no spaces hugging the stars
    return " ".join(text.split())                           # tidy any leftover double spaces
    
def change_box_type(box, type_name):
    lines = get_box_lines(box)
    one_piece = " ".join(line.strip() for line in lines)
    if type_name == "paragraph":
        new_box = make_paragraph(one_piece)
    elif type_name == "ul" or type_name == "ol":
        new_box = {"kind": "list", "ordered": type_name == "ol", "items": lines}
    elif type_name == "video":
        if find_video(one_piece) is None:
            new_box = make_paragraph(one_piece)              # the video address is gone, so all it can be is a paragraph
        else:
            new_box = {"kind": "video", "text": one_piece}
    elif type_name.startswith("h"):
        one_piece = strip_emphasis(one_piece)    # a heading is already bold; leftover markers would show up as typed characters
        lines = [one_piece]                      # so the Edit box shows the clean version too
        new_box = {"kind": "heading", "level": int(type_name[1]), "text": one_piece}
    else:
        return box
    new_box["lines"] = lines
    if box.get("dressing"):                  # a dressing piece stays a dressing piece when the box changes type
        new_box["dressing"] = box["dressing"]
    if box.get("video"):                     # a video box keeps its title, length and language when the type changes
        new_box["video"] = box["video"]
    return keep_valid_dressing(new_box)

# --- WHICH TYPES CAN THIS BOX BE? EVERYTHING, EXCEPT "VIDEO" WHEN THERE'S NO VIDEO ADDRESS IN ITS WORDS ---

def type_choices(box):

    one_piece = " ".join(line.strip() for line in get_box_lines(box))
    has_video = find_video(one_piece) is not None
    return [(name, label) for name, label in BOX_TYPE_CHOICES if name != "video" or has_video]

# --- THE INSTRUCTOR PICKED A CALLOUT (OR "NO CALLOUT"): RETURN A COPY OF THE BOX WITH THAT CALLOUT ---
# --- an empty name means no callout; the box's own words and type are untouched ---

def set_box_callout(box, callout_name):

    new_box = dict(box)                     # a copy, so the old box is left alone
    new_box["dressing"] = callout_name
    return new_box

# --- WHICH DRESSINGS CAN THIS BOX WEAR? HEADINGS: NONE, ACCORDION TITLE, ACCORDION CONTENT; EVERYTHING ELSE: NONE, THE CALLOUTS, ACCORDION CONTENT ---

def dressing_choices(box):

    choices = [("", "None")]
    if box["kind"] == "heading":
        choices.append(("accordion-title", "Accordion Title"))
    else:
        for name, label, icon_class in CALLOUT_CHOICES:
            choices.append((name, label))
    choices.append(("accordion-content", "Accordion Content"))
    return choices

def keep_valid_dressing(box):

    valid_names = [name for name, label in dressing_choices(box)]
    if box.get("dressing", "") not in valid_names:
        return set_box_callout(box, "")
    return box

# --- ACCORDIONS: A STRETCH OF CONSECUTIVE ACCORDION-MARKED BOXES BECOMES ONE ACCORDION ---
# --- a title opens a panel; the content boxes after it fill the panel; a stretch that doesn't follow that pattern stays plain ---

def is_accordion_piece(box):
    return box.get("dressing", "") in ("accordion-title", "accordion-content")

def find_accordion_runs(boxes):

    runs = []                                # each run is (first index, index after the last)
    start = None
    for index, box in enumerate(boxes):
        if is_accordion_piece(box):
            if start is None:
                start = index                # a new stretch begins here
        elif start is not None:
            runs.append((start, index))      # a plain box ends the stretch
            start = None
    if start is not None:
        runs.append((start, len(boxes)))     # the stretch ran to the end of the page
    return runs

def accordion_run_is_valid(run_boxes):

    if run_boxes[0].get("dressing") != "accordion-title":
        return False                         # content with no title above it
    for index, box in enumerate(run_boxes):
        if box.get("dressing") == "accordion-title":
            if index + 1 >= len(run_boxes):
                return False                 # a title at the very end has no content
            if run_boxes[index + 1].get("dressing") == "accordion-title":
                return False                 # a title right before another title has no content
    return True

def clean_accordion_title(text):

    text = text.replace("&nbsp;", " ")       # no-break spaces are just clutter in a title
    return " ".join(text.split())            # split() also treats the real no-break character as a space

def make_accordion_html(run_boxes):

    cards = []
    index = 0
    while index < len(run_boxes):
        title_box = run_boxes[index]
        index += 1
        pieces = []
        while index < len(run_boxes) and run_boxes[index].get("dressing") == "accordion-content":
            pieces.append(box_to_plain_html(run_boxes[index]))
            index += 1
        tag = "h" + str(title_box["level"])  # the title keeps the heading level the instructor chose
        title = escape(clean_accordion_title(title_box["text"]), quote=False)
        inner = "\n".join(pieces)
        cards.append(
            '<div class="card">\n'
            '<div class="card-header">\n'
            f'<{tag} class="card-title text-left">{title}</{tag}>\n'
            '</div>\n'
            '<div class="collapse">\n'
            '<div class="card-body">\n'
            f'{inner}\n'
            '</div>\n'
            '</div>\n'
            '</div>'
        )
    all_cards = "\n".join(cards)
    return (
        '<!-- accordion begin -->\n'
        '<div class="container-fluid mb-3">\n'
        '<div class="accordion">\n'
        f'{all_cards}\n'
        '</div>\n'
        '</div>\n'
        '<!-- accordion end -->'
    )

# --- THE INSTRUCTOR JUST MARKED A TITLE: IF THE BOX UNDER IT IS UNDRESSED, MAKE IT THE ACCORDION CONTENT ---
# --- (a callout or an existing accordion mark is left alone; Needed Repairs speaks up if that causes trouble) ---

def mark_content_after_title(boxes, title_index):

    next_index = title_index + 1
    if next_index >= len(boxes):
        return False                                     # the title is the last box; nothing under it
    if boxes[next_index].get("dressing", "") != "":
        return False                                     # already dressed as something; not our call
    boxes[next_index] = set_box_callout(boxes[next_index], "accordion-content")
    return True

# --- VIDEOS: ONE PASTED YOUTUBE OR VIMEO ADDRESS GIVES US BOTH THE EMBED ADDRESS AND THE DIRECT LINK ---

VIDEO_DEFAULT_LANGUAGE = "English, with subtitles"

def is_video_id(text):

    return text != "" and all(character.isalnum() or character in "-_" for character in text)

def parse_video_url(url):

    parts = urlparse(url)
    host = (parts.hostname or "").lower()
    for prefix in ("www.", "m."):
        if host.startswith(prefix):
            host = host[len(prefix):]
    bits = [bit for bit in parts.path.split("/") if bit]
    query = {}
    for pair in parts.query.split("&"):
        if "=" in pair:
            name, value = pair.split("=", 1)
            query[name] = value

    video_id = ""
    if host == "youtu.be" and bits:
        video_id = bits[0]
    elif host in ("youtube.com", "youtube-nocookie.com"):
        if bits[:1] == ["watch"]:
            video_id = query.get("v", "")
        elif bits[:1] in (["embed"], ["shorts"], ["live"], ["v"]) and len(bits) > 1:
            video_id = bits[1]
    if is_video_id(video_id):
        return {"embed": f"https://www.youtube.com/embed/{video_id}", "direct": f"https://youtu.be/{video_id}"}

    raw_host = (parts.hostname or "").lower()
    if raw_host.endswith(".panopto.com") and parts.path.lower().endswith(("/panopto/pages/viewer.aspx", "/panopto/pages/embed.aspx")):
        if is_video_id(query.get("id", "")):    # every school has its own Panopto address, so we go by the shape, not the name
            return {"embed": f"https://{raw_host}/Panopto/Pages/Embed.aspx?id={query['id']}&v=1",
                    "direct": f"https://{raw_host}/Panopto/Pages/Viewer.aspx?id={query['id']}"}
        return None
        
    if host == "vimeo.com" and bits and bits[0].isdigit():
        video_id = bits[0]
        secret = bits[1] if len(bits) > 1 and is_video_id(bits[1]) else ""     # unlisted videos carry a secret code
    elif host == "player.vimeo.com" and len(bits) > 1 and bits[0] == "video" and bits[1].isdigit():
        video_id = bits[1]
        secret = query.get("h", "") if is_video_id(query.get("h", "")) else ""
    else:
        return None
    embed = f"https://player.vimeo.com/video/{video_id}" + (f"?h={secret}" if secret else "")
    direct = f"https://vimeo.com/{video_id}" + (f"/{secret}" if secret else "")
    return {"embed": embed, "direct": direct}

def find_video(text):

    for link_text, url in find_links(text):     # a pasted address has already become a markdown link
        info = parse_video_url(url)
        if info is not None:
            return info                         # the first video address in the box wins
    return None

def make_video_html(info, title, length, language, number):

    title = title.strip()
    iframe_title = escape(title if title else "Video", quote=True)
    link_text = escape(title if title else "Watch this video", quote=False)
    details = []
    if length.strip():
        details.append(f"Length: {escape(length.strip(), quote=False)}")
    details.append(f"Language: {escape(language.strip() if language.strip() else VIDEO_DEFAULT_LANGUAGE, quote=False)}")
    details_line = " | ".join(details)
    return (
        '<div class="video-wrapper">\n'
        f'<div class="embed-responsive embed-responsive-16by9"><iframe class="embed-responsive-item" src="{escape(info["embed"])}" title="{iframe_title}" allowfullscreen="allowfullscreen"></iframe></div>\n'
        '<div class="video-text">\n'
        f'<p class="text-center">Direct Link: <a href="{escape(info["direct"])}" class="new-window" target="_blank" id="new-window{number}" '
        'data-original-title="opens in new window/tab" data-toggle="tooltip" rel="noopener">'
        f'{link_text}<span class="sr-only">(this link opens in a new window/tab)</span></a><br>\n'
        f'{details_line}</p>\n'
        '</div>\n'
        '</div>\n'
    )

# --- WHERE COULD WE ASK FOR THIS VIDEO'S TITLE? (YOUTUBE AND VIMEO ANSWER THAT; PANOPTO DOESN'T) ---

def video_title_lookup_url(info):

    direct = info["direct"]
    if direct.startswith("https://youtu.be/"):
        return "https://www.youtube.com/oembed?url=" + direct + "&format=json"
    if direct.startswith("https://vimeo.com/"):
        return "https://vimeo.com/api/oembed.json?url=" + direct
    return None

# --- "3:29" OR "1:02:03" BECOMES A NUMBER OF SECONDS; ANYTHING ELSE COMES BACK AS None ---

def length_to_seconds(text):

    pieces = text.strip().split(":")
    if len(pieces) not in (2, 3) or not all(piece.isdigit() for piece in pieces):
        return None
    numbers = [int(piece) for piece in pieces]
    if any(number >= 60 for number in numbers[1:]):        # minutes after hours and seconds after minutes stop at 59
        return None
    seconds = 0
    for number in numbers:
        seconds = seconds * 60 + number
    return seconds

# --- ADD UP EVERY VIDEO'S TYPED LENGTH AND ROUND UP TO WHOLE MINUTES (0 IF THERE'S NOTHING TO ADD) ---

def calculate_video_minutes(boxes):

    total_seconds = 0
    for box in boxes:
        if box["kind"] == "video":
            seconds = length_to_seconds(get_video_fields(box)["length"])
            if seconds is not None:
                total_seconds += seconds
    return math.ceil(total_seconds / 60)

# --- A VIDEO BOX REMEMBERS ITS TITLE, LENGTH AND LANGUAGE IN box["video"]; UNTOUCHED FIELDS HAVE DEFAULTS ---

def get_video_fields(box):

    saved = box.get("video", {})
    return {"title": saved.get("title", ""), "length": saved.get("length", ""), "language": saved.get("language", VIDEO_DEFAULT_LANGUAGE)}

def set_box_video(box, title, length, language):

    new_box = dict(box)                     # a copy, so the old box is untouched
    new_box["video"] = {"title": title, "length": length, "language": language}
    return new_box

# --- EVERY VIDEO LINK ON A PAGE NEEDS ITS OWN ID: SWAP THE "#" PLACEHOLDERS FOR 0, 1, 2... IN PAGE ORDER ---

def number_video_links(html):

    count = 0
    while 'id="new-window#"' in html:
        html = html.replace('id="new-window#"', f'id="new-window{count}"', 1)
        count += 1
    return html

# --- ALL THE BOXES AS ONE LONG STRING OF HTML (NO TIME CARD YET) --------------------------------------------------------
# --- the web page and the command line both start from here ---

def boxes_to_content(boxes):

    run_ends = {}                           # where each accordion stretch starts -> where it ends
    for start, end in find_accordion_runs(boxes):
        if accordion_run_is_valid(boxes[start:end]):
            run_ends[start] = end            # only stretches that follow the pattern become accordions

    pieces = []
    index = 0
    while index < len(boxes):
        if index in run_ends:
            pieces.append(make_accordion_html(boxes[index:run_ends[index]]))
            index = run_ends[index]          # hop past all the boxes the accordion used
        else:
            pieces.append(box_to_html(boxes[index]))
            index += 1
    return number_video_links("\n".join(pieces))    # newlines cuz humans have to check it; then give each video link its own id
    
# --- THE PREVIEW: THE CONTENT WITH THE TIME CARD DROPPED IN RIGHT AFTER THE H1, SAME AS THE REAL PAGE ---
# --- no template here; the template's styles only exist inside Brightspace, so this is a simulation ---

def make_preview_html(boxes, details=None):

    content = boxes_to_content(boxes) + "\n" + make_page_end(details)
    page_leader = make_page_leader(calculate_time_on_task(boxes), details)
    return content.replace("</h1>", "</h1>\n" + page_leader, 1)

# --- THE REAL THING: THE WHOLE FINISHED PAGE, READY TO SAVE AS A FILE ---

def make_finished_page(template, boxes, details=None):

    content = boxes_to_content(boxes) + "\n" + make_page_end(details)
    page_leader = make_page_leader(calculate_time_on_task(boxes), details)
    return build_page(template, boxes, content, page_leader, details)

# --- WHAT TO CALL THE DOWNLOADED FILE: THE PAGE TITLE, LOWERCASE, WITH HYPHENS ---
# --- "The Beginner's Guide (Test)" becomes the-beginners-guide-test.html ---

def make_file_name(boxes, details=None):

    details = details or {}                 # the command-line run passes nothing
    title = "page"                          # in case there's no H1
    for box in boxes:
        if box["kind"] == "heading" and box["level"] == 1:
            title = box["text"]
            break

    name = ""
    for character in title.lower():
        if character == "'":                # apostrophes just disappear: beginners, not beginner-s
            continue
        if character.isalnum():
            name += character
        elif name != "" and not name.endswith("-"):
            name += "-"                     # anything else becomes one hyphen, never two in a row
    name = name.strip("-")
    if name == "":
        name = "page"

    prefix = ""                             # Week 11 becomes W11-, Module 2 becomes M02-; no number, no prefix
    unit_number = one_line(details.get("unit_number", ""))
    if unit_number.isdigit() and int(unit_number) > 0:
        letter = {"Week": "W", "Unit": "U", "Module": "M"}.get(one_line(details.get("unit_type", "")), "W")   # same fallback as the Week line at the bottom of the page
        prefix = f"{letter}{int(unit_number):02d}-"
    return prefix + name + ".html"
    
# --- WHAT THE EDITING TEXT BOX SHOULD SHOW FOR A BOX -------------------------------------------------------------------
# --- one line per line of the box; list items get a "- " in front, numbered or not (the dropdown decides numbered, and the page counts) ---

def box_to_editor_text(box):

    lines = get_box_lines(box)
    if box_type_name(box) == "ul" or box_type_name(box) == "ol":
        lines = ["- " + line for line in lines]
    return "\n".join(lines)

# --- DOES THIS LINE START A NEW LIST ITEM? RETURN (YES/NO, THE LINE WITHOUT ITS MARKER) -------------------------------
# --- we're generous about what we accept ("- ", "* ", "1. ") and strict about what we hand back ---

def strip_list_marker(line):

    if line.startswith("- ") or line.startswith("* "):
        return True, line[2:].strip()
    number, dot, rest = line.partition(". ")
    if dot and number.isdigit():            # somebody typed 1. out of habit; fine, the page numbers things itself
        return True, rest.strip()
    return False, line

# --- A LIST'S LINES COME BACK AS ITEMS: A MARKER STARTS A NEW ITEM, A LINE WITHOUT ONE GLUES ONTO THE ONE ABOVE --------
# --- same rule the pasted text follows in chunk_to_list ---

def lines_to_items(lines):

    items = []
    for line in lines:
        if line == "-" or line == "*":      # a marker with nothing after it is an empty item; skip it
            continue
        is_new_item, text = strip_list_marker(line)
        if is_new_item or not items:
            items.append(text)
        else:
            items[-1] = items[-1] + " " + text
    return items

# --- THE INSTRUCTOR EDITED A BOX'S WORDS: RETURN A NEW BOX OF THE SAME TYPE WITH THE NEW WORDS --------------------------
# --- same cleanup the pasted text got, then blank lines vanish; one box stays one box ---
# --- if they erased everything, hand back the box we were given (an empty box would break things) ---

def edit_box_text(box, new_text):

    new_text = structure_bare_urls(clean_text(new_text))    # curly quotes and bare urls get the same treatment as pasted text
    lines = [line.strip() for line in new_text.splitlines() if line.strip() != ""]
    type_name = box_type_name(box)
    if type_name == "ul" or type_name == "ol":
        lines = lines_to_items(lines)       # markers only mean something inside a list
    if not lines:
        return box
    old_pieces = {"lines": lines, "dressing": box.get("dressing", "")}
    if box.get("video"):
        old_pieces["video"] = box["video"]                  # editing the words must not lose the video details
    return change_box_type(old_pieces, type_name)

# --- FIND EVERY [TEXT](URL) IN A PIECE OF TEXT: RETURN A LIST OF (TEXT, URL) PAIRS ----------------------------------
# --- same hunt as format_inline, but on raw text, and it only reports; it doesn't change anything ---

def find_links(text):

    links = []
    rest = text
    while True:
        url_seam_position = rest.find("](http")
        if url_seam_position == -1:
            break
        open_bracket_position = rest.rfind("[", 0, url_seam_position)
        close_paren_position = rest.find(")", url_seam_position)
        if open_bracket_position == -1 or close_paren_position == -1:
            rest = rest[url_seam_position + 2:]     # not a link; keep looking past it
            continue
        link_text = rest[open_bracket_position + 1:url_seam_position]
        url = rest[url_seam_position + 2:close_paren_position]
        links.append((link_text, url))
        rest = rest[close_paren_position + 1:]
    return links

# --- WALK THE BOXES AND LIST EVERYTHING AN INSTRUCTOR SHOULD FIX ------------------------------------------------------
# --- returns a list of plain sentences, each starting with the box number so the instructor can find it ---
# --- right now there's one kind of problem; this is where the other kinds will go ---
# --- (headings are skipped on purpose: format_inline doesn't make links inside headings yet) ---

def find_issues(boxes):

    issues = []                                     # pairs of (box number, sentence) so we can sort them at the end
    for number, box in enumerate(boxes, start=1):   # people count from 1, not 0
        if box["kind"] == "video":                  # videos need a title and a length; their links are handled elsewhere
            fields = get_video_fields(box)
            length = fields["length"].strip()
            if fields["title"].strip() == "":
                issues.append((number, f"Box {number}: video needs a title (it names the video for screen readers and is the link text)."))
            if length == "":
                issues.append((number, f"Box {number}: video needs a length, like 3:29."))
            elif length_to_seconds(length) is None:
                issues.append((number, f"Box {number}: video length ({length}) should look like 3:29 (minutes:seconds)."))
            continue
        if box["kind"] == "paragraph":
            texts = [box["text"]]
        elif box["kind"] == "list":
            texts = box["items"]
        else:
            continue

        for text in texts:
            for link_text, url in find_links(text):
                if link_text_is_weak(link_text, url):
                    issues.append((number, f"Box {number}: link ({url}) is missing descriptive text."))

    for start, end in find_accordion_runs(boxes):   # accordions: every title needs content, every content needs a title
        for index in range(start, end):
            number = index + 1
            dressing = boxes[index].get("dressing", "")
            if dressing == "accordion-content" and index == start:
                issues.append((number, f"Box {number}: accordion content has no accordion title above it. "
                                       "Mark a heading above it as Accordion title, or set this box back to None."))
            if dressing == "accordion-title":
                if index + 1 < end and boxes[index + 1].get("dressing") == "accordion-title":
                    issues.append((number, f"Box {number}: accordion title has no content before the next title. "
                                           "Mark a box under it as Accordion content."))
                elif index + 1 == end:
                    next_dressing = boxes[end].get("dressing", "") if end < len(boxes) else ""
                    if next_dressing != "":
                        issues.append((number, f"Box {number}: accordion title is followed by a callout, which can't be accordion content. "
                                               "Move the callout, or set it back to None."))
                    else:
                        issues.append((number, f"Box {number}: accordion title has no content under it. "
                                               "Mark the box below it as Accordion content, or set this one back to None."))

    issues.sort(key=lambda pair: pair[0])           # sort() keeps ties in the order we added them
    return [sentence for number, sentence in issues]

# --- A PARAGRAPH THAT IS NOTHING BUT ONE VIDEO LINK STARTS OUT AS A VIDEO BOX ---
# --- if the link already has real words ([Intro to Excel](https://youtu.be/...)), those words become the starting title ---

def is_lone_video_link(text):

    links = find_links(text)
    if len(links) != 1:
        return False
    link_text, url = links[0]
    return text.strip() == f"[{link_text}]({url})" and parse_video_url(url) is not None

def make_lone_video_box(text):

    box = {"kind": "video", "text": text}
    link_text, url = find_links(text)[0]
    if link_text.strip() != "" and not link_text_is_weak(link_text, url):
        box["video"] = {"title": link_text.strip(), "length": "", "language": VIDEO_DEFAULT_LANGUAGE}
    return box

# --- PHASE ONE AS ONE CALL: RAW MARKDOWN IN, LIST OF BOXES OUT -------------------------------------------------------
# --- cleans the text, fixes bare urls, splits it into chunks, and puts each chunk in a labeled box ---
# --- main logic and the web page both call this, so the sorting rules live in exactly one place ---

def text_to_boxes(markdown_text):

    markdown_text = clean_text(markdown_text)           # remove any wonky characters
    markdown_text = structure_bare_urls(markdown_text)  # make sure bare URLs are properly formatted
    chunks = split_into_chunks(markdown_text)           # split markdown into chunks of text

    boxes = []                                          # initialize this puppy
    for chunk in chunks:
        if chunk.startswith("#"):                       # things with hashtags in col 1 are usually headers
            box = chunk_to_header(chunk)
        elif chunk.startswith("- ") or chunk.startswith("* "):   # hey look, a bullet list!
            box = chunk_to_list(chunk)
        elif chunk.startswith("1. "):                   # ooooh, a numbered list... we be callin the same function
            box = chunk_to_list(chunk)
        else:
            box = make_paragraph(chunk)                 # everything else is a damn paragraph
            if is_lone_video_link(chunk):               # unless it's nothing but a video link, which is almost certainly meant as a video
                box = make_lone_video_box(chunk)

        boxes.append(box)                               # whatever kind of box we just made, add it to the output list

    return boxes

# === MAIN LOGIC STARTS HERE ==========================================================================================
# --- everything below only runs when you run this file directly (python md2bsp.py) ---
# --- when the web page imports this file, it only gets the functions above and skips all of this ---

if __name__ == "__main__":

    # --- Hello, world! ---
    print("Welcome to the Markdown to Brightspace Conversion Tool!")
    print()

    brightspace_wrapper = read_file(TEMPLATE_FILE)
    markdown_content = read_file(INPUT_FILE)

    # --- Sanity check: did both files load? ---
    print(f"Template {TEMPLATE_FILE} loaded: ({len(brightspace_wrapper)} characters)")
    print(f"Content file {INPUT_FILE} loaded: ({len(markdown_content)} characters)")
    print()

    # --- Phase One: clean the text, split it into chunks, put each chunk in a labeled box ---
    boxes = text_to_boxes(markdown_content)

    print("Made", len(boxes), "boxes")          # --- Sanity check: how many boxes did we make? ---
    if TESTING:
        for box in boxes:
            print(box)
            print()

    # --- Phase Two: process boxes of content into proper HTML ---

    html_pieces = []                            # sing it with me: ih-nih-shul-eyes!
    for box in boxes:
        html_pieces.append(box_to_html(box))

    page_content = "\n".join(html_pieces)       # newlines cuz humans have to check it

    if TESTING:
        print(page_content)

    # --- Phase Three: put the content in the standard Brightspace template and ship it ---

    minutes = calculate_time_on_task(boxes)     # calculate time on task
    page_leader = make_page_leader(minutes)     # setup the first of the top of page headers

    finished_page = build_page(brightspace_wrapper, boxes, page_content, page_leader)
    write_file(OUTPUT_FILE, finished_page)

    print(f"Saved {OUTPUT_FILE}")               # --- Sanity check: did we make it? ---
