'''
Created on 2023-09-09

@author: wf
'''
import os
import sys
from pypdf import PdfReader
from nicepdf.pdftool import PDFTool,PdfFile
from tests.basetest import Basetest
import webbrowser

class TestPDFTool(Basetest):
    """
    test the PDF Tool
    """  
    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        
    def create_booklet(self,double_pages:int = 2,postfix="",do_rotate:bool=False):
        """
        create a booklet
        """
        booklet_pdf_path=f"/tmp/example_booklet_{double_pages}{postfix}.pdf"
        booklet_pdf=PdfFile(booklet_pdf_path)
        booklet_pdf.create_example_booklet(double_pages,with_random_rotation=do_rotate)
        booklet_pdf.open()
        self.show_debug(booklet_pdf_path)
        return booklet_pdf
        
    def show_debug(self,pdf_path:str):
        """
        optionally show the pdf_file at the given file
        """
        if self.debug:
            if sys.platform == "darwin":  # Darwin indicates macOS
                os.system(f"open {pdf_path}")
            else:
                # Fallback for other platforms, using webbrowser or another approach
                url = 'file://' + os.path.realpath(pdf_path)
                webbrowser.open(url)
                
            
    def check_split(self,pdf_file,expected_pages:int):
        """
        check the split of the given pdf_file
        """
        # Creating an instance of the PDFTool class
        output_path=pdf_file.filename.replace(".pdf","_out.pdf")
        pdf_tool = PDFTool(pdf_file.filename, output_path, debug=self.debug)

        # Running the split function
        pdf_tool.split_booklet_style()
        self.show_debug(output_path)
        
        # Validations
        with open(output_path, "rb") as output_file:
            pdf = PdfReader(output_file)
            self.assertEqual(len(pdf.pages), expected_pages)  # 2 double pages yield 4 single pages

    def test_double_pages(self):
        """
        test the double page /half_page creation code
        """
        test_cases=[
            (4,[4,1,2,3]),
            (100,[100,1,2,99,98,3,4,97])
        ]
        for pages,expected in test_cases:
            double_pages=PdfFile.create_double_pages(pages//2)
            if self.debug:
                for double_page in double_pages:
                    print(double_page.left.page_num)
                    print(double_page.right.page_num)
            for i,double_page in enumerate(double_pages):
                if 2*i+1<len(expected):
                    self.assertEquals(expected[2*i],double_page.left.page_num)
                    self.assertEquals(expected[2*i+1],double_page.right.page_num)
                           
    def test_read_booklet(self):
        """
        Test the read_booklet method
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
        for do_rotate in [True,False]:
            postfix="_rot" if do_rotate else "" 
            for double_pages in range(2,8,2):
                booklet=self.create_booklet(double_pages,postfix=postfix,do_rotate=do_rotate)
                self.check_split(booklet,double_pages*2)