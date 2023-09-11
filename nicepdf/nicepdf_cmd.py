from ngwidgets.cmd import WebserverCmd
import sys
from nicepdf.pdftool import PDFTool
from argparse import ArgumentParser
from nicepdf.version import Version
from nicepdf.webserver import WebServer

class NicePdfCmd(WebserverCmd):
    """
    Command line for NicePdf
    """
    def __init__(self):
        """
        """
        WebserverCmd.__init__(self, Version, WebServer, DEBUG)
        pass
    
    def getArgParser(self,description:str,version_msg)->ArgumentParser:
        description="Split a PDF booklet into individual pages."
        parser=super().getArgParser(description, version_msg)
        parser.add_argument("-o","--output", type=str, help="Path to the output PDF file.")
        parser.add_argument("-v", "--verbose", dest="debug", action="store_true", help="show verbose output [default: %(default)s]")
  
        return parser
    
    def cmd_main(self,argv:list=None):
        """
        command line main
        """
        exit_code=super().cmd_main(argv)
        if self.args.input and self.args.output:
            tool = PDFTool.from_args()
            if tool.args.input:
                tool.split_booklet_style()
            return exit_code
    
def main(argv:list=None):
    """
    main call
    """
    cmd=NicePdfCmd()
    exit_code=cmd.cmd_main(argv)
    return exit_code
        
DEBUG = 1
if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-d")
    sys.exit(main())