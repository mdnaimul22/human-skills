import sys
import asyncio
from pypdf import PdfReader
from helpers.tool import Tool, Response

class check_fillable_fields(Tool):
    name = "check_fillable_fields"
    description = "Checks if a PDF has fillable form fields."
    arguments = "json payload with 'pdf_path'"
    
    async def execute(self, **kwargs) -> Response:
        pdf_path = self.args.get("pdf_path")
        if not pdf_path:
            return Response(message="Error: pdf_path is required.", break_loop=False)
            
        try:
            reader = PdfReader(pdf_path)
            if reader.get_fields():
                return Response(message="✅ This PDF has fillable form fields", break_loop=False)
            else:
                return Response(message="ℹ️ This PDF does not have fillable form fields; you will need to visually determine where to enter data", break_loop=False)
        except Exception as e:
            return Response(message=f"❌ Error reading PDF: {e}", break_loop=False)

if __name__ == "__main__":
    # Compatibility for direct execution
    if len(sys.argv) > 1:
        tool = check_fillable_fields({"pdf_path": sys.argv[1]})
        res = asyncio.run(tool.execute())
        print(res.message)
