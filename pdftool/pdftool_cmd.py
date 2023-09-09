from PyPDF2 import PdfFileReader, PdfFileWriter, PageObject
from tqdm import tqdm
from copy import copy
from dataclasses import dataclass
import argparse
from reportlab.pdfgen import canvas
from reportlab.lib import colors, pagesizes
from io import BytesIO
import os

class Watermark:
    """
    a PDF Watermark
    """
    
    @classmethod
    def get_watermark(cls, page, message: str, rotation: int = 0, font: str = 'Helvetica', 
                      font_size: int = 18, color=colors.blue) -> PdfFileWriter:
        """
        Create a temporary PDF with the given message as a watermark.
        
        Args:
            page (object): Page object to get the dimensions for watermark.
            message (str): Message to display as watermark.
            rotation (int): Rotation degree of the watermark text.
            font (str): Font for the watermark text. Default is 'Helvetica'.
            font_size (int): Font size for the watermark text. Default is 18.
            color: Color for the watermark text. Default is blue.
            
        Returns:
            PdfFileWriter: Temporary PDF with watermark.
        """
        
        # Use the dimensions from the cropBox (the visible portion of the page).
        page_width = float(page.cropBox.getWidth())
        page_height = float(page.cropBox.getHeight())
    
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=(page_width, page_height))
    
        text_width = can.stringWidth(message, font, font_size)
        text_height = font_size  # Assuming font_size roughly corresponds to height
        
        x = (page_width - text_width) / 2
        y = (page_height - text_height) / 2  # Adjusted y calculation
    
        can.saveState()  # Save the current state
    
        # Setting fill color and font details
        can.setFillColor(color)
        can.setFont(font, font_size)
        can.drawString(x, y, message)
    
        can.restoreState()  # Restore to the previous state
        can.save()
    
        packet.seek(0)
        new_pdf = PdfFileReader(packet)
    
        watermark = PdfFileWriter()
        watermark.add_page(new_pdf.getPage(0))
        
        return watermark

    
    @classmethod
    def get_watermarked_page(cls, page, message: str, rotation: int = 0):
        watermark = cls.get_watermark(page,message, rotation)
        watermarked_page = copy(page)
            
        # Merge watermark onto the page
        watermarked_page.merge_page(watermark.getPage(0))
            
        return watermarked_page

@dataclass
class HalfPage:
    """
    a half page in a booklet
    """
    page_num: int # index starting from one
    page: object  # The extracted page 
    
    def __str__(self):
        text=f"Halfpage {self.page_num}"
        if hasattr(self, "double_page"):
            text=f"{text} {str(self.double_page)}"
        return text
    
    def add_debug_info(self):
        debug_info=str(self)
        rotation=0
        if hasattr(self, "double_page"):
            rotation=self.double_page.rotation
        watermarked_page=Watermark.get_watermarked_page(self.page, debug_info,rotation)      
        return watermarked_page

@dataclass
class DoublePage:
    """
    a double page containing two half pages
    """
    page: object  # The actual page from PdfFileReader
    rotation: int # e.g. 0,90,180,270
    left: HalfPage
    right: HalfPage
    page_index: int # counting from 0

    @classmethod
    def from_page(cls, page, index, total_pages):
        # Get the rotation of the original page
        rotation = page.get('/Rotate', 0)
    
        # Create a rotated copy of the original page
        rotated_page = copy(page)
        rotated_page.rotateCounterClockwise(rotation)
    
        # Split the rotated page
        width = rotated_page.mediaBox.getWidth()
        height = rotated_page.mediaBox.getHeight()
    
        left_half = copy(rotated_page)
        left_half.cropBox.lowerLeft = (0, 0)
        left_half.cropBox.upperRight = (width / 2, height)
    
        right_half = copy(rotated_page)
        right_half.cropBox.lowerLeft = (width / 2, 0)
        right_half.cropBox.upperRight = (width, height)
    
        # Calculate booklet page numbers
        if index % 2 == 0:  # even index (0-based)
            left_num = total_pages - index
            right_num = index + 1
        else:
            left_num = index + 1
            right_num = total_pages - index
    
        # Create HalfPage instances for each half
        left = HalfPage(page_num=left_num, page=left_half)
        right = HalfPage(page_num=right_num, page=right_half)
    
        # Return a DoublePage instance
        return cls(page=page, rotation=rotation, left=left, right=right, page_index=index)

        
    def rotation_symbol(self)->str:
        rotation=self.rotation
        # Use Unicode symbols for rotation
        if rotation == 0:
            rotation_symbol = "↕   0"
        elif rotation == 90:
            rotation_symbol = "→  90"
        elif rotation == 180:
            rotation_symbol = "↔ 180"
        elif rotation == 270:
            rotation_symbol = "← 270"
        else:
            rotation_symbol = ""
        return rotation_symbol
    
    def __str__(self):
        text=f"Page {self.page_index}: {self.left.page_num}-{self.right.page_num} {self.rotation_symbol()}"
        return text
    
    def add_debug_info(self):
        debug_info=str(self)
        watermarked_page=Watermark.get_watermarked_page(self.page, debug_info,self.rotation)      
        return watermarked_page

@dataclass
class PdfFile:
    """
    a pdf file
    """
    filename: str
    reader: PdfFileReader = None
    double_pages: list = None
    pages: dict = None
    
    def __post_init__(self):
        if os.path.exists(self.filename):
            self.file_obj = open(self.filename, "rb")
            self.reader = PdfFileReader(self.file_obj)
        
    def close(self):
        if self.file_obj:
            self.file_obj.close()

    def read_booklet(self):
        self.double_pages = []
        double_page_count = self.reader.numPages

        for i in range(double_page_count):
            page = self.reader.getPage(i)
            double_page = DoublePage.from_page(page, i, double_page_count * 2)
            self.double_pages.append(double_page)

        return self.double_pages
        
    def add_half_page(self,double_page:DoublePage,half_page:HalfPage):
        half_page.double_page=double_page
        idx=half_page.page_num
        self.pages[idx]=half_page
        
    def un_booklet(self)->list:
        """
        convert my double pages to single pages by returning
        my half pages in proper order
        """
        # Convert double pages to single pages by extracting half pages in proper order.
        self.pages = {}
        for dp in self.double_pages:
            self.add_half_page(dp,dp.left)
            self.add_half_page(dp,dp.right)
        return self.pages
        
    @classmethod
    def create_double_pages(self, double_pages: int) -> list:
        """
        create double pages in booklet style
        """
        total_pages = double_pages * 2
        double_page_list = []

        for i in range(double_pages):
            rotation = 90 if i % 2 == 1 else 0

            if i % 2 == 0:
                left_page = HalfPage(page_num=total_pages - i, page=None)
                right_page = HalfPage(page_num=i + 1, page=None)
            else:
                left_page = HalfPage(page_num=i + 1, page=None)
                right_page = HalfPage(page_num=total_pages - i, page=None)

            double_page = DoublePage(page=None, rotation=rotation, 
                                     left=left_page, right=right_page, 
                                     page_index=i)
            double_page_list.append(double_page)

        return double_page_list
        
    def create_example_booklet(self, double_pages=3):
        """Creates a dummy booklet pdf with the specified number of double pages."""
        writer = PdfFileWriter()
        height,width=pagesizes.A4 # landscape A4
        
        double_pages=self.create_double_pages(double_pages)

        for double_page in double_pages:
            # Create an empty double page of 'A4 landscape' size
            double_page.page = PageObject.createBlankPage(width=width, height=height)
    
            # Left half of the page with debug info
            page_debug = double_page.add_debug_info()
            writer.add_page(page_debug)
        
        with open(self.filename, "wb") as output_file:
            writer.write(output_file)

class PDFTool:
    """
    A class to work on PDFs
    
    Functions:
        convert booklet-style PDF to plain PDF
    
    Attributes:
        input_file (str): The path to the input PDF file.
        output_file (str): The path to the output split PDF file.
    """
    
    def __init__(self, input_file: str, output_file: str, debug: bool = False) -> None:
        """
        Initializes the PDFTool with input and output file paths and optional debugging.
        
        Args:
            input_file (str): Path to the input PDF file.
            output_file (str): Path to the output PDF file.
            debug (bool): Whether to enable debugging watermarks. Default is False.
        """
        self.input_file = PdfFile(input_file)
        self.output_file = PdfFile(output_file)
        self.debug = debug
        self.args = None
        self.verbose=False
        
    def split_booklet_style(self) -> None:
        """
        Split a booklet-style PDF into individual pages.
        """
        if self.verbose:
            print(f"Processing {self.input_file.filename} ...")
    
        self.input_file.read_booklet()
        self.input_file.un_booklet()
    
        writer=PdfFileWriter()

        page_nums=sorted(list(self.input_file.pages.keys()))
        for page_num in tqdm(page_nums, desc="Processing pages", unit="page"):
            half_page=self.input_file.pages[page_num]
            if self.debug:
                page = half_page.add_debug_info()  
                writer.add_page(page)
            else:
                writer.add_page(half_page.page)
    
        if self.verbose:
            print(f"\nOutput at {self.output_file.filename}")
    
        with open(self.output_file.filename, "wb") as output_file:
            writer.write(output_file)
            
        self.input_file.close()
            
    @classmethod
    def get_parser(cls):
        """
        Return an argparse parser for the PDFTool class.
        """
        parser = argparse.ArgumentParser(description="Split a PDF booklet into individual pages.")
        parser.add_argument("input_file", type=str, help="Path to the input PDF file.")
        parser.add_argument("output_file", type=str, help="Path to the output PDF file.")
        parser.add_argument("-d","--debug", action="store_true", help="Enable debugging watermarks.")
        parser.add_argument("-v","--verbose", action="store_true", help="Give verbose output.")
        return parser
    
    @classmethod
    def from_args(cls):
        """
        Instantiate PDFTool from command-line arguments.
        """
        parser = cls.get_parser()
        args = parser.parse_args()
        tool=cls(args.input_file, args.output_file, args.debug)
        tool.args=args
        return tool

def main():
    """
    Main function to execute the PDFTool functionality based on command-line arguments.
    """
    tool = PDFTool.from_args()
    tool.split_booklet_style()

if __name__ == "__main__":
    main()
