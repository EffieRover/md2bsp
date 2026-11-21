import asyncio
from pyodide.http import pyfetch
from pyscript import document, when, window
from md2bsp_web import (
    BOX_TYPE_CHOICES,
    CALLOUT_CHOICES,
    TEMPLATE_FILE,
    BANNER_CHOICES,
    DEFAULT_BANNER_FILE,
    banner_preview_url,
    text_to_boxes,
    html_to_markdown,
    html_has_structure,
    box_to_html,
    box_type_name,
    change_box_type,
    box_to_editor_text,
    edit_box_text,
    set_box_callout,
    dressing_choices,
    find_issues,
    mark_content_after_title,
    type_choices,
    get_video_fields,
    set_box_video,
    find_video,
    video_title_lookup_url,
    calculate_video_minutes,
    make_preview_html,
    make_finished_page,
    make_file_name,
    read_file,
)

document.getElementById("status").innerText = "Python is ready."
document.getElementById("go-button").disabled = False   # Python is ready, so turn the button on

state = {"boxes": [], "screen": "paste"}        # the boxes we're working on; the dropdowns change these
TYPE_LABELS = dict(BOX_TYPE_CHOICES)            # "h2" -> "Heading 2", so we can say it out loud
CALLOUT_LABELS = {"": "No callout"}             # same idea for callouts: "tip" -> "Tip"
for value, label, icon_class in CALLOUT_CHOICES:
    CALLOUT_LABELS[value] = label
CALLOUT_LABELS["accordion-title"] = "Accordion title"
CALLOUT_LABELS["accordion-content"] = "Accordion content"

# --- shortcut: hide or show one thing on the page, found by its id ---
def set_hidden(element_id, is_hidden):
    document.getElementById(element_id).hidden = is_hidden

# --- the page-details fields: the name the engine uses -> the id of the box on the page ---
DETAIL_FIELDS = {
    "before": "detail-before",
    "materials": "detail-materials",
    "terms": "detail-terms",
    "questions": "detail-questions",
    "working": "detail-working",
    "external": "detail-external",
    "video": "detail-video",
    "activity": "detail-activity",
    "banner": "banner-choice",
    "unit_type": "detail-unit-type",
    "unit_number": "detail-unit-number",
}

# --- read whatever the instructor typed into those fields right now; an untouched field is just empty text ---
def read_details():
    details = {}
    for name, element_id in DETAIL_FIELDS.items():
        details[name] = document.getElementById(element_id).value
    return details

# --- THE BANNER PICKER: A LABELED DROPDOWN, BUILT HERE AND DROPPED INTO THE RIGHT-HAND COLUMN, JUST ABOVE NEEDED REPAIRS ---
# --- the choices come from BANNER_CHOICES in the engine; each group becomes a heading inside the dropdown ---
# --- it borrows the class of the Needed Repairs section (and its heading's class), so it looks like its neighbors ---
def make_banner_picker():
    issues = document.getElementById("issues")
    area = document.createElement("div")
    area.id = "banner-area"
    area.className = ("banner-area " + issues.className).strip()
    area.hidden = True                          # the preview screen shows it; every other screen hides it
    heading_model = issues.firstElementChild    # the "Needed repairs" heading; we copy its tag and class
    heading = document.createElement(heading_model.tagName)
    heading.className = heading_model.className
    heading.id = "banner-heading"
    heading.innerText = "Banner"
    picker = document.createElement("select")
    picker.id = "banner-choice"
    picker.setAttribute("aria-labelledby", "banner-heading")    # the visible heading names the dropdown for screen readers
    for group_label, banners in BANNER_CHOICES:
        group = document.createElement("optgroup")
        group.setAttribute("label", group_label)
        for file_name, description in banners:
            option = document.createElement("option")
            option.value = file_name
            option.innerText = description
            group.appendChild(option)
        picker.appendChild(group)
    picker.value = DEFAULT_BANNER_FILE          # start on the notebook and teapot, same as always
    area.appendChild(heading)
    area.appendChild(picker)
    issues.before(area)                         # right before Needed Repairs, so right after How this works

make_banner_picker()

# --- THE THREE SCREENS: WHAT EACH ONE SHOWS, WHICH STEP LIGHTS UP, WHERE FOCUS GOES, AND WHAT THE BACK BUTTON SAYS ---
# --- every piece of the page that comes and goes is listed once in ALL_PARTS; a screen only lists what it shows ---

ALL_PARTS = ["paste-screen", "boxes", "page-preview", "page-details",
             "go-button", "clear-button", "finish-button", "preview-button",
             "download-button", "back-button",
             "help-paste", "help-organize", "help-finish", "help-preview",
             "issues", "banner-area"]

STEP_IDS = ["step-paste", "step-organize", "step-finish", "step-preview"]

SCREENS = {
    "paste": {
        "show": ["paste-screen", "go-button", "clear-button", "help-paste"],
        "step": "step-paste", "focus": "markdown-input", "back": "",
    },
    "organize": {
        "show": ["boxes", "finish-button", "back-button", "help-organize", "issues"],
        "step": "step-organize", "focus": "boxes", "back": "Back to 1: Paste",
    },
    "finish": {
        "show": ["page-details", "preview-button", "back-button", "help-finish"],
        "step": "step-finish", "focus": "page-details", "back": "Back to 2: Organize",
    },
    "preview": {
        "show": ["banner-area", "page-preview", "download-button", "back-button", "help-preview", "issues"],
        "step": "step-preview", "focus": "page-preview", "back": "Back to 3: Finishing Touches",
    },
}

# --- page button lists ... where do they return to ---
BACK_TO = {"organize": "paste", "finish": "organize", "preview": "finish"}

# --- switch the page to one of the screens above ---
def show_screen(name):
    screen = SCREENS[name]
    for element_id in ALL_PARTS:                # hide everything, then show only what this screen wants
        set_hidden(element_id, element_id not in screen["show"])
    for step_id in STEP_IDS:                    # move the white pill in the nav bar
        document.getElementById(step_id).removeAttribute("aria-current")
    document.getElementById(screen["step"]).setAttribute("aria-current", "step")
    if screen["back"] != "":
        document.getElementById("back-button").innerText = screen["back"]
    state["screen"] = name                      # so the Back button knows where it is
    document.getElementById(screen["focus"]).focus()    # the button that had focus just vanished, so hand focus to the new screen
    window.scrollTo(0, 0)                       # focusing a tall element scrolls the page; put it back at the top

def make_video_fields(number, box):
    saved = get_video_fields(box)
    wrapper = document.createElement("div")
    wrapper.id = f"video-fields-{number}"
    wrapper.className = "video-fields"
    wrapper.hidden = box["kind"] != "video"      # no page lookups here; the box isn't on the page yet
    for name, label_text in [("title", "Video title"), ("length", "Length (mm:ss)"), ("language", "Language")]:
        piece = document.createElement("div")
        piece.className = f"video-field-{name}"
        label = document.createElement("label")
        label.setAttribute("for", f"video-{name}-{number}")
        label.innerText = label_text
        field = document.createElement("input")
        field.setAttribute("type", "text")
        field.id = f"video-{name}-{number}"
        field.className = "video-field"
        field.setAttribute("data-box", str(number))
        field.value = saved[name]
        piece.appendChild(label)
        piece.appendChild(field)
        wrapper.appendChild(piece)
    return wrapper

# --- show the fields only if this box is a video, and put the box's saved title, length and language in them ---
def fill_video_fields(number, box):
    fields = get_video_fields(box)
    document.getElementById(f"video-fields-{number}").hidden = box["kind"] != "video"
    for name in ("title", "length", "language"):
        document.getElementById(f"video-{name}-{number}").value = fields[name]

# --- fill a box's type dropdown with the types that box can be (Video only if it holds a video address) and pick the current one ---
def fill_type_picker(select, box):
    select.innerHTML = ""                       # empty out whatever was there
    for value, label in type_choices(box):
        option = document.createElement("option")
        option.value = value
        option.innerText = label
        select.appendChild(option)
    select.value = box_type_name(box)           # start on whatever the engine says this box is

# --- fill a box's dressing dropdown with the choices that box is allowed to have, and pick the one it has now ---
def fill_dressing_picker(select, box):
    select.innerHTML = ""                       # empty out whatever was there
    for value, label in dressing_choices(box):
        option = document.createElement("option")
        option.value = value
        option.innerText = label
        select.appendChild(option)
    select.value = box.get("dressing", "")
    
# --- build one framed box: a toolbar on top (number + type dropdown), the preview underneath ---
def make_box_frame(number, box):

    frame = document.createElement("section")
    frame.className = "box-frame"
    frame.setAttribute("role", "group")
    frame.setAttribute("aria-label", f"Box {number}")

    toolbar = document.createElement("div")     # the single row of controls, pushed to the right by the CSS
    toolbar.className = "box-toolbar"

    badge = document.createElement("span")      # just the number; the word "Box" is only for screen readers
    badge.className = "box-number"
    badge.innerHTML = f'<span class="visually-hidden">Box </span>{number}'

    picker = document.createElement("select")   # the type dropdown
    picker.setAttribute("aria-label", f"Type for box {number}")
    picker.setAttribute("data-box", str(number))
    fill_type_picker(picker, box)               # the choices this box can have, starting on its current type
    picker.id = f"type-{number}"                # ids so the edit code can find this box's pieces again
    
    callout_picker = document.createElement("select")   # the dressing dropdown: callouts and accordion pieces
    callout_picker.setAttribute("aria-label", f"Callout or accordion for box {number}")
    callout_picker.setAttribute("data-box", str(number))
    callout_picker.id = f"callout-{number}"             # keeps its old id so the rest of the code still finds it
    fill_dressing_picker(callout_picker, box)

    edit_button = document.createElement("button")   # one button that flips between Edit and Done
    edit_button.type = "button"                 # a plain button, not one that submits the form
    edit_button.id = f"edit-{number}"
    edit_button.className = "secondary edit-toggle"
    edit_button.setAttribute("data-box", str(number))
    edit_button.setAttribute("aria-label", f"Edit text of box {number}")
    edit_button.innerHTML = '<span class="fas fa-fw fa-pencil-alt" aria-hidden="true"></span>'
    edit_button.title = "Edit"                  # the tooltip for mouse users

    delete_button = document.createElement("button")   # throws the whole box away (Undo delete brings it back)
    delete_button.type = "button"
    delete_button.id = f"delete-{number}"
    delete_button.className = "secondary edit-toggle delete-box"   # edit-toggle is only here to borrow the pencil button's look; box_clicked checks delete-box first
    delete_button.setAttribute("data-box", str(number))
    delete_button.setAttribute("aria-label", f"Delete box {number}")
    delete_button.innerHTML = '<span class="fas fa-fw fa-trash-alt" aria-hidden="true"></span>'
    delete_button.title = "Delete"
    
    editor = document.createElement("textarea") # hidden until Edit is clicked; holds the box's raw words
    editor.id = f"editor-{number}"
    editor.className = "box-editor"
    editor.setAttribute("aria-label", f"Text of box {number}")
    editor.hidden = True
    
    hint = document.createElement("p")          # a one-line tip that only shows while a list box is being edited
    hint.id = f"hint-{number}"
    hint.className = "box-hint"
    hint.innerText = "Start each list item with a dash. Numbers are added for you."
    hint.hidden = True

    preview = document.createElement("div")     # the box's words, shown the way they'll look on the page
    preview.className = "preview"
    preview.id = f"preview-{number}"
    preview.innerHTML = box_to_html(box)

    toolbar.appendChild(badge)
    toolbar.appendChild(picker)
    toolbar.appendChild(callout_picker)
    toolbar.appendChild(edit_button)
    toolbar.appendChild(delete_button)
    frame.appendChild(toolbar)
    frame.appendChild(preview)
    frame.appendChild(make_video_fields(number, box))   # hidden unless this box is a video
    frame.appendChild(hint)
    frame.appendChild(editor)
    return frame

def render_issues(boxes):
    issues = find_issues(boxes)
    issue_list = document.getElementById("issues-list")
    issue_list.innerHTML = ""                   # empty out the old list first
    if not issues:
        item = document.createElement("li")
        item.innerText = "Nothing to fix."
        issue_list.appendChild(item)
    for sentence in issues:
        item = document.createElement("li")
        box_label, colon, rest = sentence.partition(": ")      # "Box 12" and everything after the first colon
        if colon == "":                                        # no "Box N:" in front; just show the sentence
            item.innerText = sentence
        else:
            label = document.createElement("strong")           # the box number, bold so each repair is easy to spot
            label.innerText = box_label + ":"
            item.appendChild(label)
            item.appendChild(document.createTextNode(" " + rest))    # a text node, so pasted urls stay plain text
        issue_list.appendChild(item)
    return len(issues)

# --- PASTE HOOK: IF THE CLIPBOARD CARRIES REAL FORMATTING, CONVERT IT TO MARKDOWN AS IT LANDS ---
# --- the browser fires "paste" before anything goes into the box; we peek at the HTML copy of the clipboard ---
# --- no real structure (or anything goes wrong)? we return without touching the event, and the normal paste happens ---

@when("paste", "#markdown-input")
def paste_arrived(event):

    html = event.clipboardData.getData("text/html")
    if not html or not html_has_structure(html):
        return                                          # plain text, or code-editor colors: leave it alone

    try:
        markdown, notes = html_to_markdown(html)
    except Exception as problem:
        document.getElementById("result").innerText = f"Couldn't read the pasted formatting ({problem}), so it was pasted as plain text."
        return

    if markdown.strip() == "":                          # nothing usable in there (say, only an image); plain paste takes over
        return

    event.preventDefault()                              # stop the browser pasting its own version
    box = document.getElementById("markdown-input")
    if not document.execCommand("insertText", False, markdown):     # this keeps Ctrl+Z working
        box.setRangeText(markdown, box.selectionStart, box.selectionEnd, "end")   # backup plan; undo won't work, but the text lands

    message = "Pasted with formatting converted to markdown: headings, lists, bold, italic and links kept."
    if notes:
        message += " " + " ".join(notes)
    document.getElementById("result").innerText = message

@when("click", "#go-button")
def chunk_it(event):
    text = document.getElementById("markdown-input").value   # whatever was pasted
    boxes = text_to_boxes(text)                              # the engine does the real work

    if len(boxes) == 0:                                      # nothing pasted, nothing to chunk
        document.getElementById("result").innerText = "Nothing to chunk yet. Paste some text first."
        return

    state["boxes"] = boxes                                   # remember them so the dropdowns can change them
    state["deleted"] = None                                  # a fresh chunking means nothing is waiting to be undone
    problems = render_issues(boxes)                          # do we have any issues with link text?

    container = document.getElementById("boxes")
    container.innerHTML = ""                                 # wipe any old boxes first

    for number, box in enumerate(boxes, start=1):
        container.appendChild(make_box_frame(number, box))
        if box["kind"] == "video" and get_video_fields(box)["title"] == "":   # videos found while chunking get their titles looked up too
            asyncio.ensure_future(fetch_video_title(number))

    document.getElementById("result").innerText = f"Found {len(boxes)} boxes. Things to fix: {problems}."
    show_screen("organize")

# --- ask the video site for the title (YouTube and Vimeo only); fill it in if the title box is still empty, say so if the lookup fails ---
async def fetch_video_title(number):
    box = state["boxes"][number - 1]
    info = find_video(box["text"])
    lookup_url = video_title_lookup_url(info) if info is not None else None
    if lookup_url is None:                                   # Panopto, or nothing to look up
        return
    try:
        response = await pyfetch(lookup_url)
        data = await response.json()
        title = data["title"]
    except Exception:                                        # blocked by the browser, no internet, video not found...
        document.getElementById("result").innerText = f"Box {number}: couldn't get the title from the video site. Please type it in."
        return
    try:
        box = state["boxes"][number - 1]                     # the box may have changed while we waited; look again
        if find_video(box["text"]) != info:                  # a different video is in this box now; this title isn't for it
            return
        fields = get_video_fields(box)
        if box["kind"] != "video" or fields["title"] != "":  # no longer a video, or the instructor already typed a title
            return
        new_box = set_box_video(box, title, fields["length"], fields["language"])
        state["boxes"][number - 1] = new_box
        fill_video_fields(number, new_box)
        document.getElementById(f"preview-{number}").innerHTML = box_to_html(new_box)
        render_issues(state["boxes"])
        document.getElementById("result").innerText = f"Box {number}: video title filled in. Check that it's right."
    except Exception as problem:                             # if anything goes wrong placing the title, say what
        document.getElementById("result").innerText = f"Box {number}: got the title but couldn't place it ({problem})."

# --- typing in a video field: save it into the box right away (the preview waits until you leave the field, so the video doesn't reload on every keystroke) ---
@when("input", "#boxes")
def video_field_typed(event):
    field = event.target
    if not field.classList.contains("video-field"):          # not one of ours
        return
    number = int(field.getAttribute("data-box"))
    state["boxes"][number - 1] = set_box_video(
        state["boxes"][number - 1],
        document.getElementById(f"video-title-{number}").value,
        document.getElementById(f"video-length-{number}").value,
        document.getElementById(f"video-language-{number}").value,
    )

# --- leaving a video field: redraw that box's preview and recheck Needed Repairs (type_changed hands "change" events here) ---
def video_field_changed(event):
    field = event.target
    if not field.classList.contains("video-field"):          # the editing box fires "change" too; not ours
        return
    number = int(field.getAttribute("data-box"))
    document.getElementById(f"preview-{number}").innerHTML = box_to_html(state["boxes"][number - 1])
    render_issues(state["boxes"])
    document.getElementById("result").innerText = f"Box {number} video details updated."

# --- the instructor changed a dropdown: relabel that box and redraw its preview ---
@when("change", "#boxes")
def type_changed(event):
    picker = event.target                                    # the dropdown that was just changed
    if picker.tagName != "SELECT":                           # not a dropdown: maybe a video field, maybe the editing box
        video_field_changed(event)
        return
    number = int(picker.getAttribute("data-box"))            # which box it belongs to
    callout_picker = document.getElementById(f"callout-{number}")

    if picker.id.startswith("callout-"):                     # the callout dropdown changed: dress the box up (or not)
        new_box = set_box_callout(state["boxes"][number - 1], picker.value)
        message = f"Box {number} callout: {CALLOUT_LABELS[picker.value]}."
    else:                                                    # the type dropdown changed: relabel the box
        new_box = change_box_type(state["boxes"][number - 1], picker.value)
        fill_dressing_picker(callout_picker, new_box)        # the new type may wear different things; refill the list
        message = f"Box {number} is now: {TYPE_LABELS[picker.value]}."

    state["boxes"][number - 1] = new_box                     # swap the old box for the new one
    fill_video_fields(number, new_box)                       # a box that just became a video (or stopped being one) shows or hides its fields
    if not picker.id.startswith("callout-") and picker.value == "video":      # the type dropdown just chose Video
        if get_video_fields(new_box)["title"] == "":
            asyncio.ensure_future(fetch_video_title(number))                  # runs in the background; the page keeps working
    if picker.id.startswith("callout-") and picker.value == "accordion-title":    # a title was just chosen
        if mark_content_after_title(state["boxes"], number - 1):                  # the box under it was undressed
            next_number = number + 1
            document.getElementById(f"callout-{next_number}").value = "accordion-content"   # show it in that box's dropdown
            message += f" Box {next_number} was marked as Accordion content."
    render_issues(state["boxes"])                            # a change can change what needs fixing
    document.getElementById(f"preview-{number}").innerHTML = box_to_html(new_box)
    document.getElementById("result").innerText = message

# --- flip one box between "looking at the preview" and "typing in the text box" ---
def set_editing_look(number, is_editing):
    document.getElementById(f"editor-{number}").hidden = not is_editing
    if not is_editing:
        document.getElementById(f"hint-{number}").hidden = True
    document.getElementById(f"preview-{number}").hidden = is_editing
    document.getElementById(f"type-{number}").disabled = is_editing     # no relabeling while typing
    document.getElementById(f"callout-{number}").disabled = is_editing  # and no callout changes while typing
    button = document.getElementById(f"edit-{number}")
    if is_editing:
        button.innerHTML = '<span class="fas fa-fw fa-check" aria-hidden="true"></span>'
        button.title = "Done"
        button.setAttribute("aria-label", f"Done editing box {number}")
    else:
        button.innerHTML = '<span class="fas fa-fw fa-pencil-alt" aria-hidden="true"></span>'
        button.title = "Edit"
        button.setAttribute("aria-label", f"Edit text of box {number}")

# --- Edit was clicked: show the box's words in a text box and put the cursor there ---
def start_editing(number):
    box = state["boxes"][number - 1]
    editor = document.getElementById(f"editor-{number}")
    editor.value = box_to_editor_text(box)
    is_list = box_type_name(box) == "ul" or box_type_name(box) == "ol"
    document.getElementById(f"hint-{number}").hidden = not is_list    # the tip only matters for lists
    if is_list:
        editor.setAttribute("aria-describedby", f"hint-{number}")     # screen readers hear the tip too
    else:
        editor.removeAttribute("aria-describedby")
    set_editing_look(number, True)
    editor.style.height = "auto"                             # then grow to fit the words
    editor.style.height = str(editor.scrollHeight + 4) + "px"
    editor.focus()

# --- Done was clicked: rebuild the box from what was typed and go back to the preview ---
def finish_editing(number):
    old_box = state["boxes"][number - 1]
    new_box = edit_box_text(old_box, document.getElementById(f"editor-{number}").value)
    state["boxes"][number - 1] = new_box
    fill_type_picker(document.getElementById(f"type-{number}"), new_box)          # the words may have gained or lost a video address
    fill_dressing_picker(document.getElementById(f"callout-{number}"), new_box)   # and the box may no longer wear what it wore
    fill_video_fields(number, new_box)
    document.getElementById(f"preview-{number}").innerHTML = box_to_html(new_box)
    set_editing_look(number, False)
    problems = render_issues(state["boxes"])                 # the fix might have cleared (or caused) a problem
    if new_box is old_box:
        message = f"Box {number} can't be empty, so it was left as it was."
    else:
        message = f"Box {number} updated."
    document.getElementById("result").innerText = f"{message} Things to fix: {problems}."
    document.getElementById(f"edit-{number}").focus()        # keep the keyboard where it was

# --- THE "UNDO DELETE" LINE: A SMALL BUTTON THAT SITS IN THE COLUMN WHERE THE DELETED BOX USED TO BE ---
def make_undo_line():
    line = document.createElement("div")
    line.className = "undo-line"
    button = document.createElement("button")
    button.type = "button"
    button.id = "undo-delete"
    button.className = "undo-delete"
    button.innerText = "Undo delete"
    line.appendChild(button)
    return line

# --- DRAW ALL THE BOXES FROM SCRATCH, NUMBERED 1, 2, 3 AGAIN, WITH THE UNDO LINE IN THE GAP IF A BOX WAS JUST DELETED ---
def render_boxes():
    container = document.getElementById("boxes")
    container.innerHTML = ""
    deleted = state.get("deleted")
    for number, box in enumerate(state["boxes"], start=1):
        if deleted and deleted["index"] == number - 1:
            container.appendChild(make_undo_line())
        container.appendChild(make_box_frame(number, box))
    if deleted and deleted["index"] >= len(state["boxes"]):      # the deleted box was the last one
        container.appendChild(make_undo_line())

# --- DELETE BOX NUMBER N: REMEMBER IT (ONE LEVEL ONLY), TAKE IT OUT, REDRAW ---
def delete_box(number):
    if len(state["boxes"]) == 1:
        document.getElementById("result").innerText = "That's the only box left, so it can't be deleted. Go back to step 1 to start over."
        return
    finish_all_editing()                                     # save anybody's half-finished typing before the boxes get redrawn
    box = state["boxes"].pop(number - 1)
    state["deleted"] = {"box": box, "index": number - 1}     # a second delete replaces this; only the latest can be undone
    render_boxes()
    problems = render_issues(state["boxes"])
    document.getElementById("result").innerText = f"Box {number} deleted. Things to fix: {problems}. Press Undo delete to bring it back."
    document.getElementById("undo-delete").focus()           # keyboard focus goes to the undo button, since the delete button just vanished

# --- BRING THE LAST DELETED BOX BACK TO WHERE IT WAS ---
def undo_delete():
    deleted = state.get("deleted")
    if not deleted:
        return
    state["boxes"].insert(deleted["index"], deleted["box"])
    state["deleted"] = None
    render_boxes()
    problems = render_issues(state["boxes"])
    number = deleted["index"] + 1
    document.getElementById("result").innerText = f"Box {number} is back. Things to fix: {problems}."
    document.getElementById(f"edit-{number}").focus()

@when("click", "#boxes")
def box_clicked(event):
    button = event.target
    keepers = ("edit-toggle", "delete-box", "undo-delete")  # the buttons whose clicks we care about
    if not any(button.classList.contains(name) for name in keepers):    # the click may have landed on the icon inside the button
        button = button.parentElement                        # so step up one level: an icon's parent is its button
        if not any(button.classList.contains(name) for name in keepers):   # still not one of our buttons; not our click
            return
    if button.classList.contains("undo-delete"):
        undo_delete()
        return
    number = int(button.getAttribute("data-box"))
    if button.classList.contains("delete-box"):              # checked before edit-toggle, because the delete button borrows that class for its look
        delete_box(number)
    elif document.getElementById(f"editor-{number}").hidden:
        start_editing(number)
    else:
        finish_editing(number)

# --- make sure nobody's half-finished edit gets left behind when the page moves on ---
def finish_all_editing():
    for number in range(1, len(state["boxes"]) + 1):
        if not document.getElementById(f"editor-{number}").hidden:
            finish_editing(number)

@when("click", "#finish-button")
def go_finish(event):
    finish_all_editing()
    render_issues(state["boxes"])
    automatic = calculate_video_minutes(state["boxes"])      # 0 when there are no videos, or no lengths typed yet
    automatic = str(automatic) if automatic > 0 else ""
    field = document.getElementById("detail-video")
    if field.value == "" or field.value == state.get("auto_video", ""):    # never overwrite a number the instructor typed themselves
        field.value = automatic
    state["auto_video"] = automatic
    show_screen("finish")
    
@when("click", "#preview-button")
def show_preview(event):
    finish_all_editing()                        # an open edit box counts as a finished one
    banner_url = banner_preview_url(read_details()["banner"])    # the real banner, loaded from the shared Brightspace folder
    banner = (f'<img id="preview-banner-img" class="preview-banner" src="{banner_url}" '
              'onerror="this.onerror=null; this.src=\'./preview_banner.jpg\'" alt="">')    # if that address ever fails, the mint stand-in takes over
    content = '<div class="preview-content">' + make_preview_html(state["boxes"], read_details()) + '</div>'    # the narrower column the template puts content in
    document.getElementById("page-preview").innerHTML = banner + content
    problems = find_issues(state["boxes"])
    document.getElementById("result").innerText = f"Preview ready. Things to fix: {len(problems)}."
    show_screen("preview")

# --- the instructor picked a different banner: swap the picture in the preview (the download reads the dropdown when it's clicked) ---
@when("change", "#banner-choice")
def banner_changed(event):
    picker = event.target
    document.getElementById("preview-banner-img").src = banner_preview_url(picker.value)
    description = picker.options.item(picker.selectedIndex).innerText
    document.getElementById("result").innerText = f"Banner: {description}."

@when("click", "#download-button")
def download_page(event):
    try:
        template = read_file(TEMPLATE_FILE)     # read_file stops the program if the file is missing; catch that one thing
    except SystemExit:
        document.getElementById("result").innerText = "Can't find the page template, so nothing was downloaded."
        return
    page = make_finished_page(template, state["boxes"], read_details())
    file_name = make_file_name(state["boxes"], read_details())
    
    link = document.createElement("a")          # a throwaway link that does the downloading, then disappears
    link.href = "data:text/html;charset=utf-8," + window.encodeURIComponent(page)
    link.download = file_name
    document.body.appendChild(link)
    link.click()
    link.remove()
    document.getElementById("result").innerText = f"Downloaded {file_name}."

@when("click", "#back-button")
def go_back(event):
    show_screen(BACK_TO[state["screen"]])
