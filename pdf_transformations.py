import fitz  # PyMuPDF
import os


# ----------------------------------------------------------------------------------
def pdf_to_txt(pdf_path):
    doc = fitz.open(pdf_path)
    txt_path = pdf_path.replace('.pdf', '.txt')  
    with open(txt_path, 'w', encoding='utf-8') as file:
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            file.write(page.get_text())
    doc.close()
    return txt_path


# ----------------------------------------------------------------------------------
def highlight_words_in_pdf(input_pdf, words_list):
    try:
        doc = fitz.open(input_pdf)

        for page in doc:
            for word in words_list.split(' '):
                text_instances = page.search_for(word)
                for inst in text_instances:
                    page.add_highlight_annot(inst)
        
        dir_name, file_name = os.path.split(input_pdf)
        base_name, ext = os.path.splitext(file_name)
        output_pdf = os.path.join(dir_name, f"{base_name}.highlighted{ext}")
        
        doc.save(output_pdf)
        doc.close()
        return output_pdf
    except Exception as e:
        doc.close()
        return None


# ----------------------------------------------------------------------------------
def main():
    import sys
    if len(sys.argv) < 3:
        print(f"Usage: python {sys.argv[0]} <input.pdf> <word1> [word2 ...]")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    words_to_highlight = [word.lower() for word in sys.argv[2:]]
    
    highlight_words_in_pdf(input_pdf, words_to_highlight)


# ----------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
