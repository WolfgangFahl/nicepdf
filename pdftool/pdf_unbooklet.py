from PyPDF2 import PdfFileReader, PdfFileWriter
from tqdm import tqdm
from copy import copy
import argparse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

class PDFTool:
    """
    A class to work on PDFs
    
    Functions:
        convert booklet-style PDF to plain PDF
    
    Attributes:
        input_file (str): The path to the input PDF file.
        output_file (str): The path to the output split PDF file.
    """
    
    def __init__(self, input_file: str, output_file: str) -> None:
        """
        Initializes the PDFSplitter with input and output file paths.
        
        Args:
            input_file (str): Path to the input PDF file.
            output_file (str): Path to the output split PDF file.
        """
        self.input_file = input_file
        self.output_file = output_file
        
    def get_watermark(self, message: str) -> PdfFileWriter:
        """
        Create a temporary PDF with the given message as a watermark.
        
        Args:
            message (str): Message to display as watermark.
            
        Returns:
            PdfFileWriter: Temporary PDF with watermark.
        """
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        can.drawString(10, 100, message)
        can.save()

        packet.seek(0)
        new_pdf = PdfFileReader(packet)

        watermark = PdfFileWriter()
        watermark.add_page(new_pdf.getPage(0))
        
        return watermark
    
    def add_debug_info(self, page, rotation, orig_page_num) -> PdfFileWriter:
        """
        Add debugging watermark to the provided page.
        
        Args:
            page (PdfFileWriter): The PDF page to watermark.
            rotation (int): Rotation angle of the page.
            orig_page_num (int): Original page number from the input.
            
        Returns:
            PdfFileWriter: Watermarked PDF page.
        """
        
        watermark = self.get_watermark(f"Rotation: {rotation}, Orig Page: {orig_page_num}")
        watermarked_page = copy(page)
        
        # Merge watermark onto the page
        watermarked_page.merge_page(watermark.getPage(0))
        
        return watermarked_page

    def split_page(self, page):
        """
        Split the page into left and right halves taking into account any page rotations.
    
        Args:
            page: The PDF page to split.
    
        Returns:
            Tuple[PDF page, PDF page]: Left and right halves.
        """
        # Extract the dimensions of the page
        width = page.mediaBox.getWidth()
        height = page.mediaBox.getHeight()
    
        # Adjust for rotated pages
        rotation = page.get('/Rotate')
        if rotation in (90, 270):
            width, height = height, width
    
        # Left half
        left_half = copy(page)
        left_half.mediaBox.upperRight = (width / 2, height)
        left_half.mediaBox.lowerLeft = (0, 0)
    
        # Adjust rotation if needed
        if rotation:
            left_half.rotateClockwise(rotation)
    
        # Right half
        right_half = copy(page)
        right_half.mediaBox.lowerLeft = (width / 2, 0)
        right_half.mediaBox.upperRight = (width, height)
    
        # Adjust rotation if needed
        if rotation:
            right_half.rotateClockwise(rotation)
                 
        return left_half, right_half

    def split_booklet_style(self) -> None:
        """
        Split a booklet-style PDF into individual pages.
        
        A booklet-style PDF is designed to be printed double-sided and 
        then folded in half. The first scanned page contains the first and 
        the last pages of the booklet. Subsequent scans are from front and 
        back respectively, moving toward the center.
        
        Raises:
            ValueError: If the booklet does not have an even number of pages.
        """
        
        with open(self.input_file, "rb") as file:
            self.reader = PdfFileReader(file)
            self.writer = PdfFileWriter()
    
            num_pages = len(self.reader.pages)
            if num_pages % 2 != 0:
                raise ValueError("Booklet should have an even number of pages.")
    
            # Handle first scanned page
            right_half, left_half = self.split_page(self.reader.pages[0])
            self.writer.add_page(right_half)
            self.writer.add_page(left_half) 
    
            # Use tqdm for progress bar
            for idx in tqdm(range(1, num_pages // 2), desc="Splitting", ncols=100):
                # Process right side from the front part of the booklet
                page=self.reader.pages[idx]
                _, right_half = self.split_page(page)
                #if debug is enabled, add watermark
                if self.debug:
                    rotation = page.get('/Rotate', 0)
                    right_half = self.add_debug_info(right_half, rotation, idx)
                self.writer.add_page(right_half)
        
                
                # Process left side from the back part of the booklet
                left_half, _ = self.split_page(self.reader.pages[num_pages - idx])
                self.writer.add_page(left_half)
            
            # Handle middle scanned page (if there's an odd number of double pages)
            if num_pages % 4 != 0:
                middle_page_index = num_pages // 2
                left_half, right_half = self.split_page(self.reader.pages[middle_page_index])
                self.writer.add_page(left_half)   
                self.writer.add_page(right_half)   
                
            left_half = self.add_debug_info(left_half, rotation, num_pages - idx)
   
            with open(self.output_file, "wb") as output_file:
                self.writer.write(output_file)

def main():
    parser = argparse.ArgumentParser(description="Split a PDF booklet into individual pages.")
    parser.add_argument("input_file", type=str, help="Path to the input PDF file.")
    parser.add_argument("output_file", type=str, help="Path to the output PDF file.")
    parser.add_argument("--debug", action="store_true", help="Enable debugging watermarks.")
     
    args = parser.parse_args()

    tool = PDFTool(args.input_file, args.output_file)
    tool.split_booklet_style()

if __name__ == "__main__":
    main()
