
from pathlib import Path


import tomobase
from tomobase.core.registers import image_types

tomobase.bootstrap(jupyter_enabled=True)

def qualified_name(obj):
    return f"{obj.__module__}.{obj.__name__}"


lines = [
    "# Process Registry",
    "",
    "Automatically generated from TOMOBASE_PROCESSES.",
    "",
]

for key, obj in image_types.items():

    lines.append(f"## {key}")
    lines.append("")

    # optional registry description
    if obj.__doc__:
        first_line = obj.__doc__.strip().splitlines()[0]
        lines.append(first_line)
        lines.append("")

    # mkdocstrings directive
    lines.append(f"::: {qualified_name(obj)}")
    lines.append("    handler: python")
    lines.append("    options:")
    lines.append("      show_root_heading: true")
    lines.append("")

Path("docs/generated/processes.md").write_text(
    "\n".join(lines),
    encoding="utf-8"
)

