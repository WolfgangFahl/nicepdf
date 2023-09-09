'''
Created on 2023-09-09

@author: wf
'''
import os
import sys
import tempfile
from PyPDF2 import PdfFileReader, PdfFileWriter, PageObject
from pdftool.pdftool_cmd import PDFTool, PageInfo
from tests.basetest import Basetest
from reportlab.lib.pagesizes import A4
import webbrowser

class TestPDFTool(Basetest):
    """
    test the PDF Tool
    """
    
    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        # Create temporary directories and files
        self.tempdir = tempfile.TemporaryDirectory()
        self.input_path = os.path.join(self.tempdir.name, "dummy_input.pdf")
        self.output_path = os.path.join(self.tempdir.name, "dummy_output.pdf")

    def show_debug(self,pdf_path:str):
        if self.debug:
            if sys.platform == "darwin":  # Darwin indicates macOS
                os.system(f"open {pdf_path}")
            else:
                # Fallback for other platforms, using webbrowser or another approach
                url = 'file://' + os.path.realpath(pdf_path)
                webbrowser.open(url)
                
    def create_half_pages(self, double_pages:int) -> list:
        """
        create half pages in booklet style
        """
        page_objs = []
        total_pages = double_pages * 2
        for i in range(double_pages):
            # Add debug info to this blank page
            rotation = 90 if i % 2 == 1 else 0
            # Page numbering logic for booklet format
            if i == 0:
                left_page_number = total_pages
                right_page_number = 1
            else:
                left_page_number = i * 2
                right_page_number = left_page_number + 1
            page_objs.append(PageInfo(None, rotation, left_page_number))
            page_objs.append(PageInfo(None, rotation, right_page_number))
        return page_objs 
 
            
    def create_dummy_booklet_pdf(self, double_pages=3):
        """Creates a dummy booklet pdf with the specified number of double pages."""
        writer = PdfFileWriter()
        # Instantiate the PDFTool just for watermarking
        tool = PDFTool("", "")#
        height,width=A4 # landscape A4
        
        half_pages=self.create_half_pages(double_pages)
        

        for i in range(0, len(half_pages), 2):  # Iterate through the list by 2 steps
            # Create an empty double page of 'A4 landscape' size
            page = PageObject.createBlankPage(width=width, height=height)
    
            # Left half of the page
            left_page_info = half_pages[i]
            left_page = PageObject.createBlankPage(width=width/2, height=height)
            left_page = tool.add_debug_info(left_page, left_page_info.rotation, left_page_info.orig_index)
            page.mergeTranslatedPage(left_page, 0, 0)
    
            # Right half of the page
            right_page_info = half_pages[i+1]
            right_page = PageObject.createBlankPage(width=width/2, height=height)
            right_page = tool.add_debug_info(right_page, right_page_info.rotation, right_page_info.orig_index)
            page.mergeTranslatedPage(right_page, width/2, 0)
    
            writer.add_page(page)
        
        with open(self.input_path, "wb") as outf:
            writer.write(outf)
                
        self.show_debug(self.input_path)
            
    def check_split(self,expected_pages:int):
        # Creating an instance of the PDFTool class
        pdf_tool = PDFTool(self.input_path, self.output_path, debug=self.debug)

        # Running the split function
        pdf_tool.split_booklet_style()
        self.show_debug(self.output_path)
        
        # Validations
        with open(self.output_path, "rb") as output_file:
            pdf = PdfFileReader(output_file)
            self.assertEqual(pdf.numPages, expected_pages)  # 2 double pages yield 4 single pages

    def test_half_pages(self):
        """
        test the half page creation code
        """
        expected=[4,1,2,3]
        half_pages=self.create_half_pages(2)
        if self.debug:
            for half_page in half_pages:
                print(half_page.orig_index)
        for i,half_page in enumerate(half_pages):
            self.assertEquals(expected[i],half_page.orig_index)
                
    def test_split_booklet_style(self):
        """
        test even page booklet
        """
        for double_pages in range(2,4):
            self.create_dummy_booklet_pdf(double_pages=double_pages)
            self.check_split(double_pages*2)
  
    def tearDown(self):
        # Clean up the temporary directory
        self.tempdir.cleanup()

