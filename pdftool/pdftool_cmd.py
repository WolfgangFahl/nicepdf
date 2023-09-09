from PyPDF2 import PdfReader, PdfWriter, Transformation
from tqdm import tqdm
from copy import copy
from dataclasses import dataclass
import argparse
from reportlab.pdfgen import canvas
from reportlab.lib import colors, pagesizes
from io import BytesIO
from pdftool.version import Version
from pdftool.webserver import WebServer
import os
import random
import sys
import webbrowser
import traceback

class Watermark:
    """
    a PDF Watermark
    """
    
    @classmethod
    def get_watermark(cls, page, message: str, font: str = 'Helvetica', 
                      font_size: int = 18, color=colors.blue) -> PdfWriter:
        """
        Create a temporary PDF with the given message as a watermark.
    
        Args:
            page (object): Page object to get the dimensions and rotation for watermark.
            message (str): Message to display as watermark.
            font (str): Font for the watermark text. Default is 'Helvetica'.
            font_size (int): Font size for the watermark text. Default is 18.
            color: Color for the watermark text. Default is blue.
    
        Returns:
            PdfWriter: Temporary PDF with watermark.
        """
        
        # Use the dimensions from the cropbox (the visible portion of the page).
        page_width = float(page.cropbox.width)
        page_height = float(page.cropbox.height)
        rotation = page.get('/Rotate', 0)  # Fetching the rotation from the page
    
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
        can.translate(x + text_width / 2, y + text_height / 2)  # Move the origin to the center of the text
        can.rotate(rotation)  # Rotate the canvas by the rotation of the page
        can.drawString(-text_width / 2, -text_height / 2, message)  # Draw the string at the rotated origin
    
        can.restoreState()  # Restore to the previous state
        can.save()
    
        packet.seek(0)
        new_pdf = PdfReader(packet)
    
        watermark = PdfWriter()
        watermark.add_page(new_pdf.pages[0])
        
        return watermark

    
    @classmethod
    def get_watermarked_page(cls, page, message: str):
        watermark = cls.get_watermark(page,message)
        watermarked_page = copy(page)
            
        # Merge watermark onto the page
        watermarked_page.merge_page(watermark.pages[0])
            
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
        watermarked_page=Watermark.get_watermarked_page(self.page, debug_info)      
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
    def copy_page(self,writer:PdfWriter,page,width,height,tx,ty):
        new_page=writer.add_blank_page(width, height)
        # Get the rotation of the original page
        rotation = page.get('/Rotate', 0)
        rotated_page=copy(page)
        rotated_page.add_transformation(Transformation().translate(tx, ty))
        
        new_page.merge_page(rotated_page)
        return new_page

    @classmethod
    def from_page(cls, page, index, total_pages):
        # Get the rotation of the original page
        rotation = page.get('/Rotate', 0)
        width = page.mediabox.width
        height = page.mediabox.height
        a4_width, a4_height = pagesizes.A4  # Landscape A4
        writer = PdfWriter()
        rotated_page = cls.copy_page(writer=writer,page=page,width=a4_width, height=a4_height,tx=0,ty=0)
        
        # Create two new blank pages with half the width of the original
    
        left_half = cls.copy_page(writer=writer,page=rotated_page,width=width/2, height=height,tx=0,ty=0)
        right_half = cls.copy_page(writer=writer,page=rotated_page,width=width/2, height=height,tx=-width/2, ty=0)
    
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
        watermarked_page=Watermark.get_watermarked_page(self.page, debug_info)      
        return watermarked_page

@dataclass
class PdfFile:
    """
    a pdf file
    """
    filename: str
    reader: PdfReader = None
    double_pages: list = None
    pages: dict = None
    
    def __post_init__(self):
        """
        set my reader
        """
        self.open()
    
    def open(self):
        if self.filename and os.path.exists(self.filename):
            self.file_obj = open(self.filename, "rb")
            self.reader = PdfReader(self.file_obj)
        else:
            self.file_obj=None
        
    def close(self):
        if self.file_obj:
            self.file_obj.close()

    def read_booklet(self):
        """
        read min input as a booklet
        """
        self.double_pages = []
        double_page_count = len(self.reader.pages)

        for i in range(double_page_count):
            page = self.reader.pages[i]
            double_page = DoublePage.from_page(page, i, double_page_count * 2)
            self.double_pages.append(double_page)

        return self.double_pages
        
    def add_half_page(self,double_page:DoublePage,half_page:HalfPage):
        """
        add the given half page that is part of the given double_page
        to my pages
        """
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
    
    def create_double_page_with_numbers(self, left_page_number, right_page_number):
        """Generate a double PDF page with the given page numbers."""
        buffer = BytesIO()
        width, height = pagesizes.A4  # Landscape A4
        
        c = canvas.Canvas(buffer, pagesize=(width, height))
        
        # Drawing squares for the left and right pages
        c.rect(100, 350, 300, 300, fill=0)  # Left page square
        c.rect(width-400, 350, 300, 300, fill=0)  # Right page square

        # Placing numbers in the center of the squares
        c.setFont("Helvetica-Bold", 120)
        c.drawCentredString(width/4, 500, str(left_page_number))
        c.drawCentredString(3*width/4, 500, str(right_page_number))
        
        c.showPage()
        c.save()
        
        buffer.seek(0)
        return PdfReader(buffer)
        
    def create_example_booklet(self, double_pages=2,with_random_rotation:bool=False):
        """Creates a dummy booklet pdf with the specified number of double pages."""
        writer = PdfWriter()
        double_pages=self.create_double_pages(double_pages)

        for double_page in double_pages:
            # Create an empty double page of 'A4 landscape' size
            left=double_page.left
            right=double_page.right
            reader=self.create_double_page_with_numbers(left.page_num, right.page_num)
            rotated_page = reader.pages[0]
            # If random rotation is enabled, rotate the page randomly
            if with_random_rotation:
                angle = random.choice([0, 90, 180, 270])
                rotated_page = rotated_page.rotate(angle)
            double_page.page = rotated_page
            writer.add_page(double_page.page)
        
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
 
        Input is a collection of A4 landscape double pages, 
        scanned from an A5 booklet.
        
        Some pages might have been rotated to visualize them in a human readable way (instead of e.g. upside/down).
        

        Goal: Split the A4 landscape pages into individual A5 pages taking the rotation into account
        Expected Output: Instead of e.g. 50 double pages containing two A5 pages each, we should have 100 individual pages in A4 format.

        """
        if self.verbose:
            print(f"Processing {self.input_file.filename} ...")
    
        self.input_file.read_booklet()
        self.input_file.un_booklet()
    
        writer=PdfWriter()

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
        parser.add_argument("-a","--about",help="show about info [default: %(default)s]",action="store_true")
        parser.add_argument("-c","--client", action="store_true", help="start client [default: %(default)s]")
        parser.add_argument("-d","--debug", action="store_true", help="Enable debugging watermarks.")
        parser.add_argument("--host", default="localhost",
                            help="the host to serve / listen from [default: %(default)s]")
        parser.add_argument("--port",type=int,default=9849,help="the port to serve from [default: %(default)s]")
        parser.add_argument("-i","--input", type=str, help="Path to the input PDF file.")
        parser.add_argument("-o","--output", type=str, help="Path to the output PDF file.")
        parser.add_argument("-s","--serve", action="store_true", help="start webserver [default: %(default)s]")
        parser.add_argument("-v","--verbose", action="store_true", help="Give verbose output.")
  
        return parser
    
    @classmethod
    def from_args(cls):
        """
        Instantiate PDFTool from command-line arguments.
        """
        parser = cls.get_parser()
        args = parser.parse_args()
        tool=cls(args.input, args.output, args.debug)
        tool.args=args
        tool.verbose=args.verbose
        return tool

def main(argv=None): 
    """
    Main function to execute the PDFTool functionality based on command-line arguments.
    """
    '''main program.'''

    if argv is None:
        argv=sys.argv[1:]
        
    program_name = Version.name
    program_version =f"v{Version.version}" 
    program_build_date = str(Version.date)
    program_version_message = f'{program_name} ({program_version},{program_build_date})'
    tool = PDFTool.from_args()

    try:
        if tool.args.about:
                print(program_version_message)
                print(f"see {Version.doc_url}")
                webbrowser.open(Version.doc_url)
        if tool.args.serve:
                ws=WebServer()
                ws.run(tool.args)
        if tool.args.client:
                url=f"http://{tool.args.host}:{tool.args.port}"
                webbrowser.open(url)
        if tool.args.input:
            tool.split_booklet_style()
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 1
    except Exception as e:
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        if tool.args.debug:
            print(traceback.format_exc())
        return 2       
        
DEBUG = 1
if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-d")
    sys.exit(main())

if __name__ == "__main__":
    main()
