from ngwidgets.cmd import WebserverCmd
import sys
from nicepdf.pdftool import PDFTool
from argparse import ArgumentParser
from nicepdf.webserver import WebServer

class NicePdfCmd(WebserverCmd):
    """
    Command line for NicePdf
    """
    def __init__(self):
        """
        constructor
        """
        config=WebServer.get_config()
        WebserverCmd.__init__(self, config, WebServer, DEBUG)
        pass
    
    def getArgParser(self,description:str,version_msg)->ArgumentParser:
        """
        override the default argparser call
        """        
        parser=super().getArgParser(description, version_msg)
        parser.add_argument("-o","--output", type=str, help="Path to the output PDF file.")
        parser.add_argument("-v", "--verbose", action="store_true", help="show verbose output [default: %(default)s]")
        parser.add_argument("-rp", "--root_path",default=WebServer.examples_path(),help="path to pdf files [default: %(default)s]")
        parser.add_argument("-r", "--from_binder", action="store_true", help="Handle case when pages have been scanned in reverse order starting with the middle pages from the binder.")
        return parser
    
    def cmd_main(self,argv:list=None):
        """
        command line main
        """
        exit_code=super().cmd_main(argv)
        if self.args.input and self.args.output:
            tool = PDFTool.from_args(self.args)
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
        
DEBUG = 0
if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-d")
    sys.exit(main())