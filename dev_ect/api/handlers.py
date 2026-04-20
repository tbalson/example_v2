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


def process_upload(files):
    """
    Connexion maps the 'files' array from multipart/form-data directly to this argument.
    """
    # 'files' is now a list of Werkzeug FileStorage objects
    if not files:
        return {"error": "No files provided"}, 400

    processed_results = []
    
    try:
        # Initialize the engine once outside the loop 
        # so it doesn't reload the heavy NLP model on every single file
        data_engine = Data()

        for file in files:
            # Skip empty file selections
            if file.filename == '':
                continue

            # Extract the original extension to ensure data_util.py routes it correctly
            filename = secure_filename(file.filename)
            ext = os.path.splitext(filename)[1].lower()

            # Create a temporary file on disk with the correct extension
            temp_fd, temp_path = tempfile.mkstemp(suffix=ext)
            
            try:
                # Save the uploaded stream to the temp file
                with os.fdopen(temp_fd, 'wb') as f:
                    file.save(f)

                # Pass the file path to your exact method
                result = data_engine.anonymize_anything(temp_path)

                # Determine how to return the data based on what your script output
                if isinstance(result, pd.DataFrame):
                    processed_results.append({
                        "filename": filename,
                        "status": "success",
                        "data_type": "dataframe",
                        "results": result.to_dict(orient="records")
                    })
                else:
                    processed_results.append({
                        "filename": filename,
                        "status": "success",
                        "data_type": "text",
                        "results": result
                    })

            finally:
                # Clean up the temporary file from the server immediately after processing it
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        # Return the aggregated results for all uploaded files
        return {
            "status": "success", 
            "processed_count": len(processed_results), 
            "batch_results": processed_results
        }, 200

    except ValueError as ve:
        # Catches the "Unsupported file type" error from your script
        return {"error": str(ve)}, 400
    except Exception as e:
        return {"error": f"An error occurred during processing: {str(e)}"}, 500
