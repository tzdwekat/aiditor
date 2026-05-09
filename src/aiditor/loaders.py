from pathlib import Path
import pypdf
import mammoth


def script_to_text(filepath: str) -> str:
    """Convert script input (txt, md, docx, pdf) to plain text."""
    path = Path(filepath)
    suffix = path.suffix.lower()
    
    if suffix in [".txt", ".md"]:
        return path.read_text(encoding="utf-8")
    
    elif suffix == ".docx":
        with open(filepath, "rb") as f:
            result = mammoth.convert_to_markdown(f)
            return result.value
    
    elif suffix == ".pdf":
        reader = pypdf.PdfReader(filepath)
        return "\n".join(page.extract_text() for page in reader.pages)
    
    else:
        raise ValueError(f"Unsupported format: {suffix}")