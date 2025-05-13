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


# === Example usage ===
if __name__ == "__main__":
    entries_location = "data/entries.csv"
    csv_path = f"data/anki_cards_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    # Read entries from CSV file
    question_entries = []
    answer_entries = []
    try:
        with open(entries_location, mode="r", newline="") as csvfile:
            reader = csv.reader(csvfile)
            # Skip header row if it exists
            next(reader, None)
            for row in reader:
                if row and len(row) > 0:  # Ensure row is not empty
                    question_entries.append(row[0])
                    answer_entries.append(row[1])
    except FileNotFoundError:
        print(f"Error: File {entries_location} not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)
    
    if not question_entries or not answer_entries:
        print("No entries found in the CSV file.")
        sys.exit(0)
        
    for question_entry, answer_entry in zip(question_entries, answer_entries):
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        question_filename = f"{now}_question"
        answer_filename = f"{now}_answer"
        
        question_path = create_card("Question", question_entry, question_filename)
        answer_path = create_card("Answer", answer_entry, answer_filename)
        save_to_csv(question_path, answer_path, csv_path)

