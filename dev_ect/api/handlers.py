import sys
import os
import tempfile
from werkzeug.utils import secure_filename
import pandas as pd

# 1. Force Python to look in the exact directory where handlers.py lives
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 2. Now use the standard import (NO DOT)
from data_util import Data


def process_upload(file):
    """
    Connexion maps the 'file' from multipart/form-data directly to this argument.
    """
    if file is None or file.filename == '':
        return {"error": "No file provided"}, 400

    # Extract the original extension to ensure data_util.py routes it correctly
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()

    # Create a temporary file on disk with the correct extension
    # We set delete=False so it stays on disk long enough for pandas/pypdf to open it
    temp_fd, temp_path = tempfile.mkstemp(suffix=ext)
    
    try:
        # Save the uploaded stream to the temp file
        with os.fdopen(temp_fd, 'wb') as f:
            file.save(f)

        # Initialize your engine (Consider moving this to a global scope 
        # later so it doesn't reload the heavy NLP model on every single request)
        data_engine = Data()

        # Pass the file path to your exact method
        result = data_engine.anonymize_anything(temp_path)

        # Determine how to return the data based on what your script output
        if isinstance(result, pd.DataFrame):
            # Convert DataFrame to a list of dictionaries for JSON compatibility
            return_data = {
                "status": "success",
                "data_type": "dataframe",
                "results": result.to_dict(orient="records")
            }
        else:
            # It's a text block (from a PDF or TXT)
            return_data = {
                "status": "success",
                "data_type": "text",
                "results": result
            }

        return return_data, 200

    except ValueError as ve:
        # Catches the "Unsupported file type" error from your script
        return {"error": str(ve)}, 400
    except Exception as e:
        return {"error": f"An error occurred during processing: {str(e)}"}, 500
    finally:
        # Clean up the temporary file from the server
        if os.path.exists(temp_path):
            os.remove(temp_path)
