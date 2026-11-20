"""
md2bsp_web.py -- Builds a finished Brightspace web page, given content pieces

WHAT IT DOES:
    Reads a file of markdown text, and converts that markdown into the appropriate HTML sequences to be included in Brightspace. 
    Then it wraps those sequences in the standard GCC template and Bob's your uncle. Note: it works on a multi-step process 
    because I want the instructor to be able to check some things and clean some things up before it goes out.
    Words I use: a CHUNK is a piece of the raw text (a heading, a paragraph, a list).
                 a BOX is a chunk after the program has decided what it is and labeled it.
    Phase 1: pull apart the input file into chunks and put each chunk in a labeled box
        Phase 1.1 (done, on the web page): the instructor can relabel boxes, fix typos and links, and dress a box up as a callout
        Phase 1.2 (done, on the web page): a Finishing Touches screen asks for reading length, materials needed, 
            key terms, guiding questions, and Week/Unit/Module
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

DONE:
    1. Web version (GitHub Pages + PyScript): paste, chunk, show the boxes, let the instructor relabel and edit them
    2. Finished page delivered as a download
    3. Before you start, materials needed, key terms, guiding questions, working toward, and time on task at the top of the page
    4. Week/Unit/Module and Last published at the bottom of the page
    5. Callouts: any box except a heading can be dressed up as a blue icon card

TODO:
    1. Recognize and format videos in an accessible (WCAG) manner
    2. Accordions, tabs, blockquotes (dressing up boxes the way callouts do)
    3. Accept uploaded markdown and Word files; convert pasted web content
    4. Start the suggestion engine ... suggest callouts, accordions, tabs
    5. A Best Practices review step: missing closings, skipped heading levels, image alt text
    6. Carry relabels and edits back when the instructor goes Back to step 1
    7. A generic template for people outside GCC

"""
# --- IMPORTS ---------------------------------------------------------------------------------------------------------

import os                                   # allows us to ask for device folders, for now
import sys                                  # allows us to stop the program with a message
from html import escape                     # make text safe to put inside HTML / sanitize it
import math                                 # cuz we be calculatin' reading time
from datetime import date                   # short date formats ...
from urllib.parse import urlparse           # chops a web address into its parts (host, path, etc)

# --- SETTINGS --------------------------------------------------------------------------------------------------------

TESTING = True                              # print ALL the things!!!! (or false to not)
TEMPLATE_FILE = "template_gcc.html"         # the Brightspace page wrapper
INPUT_FILE = "input.md"                     # the fixed input file, for now
OUTPUT_FILE = "output.html"                 # the fixed output file, for now
WORDS_PER_MINUTE = 200                      # average reading speed, used for time on task calculation

DEFAULT_PAGE_BANNER = "/shared/Course File Templates/GNC/pages/../_assets/img/banner_03.jpg"
                                            # ye olde ubiquitous notebook and teapot file

JUNK_TO_PLAIN = {                           # get rid of Microsoft "smart" bullshit
    "\u201c": '"',                          # curly open double quote
    "\u201d": '"',                          # curly close double quote
    "\u2018": "'",                          # curly open single quote
    "\u2019": "'",                          # curly close single quote, which is also the curly apostrophe
    "\u2026": "...",                        # the one-character ellipsis
    "\u2013": "-",                          # en dash, as in 10–15
    "\u2014": " - ",                        # em dash; spaces added so the words on either side don't mash together
    "\u00a0": " ",                          # non-breaking space, a classic Word landmine
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
]

# --- THE CALLOUT CHOICES: (the short name we use in code, the words the instructor sees, the Font Awesome icon) ---
# --- a box with no callout simply has no "callout" key, or an empty one ---

CALLOUT_CHOICES = [
    ("question", "Question", "fa-question-circle"),
    ("key", "Key idea", "fa-exclamation-circle"),
    ("tip", "Tip", "fa-lightbulb"),
    ("quote", "Quote", "fa-quote-left"),
    ("steps", "Steps", "fa-project-diagram"),
    ("plan", "Plan", "fa-map"),
    ("documents", "Documents", "fa-copy"),
    ("reminder", "Reminder", "fa-bell"),
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
    
# --- IT PUTS THE HTML IN THE TEMPLATE OR ELSE IT GETS THE WONKY FILE AGAIN -------------------------------------------
# --- takes the template text, boxes, content, works out the title, banner, leader ---
# --- note that some of this is hardcoded right now but will be added as options later ---

def build_page(template, boxes, content, page_leader):

    # --- find the page title. Will be the H1 tag on the page ---
    page_title = "Untitled Page"        # in case we don't find one
    for box in boxes:
        if box["kind"] == "heading" and box["level"] == 1:
            page_title = box["text"]
            break                       # okay, we found it, stop looking

    # --- the banner is fixed for now; we'll give options later ---
    banner = DEFAULT_PAGE_BANNER

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

def change_box_type(box, type_name):
    lines = get_box_lines(box)
    one_piece = " ".join(line.strip() for line in lines)
    if type_name == "paragraph":
        new_box = make_paragraph(one_piece)
    elif type_name == "ul" or type_name == "ol":
        new_box = {"kind": "list", "ordered": type_name == "ol", "items": lines}
    elif type_name.startswith("h"):
        new_box = {"kind": "heading", "level": int(type_name[1]), "text": one_piece}
    else:
        return box
    new_box["lines"] = lines
    if box.get("dressing"):                  # a dressing piece stays a dressing piece when the box changes type
        new_box["dressing"] = box["dressing"]
    return keep_valid_dressing(new_box)

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
        choices.append(("accordion-title", "Accordion title"))
    else:
        for name, label, icon_class in CALLOUT_CHOICES:
            choices.append((name, label))
    choices.append(("accordion-content", "Accordion content"))
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
        '<div class="container-fluid">\n'
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
    return "\n".join(pieces)               # newlines cuz humans have to check it

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
    return build_page(template, boxes, content, page_leader)

# --- WHAT TO CALL THE DOWNLOADED FILE: THE PAGE TITLE, LOWERCASE, WITH HYPHENS ---
# --- "The Beginner's Guide (Test)" becomes the-beginners-guide-test.html ---

def make_file_name(boxes):

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
    return name + ".html"
    
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
    return change_box_type({"lines": lines, "dressing": box.get("dressing", "")}, type_name)

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
