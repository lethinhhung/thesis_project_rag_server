import re
import unicodedata


def clean_document_text(text: str) -> str:
    """
    Clean document text by removing page numbers, markdown, and extra whitespace.
    Used for document ingestion processing.
    """
    # Remove page numbers
    text = re.sub(r'Page \d+ of \d+', '', text)
    
    # Remove simple markdown formatting
    text = re.sub(r'\*\*|__|~~|```', '', text)
    
    # Strip whitespace from each line
    lines = [line.strip() for line in text.splitlines()]
    
    # Remove excessive blank lines (multiple blank lines become one)
    cleaned_lines = []
    blank_line = False
    for line in lines:
        if line == '':
            if not blank_line:
                cleaned_lines.append(line)
            blank_line = True
        else:
            cleaned_lines.append(line)
            blank_line = False
    
    # Join back with standard newlines
    cleaned_text = '\n'.join(cleaned_lines)
    
    return cleaned_text.strip()


def clean_vietnamese_text(text: str) -> str:
    """
    Clean Vietnamese text for search queries by normalizing Unicode,
    removing special characters, and trimming whitespace.
    """
    # Normalize Unicode (use NFC to combine diacritics)
    text = unicodedata.normalize("NFC", text)

    # Remove special characters (keep Vietnamese characters and numbers)
    text = re.sub(r"[^\w\sàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩ"
                  r"òóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]", "", text)

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text