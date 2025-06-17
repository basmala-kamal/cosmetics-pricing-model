import json
import nbformat
import glob
import shutil
import os

def render(template_file, output_file, keyword):
    candidates = sorted(glob.glob(f"*{keyword}*.json"), reverse=True)
    json_filename = None
    for f in candidates:
        if os.path.getsize(f) > 30:  # skip empty or invalid files
            json_filename = f
            break
    if not json_filename:
        print(f"No usable JSON files found for {keyword}")
        return

    nb = nbformat.read(template_file, as_version=4)

    for cell in nb.cells:
        if 'with open(' in cell.source:
            cell.source = cell.source.replace("with open(\"B:", f"with open(\"{json_filename}")

    nbformat.write(nb, output_file)
    print(f"{output_file} created.")

render("sourcebeauty_makeupbrands_clustering.ipynb", "notebook_noon.ipynb", "noon")
render("sourcebeauty_makeupbrands_clustering.ipynb", "notebook_amazon.ipynb", "amazon")
