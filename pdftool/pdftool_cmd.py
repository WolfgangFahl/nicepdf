from PyPDF2 import PdfFileReader, PdfFileWriter
from tqdm import tqdm
from copy import copy
from dataclasses import dataclass
import argparse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO

@dataclass
class PageInfo:
    page: object  # The actual page from PdfFileReader
    rotation: int
    orig_index: int

class PDFTool:
    """
    A class to work on PDFs
    
    Functions:
        convert booklet-style PDF to plain PDF
    
    Attributes:
        input_file (str): The path to the input PDF file.
        output_file (str): The path to the output split PDF file.
    """
    
    def __init__(self, input_file: str, output_file: str, debug: bool = False, args: argparse.Namespace = None) -> None:
        """
        Initializes the PDFTool with input and output file paths and optional debugging.
        
        Args:
            input_file (str): Path to the input PDF file.
            output_file (str): Path to the output PDF file.
            debug (bool): Whether to enable debugging watermarks. Default is False.
            args (argparse.Namespace): The parsed command-line arguments.
        """
        self.input_file = input_file
        self.output_file = output_file
        self.debug = debug
        self.args = args
        
    @classmethod    
    def get_watermark(cls, message: str) -> PdfFileWriter:
        """
        Create a temporary PDF with the given message as a watermark.
        
        Args:
            message (str): Message to display as watermark.
            
        Returns:
            PdfFileWriter: Temporary PDF with watermark.
        """
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)  # Use A4 pagesize
        # Calculate coordinates to center the message on the page
        text_width = can.stringWidth(message, 'Helvetica', 18)
        x = (A4[0] - text_width) / 2
        y = A4[1] / 2
        
        can.setFont('Helvetica', 18)
        can.drawString(x, y, message)
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
        
        watermark = self.get_watermark(f"Rotation: {rotation}, Page: {orig_page_num}")
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

    def gather_pages(self) -> list[PageInfo]:
        """
        Gather pages from the booklet in the order they should be processed.
        """
        num_pages = len(self.reader.pages)
        pages = []

        # Handle first scanned page
        right_page, left_page = self.split_page(self.reader.pages[0])
        pages.append(PageInfo(right_page, right_page.get('/Rotate', 0), 0))
        pages.append(PageInfo(left_page, left_page.get('/Rotate', 0), num_pages - 1))
        
        for idx in range(1, num_pages):
            # Process right side from the front part of the booklet
            page = self.reader.pages[idx]
            _, right_page = self.split_page(page)
            pages.append(PageInfo(right_page, page.get('/Rotate', 0), idx))

            # Process left side from the back part of the booklet
            page = self.reader.pages[num_pages - idx]
            left_page, _ = self.split_page(page)
            pages.append(PageInfo(left_page, page.get('/Rotate', 0), num_pages - idx))
    
        return pages
    
    def split_booklet_style(self) -> None:
        """
        Split a booklet-style PDF into individual pages.
        """
        if self.debug:
            print(f"processing {self.input_file} ...")
        with open(self.input_file, "rb") as file:
            self.reader = PdfFileReader(file)
            self.writer = PdfFileWriter()

            pages = self.gather_pages()
            
            for page_info in pages:
                if self.debug:
                    page = self.add_debug_info(page_info.page, page_info.rotation, page_info.orig_index)
                    self.writer.add_page(page)
                else:
                    self.writer.add_page(page_info.page)
        
            if self.debug:
                print(f"output at {self.output_file}")
            with open(self.output_file, "wb") as output_file:
                self.writer.write(output_file)
                
    @classmethod
    def get_parser(cls):
        """
        Return an argparse parser for the PDFTool class.
        """
        parser = argparse.ArgumentParser(description="Split a PDF booklet into individual pages.")
        parser.add_argument("input_file", type=str, help="Path to the input PDF file.")
        parser.add_argument("output_file", type=str, help="Path to the output PDF file.")
        parser.add_argument("-d","--debug", action="store_true", help="Enable debugging watermarks.")
        return parser
    
    @classmethod
    def from_args(cls):
        """
        Instantiate PDFTool from command-line arguments.
        """
        parser = cls.get_parser()
        args = parser.parse_args()
        return cls(args.input_file, args.output_file, args.debug, args)

def main():
    """
    Main function to execute the PDFTool functionality based on command-line arguments.
    """
    tool = PDFTool.from_args()
    tool.split_booklet_style()

if __name__ == "__main__":
    main()
