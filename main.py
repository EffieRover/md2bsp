from pyscript import document, when
from md2bsp_web import text_to_boxes            # the engine lives in its own file now

document.getElementById("status").innerText = "Python is ready."
document.getElementById("go-button").disabled = False   # Python is ready, so turn the button on

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
    document.getElementById("step-paste").removeAttribute("aria-current")           # move the white pill in the nav bar
    document.getElementById("step-organize").setAttribute("aria-current", "step")
    document.getElementById("boxes").focus()    # the button that had focus just vanished, so hand focus to the new screen

# --- and back to the "1: Paste" look ---
def show_paste_screen():
    set_hidden("paste-screen", False)
    set_hidden("boxes", True)
    set_hidden("go-button", False)
    set_hidden("clear-button", False)
    set_hidden("back-button", True)
    set_hidden("help-paste", False)
    set_hidden("help-organize", True)
    document.getElementById("step-organize").removeAttribute("aria-current")
    document.getElementById("step-paste").setAttribute("aria-current", "step")
    document.getElementById("markdown-input").focus()

# --- how to show one box on screen: returns (label, text) ---
def describe_box(box):

    kind = box["kind"]

    if kind == "heading":
        return f'Heading {box["level"]}', box["text"]

    if kind == "list":
        lines = []
        if box["ordered"]:
            label = "Numbered list"
            for number, item in enumerate(box["items"], start=1):
                lines.append(f"{number}. {item}")
        else:
            label = "Bulleted list"
            for item in box["items"]:
                lines.append(f"- {item}")
        return label, "\n".join(lines)

    return "Paragraph", box["text"]             # everything else is a paragraph

@when("click", "#go-button")
def chunk_it(event):
    text = document.getElementById("markdown-input").value   # whatever was pasted
    boxes = text_to_boxes(text)                              # the engine does the real work

    if len(boxes) == 0:                                      # nothing pasted, nothing to chunk
        document.getElementById("result").innerText = "Nothing to chunk yet. Paste some text first."
        return

    container = document.getElementById("boxes")
    container.innerHTML = ""                                 # wipe any old boxes first

    for number, box in enumerate(boxes, start=1):
        label, shown_text = describe_box(box)

        card = document.createElement("section")             # one card per box
        card.className = "card"

        title = document.createElement("h2")
        title.innerText = f"Box {number}: {label}"

        body = document.createElement("p")
        body.className = "box-text"
        body.innerText = shown_text

        card.appendChild(title)
        card.appendChild(body)
        container.appendChild(card)

    document.getElementById("result").innerText = f"Found {len(boxes)} boxes."
    show_organize_screen()

@when("click", "#back-button")
def go_back(event):
    document.getElementById("result").innerText = ""
    show_paste_screen()
