'''
Created on 15.09.2023

@author: wf
'''
#https://github.com/py-pdf/pypdf/issues/451
import copy

from pypdf import PdfReader, PdfWriter
from nicepdf.pdftool import PdfFile
from tests.basetest import Basetest
from pathlib import Path
from nicepdf.pdftool import DoublePage
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from io import BytesIO
  
class Testrotation(Basetest):
    """
    test the PDF roration
    
    """
    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.path = Path(__file__).parent.parent
         
    def test_rotation(self):   
        """
        test the rotation
        """ 
        example_path=self.path.joinpath("nicepdf_examples/example_booklet_2.pdf")
        reader = PdfReader(example_path)
        page = reader.pages[0]
        DoublePage.from_page(page,0,4)    
        
        writer = PdfWriter()
        for rotation in [0,90,180,270,360]:
            rotated = copy.copy(page)
            # pypdf.errors.DeprecationError: rotateClockwise is deprecated and was removed in pypdf 3.0.0. Use rotate instead.
            # rotated.rotateClockwise(rotation)
            rotated.rotate(rotation)
            writer.add_page(rotated)
        
        with open("/tmp/rotated_output.pdf", "wb") as f:
            writer.write(f)
            
