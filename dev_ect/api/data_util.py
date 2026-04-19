"""
Author: Tyler Balson
Date Created: March 2026
Date Modified:
Purpose: This module provides the Data class, which includes methods for determining file types, processing DataFrames, and anonymizing text blocks using the presidio_analyzer and presidio_anonymizer libraries.
The main entry point is the anonymize_anything method, which can handle various file types and apply the anonymization process accordingly.
Citation: The code is inspired by the Microsoft Presidio project and adapted for specific use cases. The Data class is designed to be flexible and extensible, allowing for easy integration of additional file types and entity types as needed.
Source: https://github.com/Microsoft/presidio?tab=MIT-1-ov-file ;
Use: This module will be used as a primary endpoint for anonymizing sensitive data in various file formats within and ECT internal pipeline. File that can be handeled include
text files, PDFs, CSVs, Excel files, and SQLite databases. This model can be integrated into larger data processing pipelines or used as a standalone tool for data anonymization tasks in
repeatable and documentable way.
"""






from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
import os
from pathlib import Path
import pandas as pd
import sqlite3
from presidio_analyzer.nlp_engine import SpacyNlpEngine # Import SpacyNlpEngine
from pypdf import PdfReader


class Data:
    def __init__(self, dst=0.2):
        """Initialize Data anonymization engine.


        dst: float, optional
            minimum confidence score threshold for entity detection (default 0.2).
        """
        # Configure the NLP/analyzer/anonymizer once per object instance
        # default_score_threshold=0.2 means that any entity with a confidence
        # score above 0.2 will be considered for anonymization.
        self.nlp_engine = SpacyNlpEngine()
        self.analyzer = AnalyzerEngine(nlp_engine=self.nlp_engine, default_score_threshold=dst)
        self.anonymizer = AnonymizerEngine()


    def data_type(self, filename):
        """Determines file type based on extension."""
        extension = filename.split('.')[-1].lower()
       
        file_types = {
            'txt': 'text',
            'pdf': 'document',
            'jpg': 'image',
            'png': 'image',
            'gif': 'image',
            'mp4': 'video',
            'mp3': 'audio',
            'csv': 'data',
            'json': 'data',
            'xlsx': 'spreadsheet, xlsx'
        }
        return file_types.get(extension, 'unknown')


    def process_dataframe(self, df, entities):
        """Processes a DataFrame using the provided analyzer and anonymizer."""
        df_clean = df.copy()
        sensitive_data_report = {}  # Track sensitive data found: {column: {entity_type: count}}
       
        for col in df_clean.columns:  # Iterate over all columns
            sensitive_data_report[col] = {}
            anonymized_values = []
           
            for idx, value in enumerate(df_clean[col]):
                text = str(value)
                results = self.analyzer.analyze(text=text, entities=entities, language='en')
               
                # Track entity types found in this cell
                for entity in results:
                    entity_type = entity.entity_type
                    sensitive_data_report[col][entity_type] = sensitive_data_report[col].get(entity_type, 0) + 1
               
                # Anonymize the text
                anonymized_result = self.anonymizer.anonymize(text=text, analyzer_results=results)
                anonymized_values.append(anonymized_result.text)
           
            df_clean[col] = anonymized_values
           
            # Remove columns with no sensitive data for cleaner reporting
            if not sensitive_data_report[col]:
                del sensitive_data_report[col]
       
        # Print report
        if sensitive_data_report:
            print("\n" + "="*70)
            print("SENSITIVE DATA DETECTION REPORT")
            print("="*70)
            for col, entity_counts in sensitive_data_report.items():
                print(f"\nColumn: '{col}'")
                total_detections = sum(entity_counts.values())
                for entity_type, count in sorted(entity_counts.items()):
                    print(f"  • {entity_type}: {count} occurrence(s)")
                print(f"  Total sensitive items in column: {total_detections}")
            print("="*70 + "\n")
        else:
            print("\n" + "="*70)
            print("No sensitive data detected in any columns.")
            print("="*70 + "\n")
       
        return df_clean
   
    def anonymize_text_block(self, text, entities):
        """Anonymizes a block of text using the provided analyzer and anonymizer."""
        results = self.analyzer.analyze(text=text, entities=entities, language='en')


        # Build report for non-dataframe text input
        if results:
            entity_counts = {}
            for entity in results:
                entity_counts[entity.entity_type] = entity_counts.get(entity.entity_type, 0) + 1


            print("\n" + "="*70)
            print("SENSITIVE DATA DETECTION REPORT (text/pdf)")
            print("="*70)
            for entity_type, count in sorted(entity_counts.items()):
                print(f"  • {entity_type}: {count} occurrence(s)")
            print(f"  Total sensitive items in text: {sum(entity_counts.values())}")
            print("="*70 + "\n")
        else:
            print("\n" + "="*70)
            print("No sensitive data detected in text/pdf content.")
            print("="*70 + "\n")


        anonymized_result = self.anonymizer.anonymize(text=text, analyzer_results=results)
        return anonymized_result.text
   
    def anonymize_anything(self, source, entities=None, table_name=None):
        """ Main Entry point: handles CSV, XLSX, and text files. """
        if entities is None:
            entities = ['PERSON', 'ORG', 'GPE', 'DATE', 'EMAIL', 'EMAIL_ADDRESS', 'PHONE', 'PHONE_NUMBER', 'ADDRESS', 'LOCATION', 'URL', 'IP_ADDRESS', 'US_SSN', 'CREDIT_CARD', "BIRTHDATE", "DL_NUMBER"]


        if isinstance(source, (str, Path)) and os.path.exists(source):
            ext = Path(source).suffix.lower()
            #csv
            if ext == '.csv':
                df = pd.read_csv(source)
                return self.process_dataframe(df, entities)
            # xlsx, xls
            elif ext in ['.xlsx', '.xls']:
                df = pd.read_excel(source)
                return self.process_dataframe(df, entities)
            elif ext in ['.db', '.sqlite', '.sqlite3']:
                conn = sqlite3.connect(source)
                if not table_name:
                    table_name = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn).iloc[0, 0]
                df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
                conn.close()
                return self.process_dataframe(df, entities)
               
            # text files
            elif ext in ['.txt', '.md', '.log', '.pdf']:
                if ext == '.pdf':
                    reader = PdfReader(source)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                else:
                    with open(source, 'r') as file:
                        text = file.read()
                return self.anonymize_text_block(text, entities)
            elif hasattr(source, 'read'):
                return self.anonymize_text_block(source.read(), entities)
            else:
                raise ValueError(f"Unsupported file type: {ext}")




