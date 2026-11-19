from pyscript import document, when
from md2bsp_web import text_to_boxes            # the engine lives in its own file now

document.getElementById("status").innerText = "Python is ready."
document.getElementById("go-button").disabled = False   # Python is ready, so turn the button on

@when("click", "#go-button")
def chunk_it(event):
    text = document.getElementById("markdown-input").value   # whatever was pasted
    boxes = text_to_boxes(text)                              # the engine does the real work
    kinds = [box["kind"] for box in boxes]                   # just the labels, for now
    lines = text.splitlines()                                # break it into lines
    document.getElementById("result").innerText = f"Found {len(boxes)} boxes: " + ", ".join(kinds)
