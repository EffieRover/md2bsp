from pyscript import document, when, window
from md2bsp_web import text_to_boxes, box_to_html, box_type_name, change_box_type, BOX_TYPE_CHOICES, find_issues, box_to_editor_text, edit_box_text

document.getElementById("status").innerText = "Python is ready."
document.getElementById("go-button").disabled = False   # Python is ready, so turn the button on

state = {"boxes": []}                           # the boxes we're working on; the dropdowns change these
TYPE_LABELS = dict(BOX_TYPE_CHOICES)            # "h2" -> "Heading 2", so we can say it out loud

# --- shortcut: hide or show one thing on the page, found by its id ---
def set_hidden(element_id, is_hidden):
    document.getElementById(element_id).hidden = is_hidden

# --- switch the page to the "2: Organize" look ---
def show_organize_screen():
    set_hidden("paste-screen", True)            # the paste box goes away
    set_hidden("boxes", False)                  # the boxes appear
    set_hidden("go-button", True)               # Chunk it and Clear only make sense on the paste screen
    set_hidden("clear-button", True)
    set_hidden("back-button", False)
    set_hidden("help-paste", True)              # swap the instructions in the right-hand card
    set_hidden("help-organize", False)
    set_hidden("issues", False)                 # the "Things to fix" section shows up
    document.getElementById("step-paste").removeAttribute("aria-current")           # move the white pill in the nav bar
    document.getElementById("step-organize").setAttribute("aria-current", "step")
    document.getElementById("boxes").focus()    # the button that had focus just vanished, so hand focus to the new screen
    window.scrollTo(0,0)

# --- and back to the "1: Paste" look ---
def show_paste_screen():
    set_hidden("paste-screen", False)
    set_hidden("boxes", True)
    set_hidden("go-button", False)
    set_hidden("clear-button", False)
    set_hidden("back-button", True)
    set_hidden("help-paste", False)
    set_hidden("help-organize", True)
    set_hidden("issues", True)
    document.getElementById("step-organize").removeAttribute("aria-current")
    document.getElementById("step-paste").setAttribute("aria-current", "step")
    document.getElementById("markdown-input").focus()

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
    for value, label in BOX_TYPE_CHOICES:
        option = document.createElement("option")
        option.value = value
        option.innerText = label
        picker.appendChild(option)
    picker.value = box_type_name(box)           # start on whatever the engine decided this box is
    picker.id = f"type-{number}"                # ids so the edit code can find this box's pieces again

    edit_button = document.createElement("button")   # one button that flips between Edit and Done
    edit_button.type = "button"                 # a plain button, not one that submits the form
    edit_button.id = f"edit-{number}"
    edit_button.className = "secondary edit-toggle"
    edit_button.setAttribute("data-box", str(number))
    edit_button.setAttribute("aria-label", f"Edit text of box {number}")
    edit_button.innerHTML = '<span class="fas fa-fw fa-pencil-alt" aria-hidden="true"></span>'
    edit_button.title = "Edit"                  # the tooltip for mouse users

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
    toolbar.appendChild(edit_button)
    frame.appendChild(toolbar)
    frame.appendChild(preview)
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
        item.innerText = sentence               # innerText, because the url came from pasted text
        issue_list.appendChild(item)
    return len(issues)
    
@when("click", "#go-button")
def chunk_it(event):
    text = document.getElementById("markdown-input").value   # whatever was pasted
    boxes = text_to_boxes(text)                              # the engine does the real work

    if len(boxes) == 0:                                      # nothing pasted, nothing to chunk
        document.getElementById("result").innerText = "Nothing to chunk yet. Paste some text first."
        return

    state["boxes"] = boxes                                   # remember them so the dropdowns can change them
    problems = render_issues(boxes)                          # do we have any issues with link text?

    container = document.getElementById("boxes")
    container.innerHTML = ""                                 # wipe any old boxes first

    for number, box in enumerate(boxes, start=1):
        container.appendChild(make_box_frame(number, box))

    document.getElementById("result").innerText = f"Found {len(boxes)} boxes. Things to fix: {problems}."
    show_organize_screen()

# --- the instructor changed a dropdown: relabel that box and redraw its preview ---
@when("change", "#boxes")
def type_changed(event):
    picker = event.target                                    # the dropdown that was just changed
    if picker.tagName != "SELECT":                           # the editing box fires "change" too; that's not ours
        return
    number = int(picker.getAttribute("data-box"))            # which box it belongs to
    new_box = change_box_type(state["boxes"][number - 1], picker.value)
    state["boxes"][number - 1] = new_box                     # swap the old box for the relabeled one
    render_issues(state["boxes"])                            # a type change can change what needs fixing
    document.getElementById(f"preview-{number}").innerHTML = box_to_html(new_box)
    document.getElementById("result").innerText = f"Box {number} is now: {TYPE_LABELS[picker.value]}."

# --- flip one box between "looking at the preview" and "typing in the text box" ---
def set_editing_look(number, is_editing):
    document.getElementById(f"editor-{number}").hidden = not is_editing
    if not is_editing:
        document.getElementById(f"hint-{number}").hidden = True
    document.getElementById(f"preview-{number}").hidden = is_editing
    document.getElementById(f"type-{number}").disabled = is_editing     # no relabeling while typing
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
    document.getElementById(f"preview-{number}").innerHTML = box_to_html(new_box)
    set_editing_look(number, False)
    problems = render_issues(state["boxes"])                 # the fix might have cleared (or caused) a problem
    if new_box is old_box:
        message = f"Box {number} can't be empty, so it was left as it was."
    else:
        message = f"Box {number} updated."
    document.getElementById("result").innerText = f"{message} Things to fix: {problems}."
    document.getElementById(f"edit-{number}").focus()        # keep the keyboard where it was

@when("click", "#boxes")
def box_clicked(event):
    button = event.target
    if not button.classList.contains("edit-toggle"):         # the click may have landed on the icon inside the button
        button = button.parentElement                        # so step up one level: an icon's parent is its button
        if not button.classList.contains("edit-toggle"):     # still not an Edit / Done button; not our click
            return
    number = int(button.getAttribute("data-box"))
    if document.getElementById(f"editor-{number}").hidden:
        start_editing(number)
    else:
        finish_editing(number)

@when("click", "#back-button")
def go_back(event):
    document.getElementById("result").innerText = ""
    show_paste_screen()
