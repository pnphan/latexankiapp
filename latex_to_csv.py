import os
import subprocess
import csv
import sys
from datetime import datetime

from PIL import Image

LATEX_TEMPLATE = r"""
\documentclass[preview, 20pt]{{standalone}}
\usepackage{{style}}
\usepackage[most]{{tcolorbox}}
\newtcolorbox{{mybox}}[1][]{{
  colback=gray!5,
  colframe=black,
  coltitle=black,
  colbacktitle=gray!20,
  fonttitle=\bfseries,
  title=#1,
  boxrule=0.8pt,
  arc=4pt,
  auto outer arc,
  left=6pt,
  right=6pt,
  top=6pt,
  bottom=6pt
}}
\begin{{document}}
\begin{{mybox}}[{title}]
{content}
\end{{mybox}}
\end{{document}}
"""

def create_card(title, content, filename="output"):
    tex_code = LATEX_TEMPLATE.format(title=title, content=content)
    with open(f"{filename}.tex", "w") as f:
        f.write(tex_code)

    subprocess.run(["pdflatex", "-interaction=nonstopmode", f"{filename}.tex"], stdout=subprocess.DEVNULL)
    subprocess.run(["pdfcrop", f"{filename}.pdf", f"{filename}_cropped.pdf"], stdout=subprocess.DEVNULL)
    # Expand the tilde to the actual home directory path
    home_dir = os.path.expanduser("~")
    output_path = f"{home_dir}/Library/Application Support/Anki2/User 1/collection.media/{filename}.png"
    # /Users/peterphan/Library/Application Support/Anki2/User 1/collection.media
    subprocess.run(["convert", "-density", "300", f"{filename}_cropped.pdf", output_path], stdout=subprocess.DEVNULL)
    
    # Clean up temporary files
    temp_files = [
        f"{filename}.tex",
        f"{filename}.pdf",
        f"{filename}_cropped.pdf",
        f"{filename}.aux",
        f"{filename}.log",
        f"{filename}.out"
    ]
    
    for file in temp_files:
        if os.path.exists(file):
            os.remove(file)

    return f"{filename}.png"

def save_to_csv(question_path, answer_path, csv_path="anki_cards.csv"):
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, mode="a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["Question", "Answer"])  # Header row
        writer.writerow([f'<img src="{os.path.basename(question_path)}">', f'<img src="{os.path.basename(answer_path)}">'])


# # === Example usage ===
# if __name__ == "__main__":


