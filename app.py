from flask import Flask, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
import os, zipfile
from datetime import datetime
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///renamed.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Database Model
class FileRename(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_name = db.Column(db.String(100))
    new_name = db.Column(db.String(100))
    prefix_used = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Handle file upload and renaming
@app.route('/rename', methods=['POST'])
def rename_files():
    files = request.files.getlist('files')
    prefix = request.form.get('prefix') or 'file'
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], 'renamed_files.zip')

    # Create a zip file and rename files
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for i, file in enumerate(files, 1):
            original_name = secure_filename(file.filename)
            ext = os.path.splitext(original_name)[1]
            new_name = f"{prefix}_{i}{ext}"
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], new_name)

            file.save(temp_path)
            zipf.write(temp_path, arcname=new_name)
            os.remove(temp_path)

            # Log rename in DB
            record = FileRename(
                original_name=original_name,
                new_name=new_name,
                prefix_used=prefix
            )
            db.session.add(record)

    db.session.commit()
    return send_file(zip_path, as_attachment=True)

# View history of renames
@app.route('/history')
def history():
    records = FileRename.query.order_by(FileRename.timestamp.desc()).all()
    return render_template('history.html', records=records)

# Main entry point
if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
