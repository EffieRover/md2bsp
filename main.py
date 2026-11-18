from pyscript import web, when

web.page["status"].innerText = "Python is alive."

@when("click", "#go-button")
def chunk_it(event):
    text = web.page["markdown-input"].value   # whatever the instructor pasted
    lines = text.splitlines()                 # break it into lines
    web.page["result"].innerText = f"Got {len(text)} characters on {len(lines)} lines."
