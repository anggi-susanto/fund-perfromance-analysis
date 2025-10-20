"""
Test script to check if PDF tables are extractable with pdfplumber
"""
import pdfplumber

def test_pdf_extraction():
    pdf_path = "Sample_Fund_Performance_Report.pdf"
    
    print(f"Testing PDF: {pdf_path}")
    print("="*60)
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"\nTotal pages: {len(pdf.pages)}")
        
        for page_num, page in enumerate(pdf.pages, start=1):
            print(f"\nPage {page_num}:")
            print("-"*60)
            
            # Try to extract tables
            tables = page.extract_tables()
            print(f"Tables found: {len(tables)}")
            
            if tables:
                for table_idx, table in enumerate(tables):
                    print(f"\nTable {table_idx + 1}:")
                    print(f"  Rows: {len(table)}")
                    if table:
                        print(f"  Columns: {len(table[0]) if table[0] else 0}")
                        print(f"  Headers: {table[0] if table else 'None'}")
                        if len(table) > 1:
                            print(f"  First row: {table[1]}")
            else:
                print("  No tables found on this page")
            
            # Extract text
            text = page.extract_text()
            if text:
                lines = text.split('\n')[:10]  # First 10 lines
                print(f"\nFirst 10 lines of text:")
                for line in lines:
                    print(f"  {line}")

if __name__ == "__main__":
    try:
        test_pdf_extraction()
    except ImportError:
        print("Error: pdfplumber not installed")
        print("Install with: pip install pdfplumber")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
