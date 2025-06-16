import json
import nbformat
import glob
import shutil

def render(template_file, output_file, json_keyword):
    json_files = sorted(glob.glob(f"*{json_keyword}*.json"), reverse=True)
    if not json_files:
        print(f"No matching JSON for {json_keyword}")
        return

    json_filename = json_files[0]
    nb = nbformat.read(template_file, as_version=4)

    for cell in nb.cells:
        if 'with open(' in cell.source:
            cell.source = cell.source.replace("with open(\"B:", f"with open(\"{json_filename}")
    
    nbformat.write(nb, output_file)
    print(f"{output_file} created.")

render("sourcebeauty_makeupbrands_clustering.ipynb", "notebook_noon.ipynb", "noon")
render("sourcebeauty_makeupbrands_clustering.ipynb", "notebook_amazon.ipynb", "amazon")
