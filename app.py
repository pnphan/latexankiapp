from flask import Flask, render_template, request, jsonify, send_file
import os
from latex_to_csv import create_card, save_to_csv
import base64
from PIL import Image
import io
import time
from datetime import datetime
import pandas as pd

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

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

@app.route('/save_card', methods=['POST'])
def save_card():
    data = request.json
    question = data.get('question', '')
    answer = data.get('answer', '')
    
    try:
        # Create unique filenames for permanent storage
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        question_filename = f"card_question_{timestamp}"
        answer_filename = f"card_answer_{timestamp}"
        
        # Create the cards
        question_path = create_card("Question", question, question_filename)
        answer_path = create_card("Answer", answer, answer_filename)
        
        # Save to CSV
        save_to_csv(question_path, answer_path)
        
        return jsonify({
            'success': True,
            'message': 'Card saved successfully'
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
        df.to_csv('anki_cards.csv', index=False)
        
        return jsonify({
            'success': True,
            'message': 'All cards cleared successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True) 