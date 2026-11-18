from pyscript import document, when

document.getElementById("status").innerText = "Python is alive (v2)."

@when("click", "#go-button")
def chunk_it(event):
    text = document.getElementById("markdown-input").value   # whatever was pasted
    lines = text.splitlines()                                # break it into lines
    document.getElementById("result").innerText = f"Got {len(text)} characters on {len(lines)} lines."
