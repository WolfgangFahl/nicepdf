'''
Created on 2023-09-09

@author: wf
'''
import os
import sys
from PyPDF2 import PdfFileReader
from pdftool.pdftool_cmd import PDFTool, DoublePage,HalfPage,PdfFile
from tests.basetest import Basetest
import webbrowser

class TestPDFTool(Basetest):
    """
    test the PDF Tool
    """  
    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        
    def create_booklet(self,double_pages:int = 2):
        booklet_pdf_path=f"/tmp/example_booklet_{double_pages}.pdf"
        booklet_pdf=PdfFile(booklet_pdf_path)
        booklet_pdf.create_example_booklet(double_pages)
        self.show_debug(booklet_pdf_path)
        return booklet_pdf
        
    def show_debug(self,pdf_path:str):
        if self.debug:
            if sys.platform == "darwin":  # Darwin indicates macOS
                os.system(f"open {pdf_path}")
            else:
                # Fallback for other platforms, using webbrowser or another approach
                url = 'file://' + os.path.realpath(pdf_path)
                webbrowser.open(url)
                
            
    def check_split(self,pdf_file,expected_pages:int):
        # Creating an instance of the PDFTool class
        output_path=pdf_file.filename.replace(".pdf","_out.pdf")
        pdf_tool = PDFTool(pdf_file.filename, output_path, debug=self.debug)

        # Running the split function
        pdf_tool.split_booklet_style()
        self.show_debug(output_path)
        
        # Validations
        with open(output_path, "rb") as output_file:
            pdf = PdfFileReader(output_file)
            self.assertEqual(pdf.numPages, expected_pages)  # 2 double pages yield 4 single pages

    def test_double_pages(self):
        """
        test the double page /half_page creation code
        """
        expected=[4,1,2,3]
        double_pages=PdfFile.create_double_pages(2)
        if self.debug:
            for double_page in double_pages:
                print(double_page.left.page_num)
                print(double_page.right.page_num)
        for i,double_page in enumerate(double_pages):
            self.assertEquals(expected[2*i],double_page.left.page_num)
            self.assertEquals(expected[2*i+1],double_page.right.page_num)
                       
    def test_read_booklet(self):
        """
        Test the extract_half_pages method.
        """
        pdf_file=self.create_booklet()
        pdf_file.read_booklet()
      
        expected_indices = [4, 1, 2, 3]
        for idx, double_page in enumerate(pdf_file.double_pages):
            self.assertEquals(expected_indices[idx*2], double_page.left.page_num)
            self.assertEquals(expected_indices[idx*2 + 1], double_page.right.page_num)
      
    def test_split_booklet_style(self):
        """
        test even page booklet
        """
        for double_pages in range(2,4):
            booklet=self.create_booklet(double_pages)
            self.check_split(booklet,double_pages*2)