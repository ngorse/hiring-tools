import fitz  # PyMuPDF
import sys
import os

def highlight_words_in_pdf(input_pdf, words):
    doc = fitz.open(input_pdf)
    
    for page in doc:
        for word in words:
            text_instances = page.search_for(word)
            
            for inst in text_instances:
                page.add_highlight_annot(inst)
    
    dir_name, file_name = os.path.split(input_pdf)
    base_name, ext = os.path.splitext(file_name)
    output_pdf = os.path.join(dir_name, f"{base_name}.highlighted{ext}")
    
    doc.save(output_pdf)
    print(f"Highlighted copy of {input_pdf} saved to {output_pdf}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: python {sys.argv[0]} <input.pdf> <word1> [word2 ...]")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    words_to_highlight = [word.lower() for word in sys.argv[2:]]
    
    highlight_words_in_pdf(input_pdf, words_to_highlight)
