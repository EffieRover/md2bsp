from pyscript import document, when
from md2bsp_web import text_to_boxes            # the engine lives in its own file now

document.getElementById("status").innerText = "Python is ready."
document.getElementById("go-button").disabled = False   # Python is ready, so turn the button on

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

    return "Paragraph", box["text"]                          # everything else is a paragraph

@when("click", "#go-button")
def chunk_it(event):
    text = document.getElementById("markdown-input").value   # whatever was pasted
    boxes = text_to_boxes(text)                              # the engine does the real work

    container = document.getElementById("boxes")
    container.innerHTML = ""                                 # wipe any old boxes first

    for number, box in enumerate(boxes, start=1):            # these lines start creating text boxes for the organize step
    label, shown_text = describe_box(box)

    card = document.createElement("section")                 # one card per box
    card.className = "card"

    title = document.createElement("h2")                     # boxes are labeled with an h2
    title.innerText = f"Box {number}: {label}"

    body = document.createElement("p")                       # let's actually make them
    body.className = "box-text"
    body.innerText = shown_text

    card.appendChild(title)
    card.appendChild(body)
    container.appendChild(card)

    document.getElementById("result").innerText = f"Found {len(boxes)} boxes."

@when("click", "#clear-button")
def clear_boxes(event):
    document.getElementById("boxes").innerHTML = ""          # Clear also wipes the boxes
    document.getElementById("result").innerText = ""
