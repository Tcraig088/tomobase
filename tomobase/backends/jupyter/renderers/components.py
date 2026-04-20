from ipywidgets import VBox, HBox, Label, Accordion

def build_accordion(_dict, title=""):
    children = []
    for key, value in _dict.items():
        if isinstance(value, dict):
            children.append(build_accordion(value, key))
        else:
            children.append(HBox([Label(value=f"{key}:"), Label(value=f"{value}")]))
    vb = VBox(children)
    accordion = Accordion(children=[vb])
    accordion.set_title(0, title)

    return accordion