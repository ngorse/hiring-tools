import fitz  # PyMuPDF
import sys
import os

def highlight_words_in_pdf(input_pdf, words):
    doc = fitz.open(input_pdf)  # Open the PDF file
    
    for page in doc:  # Loop through pages
        for word in words:
            text_instances = page.search_for(word)  # PyMuPDF's search_for is case-insensitive by default
            
            for inst in text_instances:
                page.add_highlight_annot(inst)  # Highlight each occurrence
    
    dir_name, file_name = os.path.split(input_pdf)  # Split path and filename
    base_name, ext = os.path.splitext(file_name)  # Extract filename and extension
    output_pdf = os.path.join(dir_name, f"candidate-{base_name}{ext}")  # Construct new filename
    
    doc.save(output_pdf)  # Save to a new PDF file
    print(f"Highlights added. Saved as {output_pdf}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py input.pdf word1 word2 ...")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    words_to_highlight = [word.lower() for word in sys.argv[2:]]  # Normalize input words
    
    highlight_words_in_pdf(input_pdf, words_to_highlight)
