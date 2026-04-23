import sys
from pypdf import PdfReader

class Tool:
    """Base class for tools"""
    def __init__(self, args: dict):
        self.args = args

class check_fillable_fields(Tool):
    name = "check_fillable_fields"
    description = "Checks if a PDF has fillable form fields."
    arguments = "json payload with 'pdf_path'"
    
    async def execute(self):
        pdf_path = self.args.get("pdf_path")
        if not pdf_path:
            return "Error: pdf_path is required."
            
        try:
            reader = PdfReader(pdf_path)
            if reader.get_fields():
                return "✅ This PDF has fillable form fields"
            else:
                return "ℹ️ This PDF does not have fillable form fields; you will need to visually determine where to enter data"
        except Exception as e:
            return f"❌ Error reading PDF: {e}"

if __name__ == "__main__":
    # Compatibility for direct execution
    if len(sys.argv) > 1:
        import asyncio
        tool = check_fillable_fields({"pdf_path": sys.argv[1]})
        print(asyncio.run(tool.execute()))
