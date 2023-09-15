'''
Created on 2023-09-07

@author: wf
'''
from pypdf import PageObject,PdfReader, PdfWriter, Transformation
from copy import copy
from dataclasses import dataclass
from reportlab.pdfgen import canvas
from reportlab.lib import colors, pagesizes
from reportlab.lib.units import mm
from io import BytesIO
import os
import random
from ngwidgets.progress import Progressbar, TqdmProgressbar

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
    def save_page(self,page,file_path:str):
        """
        save a single given page to the givne file path
        """
        writer=PdfWriter()
        writer.add_page(page)
        with open(file_path, "wb") as output_file:
            writer.write(output_file)

    @classmethod 
    def copy_page(cls,page,width,height,tx,ty):
        """
        get a copy of the given page 
        """
        new_page = PageObject.create_blank_page(pdf=None, width=width, height=height)
        # Get the rotation of the original page
        rotation = page.get('/Rotate', 0)
        rotated_page=copy(page)
        if rotation!=0:
            rotated_page.rotate(-rotation)
        pass
        rotated_page.add_transformation(Transformation().translate(tx, ty))
        # doesn't work as expected
        new_page.merge_page(rotated_page)
        return new_page
    
    @classmethod
    def calculate_booklet_page_numbers(cls, index: int, total_pages: int, from_binder: bool):
        """
        Calculate the left and right page numbers based on the current index, 
        total pages, and scanning method.
    
        For total_pages=100:
        - Standard scanning (not from binder):
          - Even indices: 0 => (100, 1), 2 => (98, 3), 4 => (96, 5) ...
          - Odd indices: 1 => (2, 99), 3 => (4, 97) ...
        - Scanning from the binder:
          - Even indices: 0 => (50, 51), 2 => (48, 53), 4 => (46, 55) ...
          - Odd indices: 1 => (52, 49), 3 => (54, 47), 5=>(56,45) ...

        For total_pages=8:
        - Standard scanning (not from binder):
          - Even indices: 0 => (8, 1), 2 => (6, 3)
          - Odd indices: 1 => (2, 7), 3 => (4, 5)
    
        - Scanning from the binder:
          - Even indices: 0 => (4, 5), 2 => (2, 7)
          - Odd indices: 1 => (6, 3), 3 => (8, 1)
        """ 
        mid = total_pages//2  # Finding the middle of the booklet
        
        if from_binder:
            if index % 2 == 0:  # even index (0-based)
                left_num = mid - index
                right_num = mid + index +1
            else:
                left_num = mid + index +1
                right_num = mid - index 
        else:
            if index % 2 == 0:  # even index (0-based)
                left_num = total_pages - index
                right_num = index + 1
            else:
                left_num = index + 1
                right_num = total_pages - index
    
        return left_num, right_num

    @classmethod
    def from_page(cls, page, index, total_pages,from_binder:bool=False,debug:bool=False):
        # Get the rotation of the original page
        rotation = page.get('/Rotate', 0)
        width = page.mediabox.width
        height = page.mediabox.height
        a4_height, a4_width = pagesizes.A4  # Landscape A4
        if height>width and rotation==0:
            print(f"Rotation missing for page {index}") 
        rotated_page = cls.copy_page(page=page,width=a4_width, height=a4_height,tx=0,ty=0)
        if debug:
            file_path=f"/tmp/debug-{index}.pdf"
            cls.save_page(rotated_page, file_path)
        
        # Create two new blank pages with half the width of the original
    
        left_half = cls.copy_page(page=rotated_page,width=a4_width/2, height=a4_height,tx=0,ty=0)
        right_half = cls.copy_page(page=rotated_page,width=a4_width/2, height=a4_height,tx=-a4_width/2, ty=0)
    
        # Calculate booklet page numbers
        left_num, right_num = cls.calculate_booklet_page_numbers(index, total_pages, from_binder)
    
        # Create HalfPage instances for each half
        left = HalfPage(page_num=left_num, page=left_half)
        right = HalfPage(page_num=right_num, page=right_half)
    
        # Return a DoublePage instance
        return cls(page=page, rotation=rotation, left=left, right=right, page_index=index)

        
    def rotation_symbol(self)->str:
        """
        return a symbol for the rotation of this page
        """
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
            
    def save(self,writer):
        with open(self.filename, "wb") as output_file:
            writer.write(output_file)
        
    def close(self):
        if self.file_obj:
            self.file_obj.close()

    def read_booklet(self,from_binder:bool=False,progress_bar=None,debug:bool=False):
        """
        read min input as a booklet
        """
        self.double_pages = []
        double_page_count = len(self.reader.pages)
        if progress_bar:
            # Change the description of the progress bar
            progress_bar.set_description("Splitting pages")
        
        for i in range(double_page_count):
            page = self.reader.pages[i]
            double_page = DoublePage.from_page(page, i, double_page_count * 2,from_binder=from_binder,debug=debug)
            self.double_pages.append(double_page)
            if progress_bar:
                # Update the progress bar
                progress_bar.update(1)

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
    
    @classmethod
    def draw_centered_rectangle(cls,canvas, large_width, large_height, margin, fill=0):
        """Draw a centered smaller rectangle within a larger rectangle after reducing its size by a given margin."""
        small_width = large_width - 2 * margin
        small_height = large_height - 2 * margin
        x = (large_width - small_width) / 2
        y = (large_height - small_height) / 2
        canvas.rect(x, y, small_width, small_height, fill=fill)
        
    @classmethod
    def draw_double_page_with_margin(cls,c, page_width, page_height, margin):
        """Draw two centered rectangles (representing pages) side-by-side with a given margin."""
        half_width = page_width / 2
    
        # Draw left rectangle
        cls.draw_centered_rectangle(c, half_width, page_height, margin)
    
        # Move to right side and draw right rectangle
        c.translate(half_width, 0)
        cls.draw_centered_rectangle(c, half_width, page_height, margin)
        
        # Reset translation for next iteration
        c.translate(-half_width, 0)

    def create_double_page_with_numbers(self, left_page_number, right_page_number, inner_margin=5*mm, font_size=240):
        """Generate a double PDF page with the given page numbers."""
        buffer = BytesIO()

        a4_landscape = pagesizes.landscape(pagesizes.A4)
        
        c = canvas.Canvas(buffer, pagesize=a4_landscape)

        # Drawing the two centered rectangles side-by-side
        self.draw_double_page_with_margin(c, *a4_landscape, inner_margin)
        
        # Placing numbers in the center of the rectangles
        vertical_adjustment = font_size / 3.5  # Adjust based on the specific font metrics
        half_width = a4_landscape[0] / 2

        c.setFont("Helvetica-Bold", font_size)
        c.drawCentredString(half_width / 2, a4_landscape[1] / 2 - vertical_adjustment, str(left_page_number))
        c.drawCentredString(1.5 * half_width, a4_landscape[1] / 2 - vertical_adjustment, str(right_page_number))

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
        self.save(writer)

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
        self.from_binder=False
        
    def get_total_steps(self)->int:
        """
        get the number of steps to be performed
        
        e.g. for 50 pages there are 150 steps:
        
        50 x extraction of left and half
        50 x writing left pages
        50 x writing right pages
        """
        total_steps=3*len(self.input_file.reader.pages)
        return total_steps
    
    def split_booklet_style(self,progress_bar:Progressbar=None) -> None:
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
        if progress_bar is None:
            total_steps=self.get_total_steps()
            progress_bar=TqdmProgressbar(total=total_steps, desc="Processing all pages", unit="step")
        self.progress_bar = progress_bar

        self.input_file.read_booklet(from_binder=self.from_binder,progress_bar=self.progress_bar,debug=self.debug)
        # Change the description
        self.progress_bar.set_description("reordering pages")
        self.input_file.un_booklet()
    
        writer=PdfWriter()

        page_nums=sorted(list(self.input_file.pages.keys()))
        self.progress_bar.set_description("writing pages")
        for page_num in page_nums:
            half_page=self.input_file.pages[page_num]
            if self.debug:
                page = half_page.add_debug_info()  
                writer.add_page(page)
            else:
                writer.add_page(half_page.page)
            # Update the progress bar
            self.progress_bar.update(1)
    
        if self.verbose:
            print(f"\nOutput at {self.output_file.filename}")
    
        with open(self.output_file.filename, "wb") as output_file:
            writer.write(output_file)
            
        self.input_file.close()
    
    @classmethod
    def from_args(cls,args):
        """
        Instantiate PDFTool from command-line arguments.
        """
        tool=cls(args.input, args.output, args.debug)
        tool.args=args
        tool.verbose=args.verbose
        tool.from_binder=args.from_binder
        return tool