from flask import Flask, render_template, request, jsonify, send_file
import os
from latex_to_csv import create_card, save_to_csv
import base64
from PIL import Image
import io
import time
from datetime import datetime
import pandas as pd
import csv

app = Flask(__name__)

DECK_NAMES_FILE = 'deck_names.txt'

def get_deck_names():
    if not os.path.exists(DECK_NAMES_FILE):
        # Create file with default deck if it doesn't exist
        with open(DECK_NAMES_FILE, 'w') as f:
            f.write('Misc\n')
        return ['Misc']
    
    with open(DECK_NAMES_FILE, 'r') as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def add_deck_name(deck_name):
    deck_names = get_deck_names()
    if deck_name not in deck_names:
        with open(DECK_NAMES_FILE, 'a') as f:
            f.write(f'{deck_name}\n')
        return True
    return False

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/select_deck', methods=['POST'])
def select_deck():
    data = request.json
    selected_deck = data.get('deck', 'Misc')
    deck_names = get_deck_names()
    
    if selected_deck not in deck_names:
        return jsonify({
            'success': False,
            'error': 'Invalid deck name'
        })
    
    global CSV_FILE
    CSV_FILE = f'entries/{selected_deck.lower().replace(" ", "_")}_entries.csv'

    global SELECTED_DECK
    SELECTED_DECK = selected_deck

    global DECK_PATH
    DECK_PATH = f'converted_decks/{selected_deck.lower().replace(" ", "_")}_converted.csv'
    
    # Create the CSV file if it doesn't exist
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame(columns=['Question', 'Answer'])
        df.to_csv(CSV_FILE, index=False)

    # Create the converted CSV file if it doesn't exist
    if not os.path.exists(DECK_PATH):
        df = pd.DataFrame(columns=['Question', 'Answer'])
        df.to_csv(DECK_PATH, index=False)
    
    return jsonify({
        'success': True,
        'message': f'Selected deck: {selected_deck}',
        'deck_names': deck_names
    })


@app.route('/create_deck', methods=['POST'])
def create_deck():
    data = request.json
    new_deck = data.get('deck', '').strip()
    
    if not new_deck:
        return jsonify({
            'success': False,
            'error': 'Deck name cannot be empty'
        })
    
    if add_deck_name(new_deck):
        # Create the CSV file for the new deck
        csv_file = f'entries/{new_deck.lower().replace(" ", "_")}_entries.csv'
        if not os.path.exists(csv_file):
            df = pd.DataFrame(columns=['Question', 'Answer'])
            df.to_csv(csv_file, index=False)
        
        return jsonify({
            'success': True,
            'message': f'Created new deck: {new_deck}',
            'deck_names': get_deck_names()
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Deck already exists'
        })


@app.route('/render', methods=['POST'])
def render_latex():
    data = request.json
    question = data.get('question', '')
    answer = data.get('answer', '')
    
    # Create unique filenames using timestamp
    timestamp = int(time.time())
    question_filename = f'temp_question_{timestamp}'
    answer_filename = f'temp_answer_{timestamp}'
    
    try:
        # Create the cards
        question_path = create_card("Question", question, question_filename)
        answer_path = create_card("Answer", answer, answer_filename)
        
        # Get the Anki media directory path
        home_dir = os.path.expanduser("~")
        anki_media_dir = os.path.join(home_dir, "Library/Application Support/Anki2/User 1/collection.media")
        
        # Convert images to base64 for display
        def image_to_base64(image_path):
            # Get just the filename from the path
            filename = os.path.basename(image_path)
            # Construct the full path in the Anki media directory
            full_path = os.path.join(anki_media_dir, filename)
            
            if not os.path.exists(full_path):
                raise Exception(f"Image file not found: {full_path}")
                
            with Image.open(full_path) as img:
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                return base64.b64encode(buffered.getvalue()).decode()
        
        question_base64 = image_to_base64(question_path)
        answer_base64 = image_to_base64(answer_path)
        
        # Clean up temporary files
        for filename in [f"{question_filename}.png", f"{answer_filename}.png"]:
            full_path = os.path.join(anki_media_dir, filename)
            if os.path.exists(full_path):
                os.remove(full_path)
        
        return jsonify({
            'success': True,
            'question_image': f'data:image/png;base64,{question_base64}',
            'answer_image': f'data:image/png;base64,{answer_base64}',
            'question_filename': question_filename,
            'answer_filename': answer_filename
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
    
@app.route('/save_entry', methods=['POST'])
def save_entry():
    data = request.json
    question = data.get('question', '')
    answer = data.get('answer', '')
    
    if question and answer:
        # Read existing CSV
        df = pd.read_csv(CSV_FILE)
        
        # Add new row
        new_row = pd.DataFrame({
            'Question': [question],
            'Answer': [answer]
        })
        df = pd.concat([df, new_row], ignore_index=True)
        
        # Save back to CSV
        df.to_csv(CSV_FILE, index=False)
        
        return jsonify({
            'success': True,
            'message': 'Entry saved successfully'
        })
    
    return jsonify({'status': 'error', 'message': 'Both fields are required'})

@app.route('/save_card', methods=['POST'])
def save_card():
    data = request.json
    question = data.get('question', '')
    answer = data.get('answer', '')
    
    try:
        # Create unique filenames for permanent storage
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        question_filename = f"{SELECTED_DECK}_question_{timestamp}"
        answer_filename = f"{SELECTED_DECK}_answer_{timestamp}"
        
        # Create the cards
        question_path = create_card("Question", question, question_filename)
        answer_path = create_card("Answer", answer, answer_filename)
        
        # Save to CSV
        save_to_csv(question_path, answer_path, DECK_PATH)
        
        return jsonify({
            'success': True,
            'message': 'Card saved successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
    
@app.route('/clear_entries', methods=['POST'])
def clear_entries():
    try:
        # Create empty DataFrame with headers
        df = pd.DataFrame(columns=['Question', 'Answer'])
        df.to_csv(CSV_FILE, index=False)
        
        return jsonify({
            'success': True,
            'message': 'All entries cleared successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/clear_cards', methods=['POST'])
def clear_cards():
    try:
        # Create empty DataFrame with headers
        df = pd.DataFrame(columns=['Question', 'Answer'])
        df.to_csv(DECK_PATH, index=False)
        
        return jsonify({
            'success': True,
            'message': 'All cards cleared successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
    
@app.route('/convert_entries', methods=['POST'])
def convert_entries():
    try:
        question_entries = []
        answer_entries = []

        with open(CSV_FILE, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row
            for row in reader:
                if row and len(row) > 0:
                    question_entries.append(row[0])
                    answer_entries.append(row[1])

        for question, answer in zip(question_entries, answer_entries):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            question_filename = f"{SELECTED_DECK}_question_{timestamp}"
            answer_filename = f"{SELECTED_DECK}_answer_{timestamp}"
            
            # Create the cards
            question_path = create_card("Question", question, question_filename)
            answer_path = create_card("Answer", answer, answer_filename)
            
            # Save to CSV
            save_to_csv(question_path, answer_path, DECK_PATH)
        
        return jsonify({
            'success': True,
            'message': 'All entries converted successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True) 