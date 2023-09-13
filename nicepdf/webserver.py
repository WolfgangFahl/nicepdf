"""
Created on 2023-09-09

@author: wf
"""
from nicegui import app, ui, Client
from nicepdf.version import Version
from ngwidgets.file_selector import FileSelector
from ngwidgets.input_webserver import InputWebserver
from ngwidgets.progress import NiceguiProgressbar
from ngwidgets.webserver import WebserverConfig
from ngwidgets.background import BackgroundTaskHandler
from nicepdf.pdftool import PDFTool
import os

class WebServer(InputWebserver):
    """
    WebServer class that manages the server 
    
    """

    def __init__(self):
        """Constructs all the necessary attributes for the WebServer object."""
        copy_right="(c)2023 Wolfgang Fahl"
        config=WebserverConfig(copy_right=copy_right,version=Version())
        InputWebserver.__init__(self,config=config)
        self.input_source=None
        self.output_path=None
        self.bth=BackgroundTaskHandler()
        app.on_shutdown(self.bth.cleanup())
        self.future=None
         
        @ui.page('/')
        async def home(client: Client):
            return await self.home(client)
        
    def on_page_change(self,page_num:int):  
        """
        switch to the given page
        """
        pass
    
    def update_progress(self):
        """
        """
        self.progressbar.update(1)
    
    async def unbooklet(self):
        """
        convert the booklet pdf to a plain pdf
        """
        if self.input_source:
            pdftool=PDFTool(self.input_source,self.output_path)
            pdftool.from_binder=True
            if self.future:
                self.future.cancel()
            self.future, result_coro = self.bth.execute_in_background(pdftool.split_booklet_style, progress_bar=self.progressbar)
            await result_coro()
            await self.render()
            
    def show_pdf(self,view,file_path):
        """
        show the given pdf in the given ui.html view
        """
        if os.path.exists(file_path):
            url= app.add_static_file(local_file=file_path)
            html=f'<embed src="{url}" type="application/pdf" width="100%" height="100%">'
        else:   
            html="-" 
        view.content=html
            
    async def render(self, _click_args=None):
        """
        render my pdf file
        """
        try:
            self.input_source=self.input
            ui.notify(f"rendering {self.input_source}")
            self.show_pdf(self.pdf_booklet_view, self.input)
            self.output_path=self.input.replace(".pdf","-A4.pdf")
            self.show_pdf(self.pdf_split_view, self.output_path)
                
        except BaseException as ex:
            self.handle_exception(ex,self.do_trace)    
             
    async def home(self, client:Client):
        """Generates the home page with a pdf view"""
        self.setup_menu()
        with ui.element("div").classes("w-full h-full"):
            with ui.splitter() as splitter:
                with splitter.before:
                    extensions = {"pdf": ".pdf"}
                    self.pdf_selector=FileSelector(path=self.root_path,extensions=extensions,handler=self.read_and_optionally_render)
                    self.input_input=ui.input(
                         value=self.input,
                         on_change=self.input_changed).props("size=100")
                    self.tool_button(tooltip="reload",icon="refresh",handler=self.reload_file)    
                    self.tool_button(tooltip="un-booklet",icon="import_contacts",handler=self.unbooklet)    
                    if self.is_local:
                        self.tool_button(tooltip="open",icon="file_open",handler=self.open_file)    
                with splitter.after:
                    self.pdf_desc=ui.html("")
            self.progressbar = NiceguiProgressbar(100,"work on PDF pages","steps")
            slider_props='label-always'
            self.page_slider = ui.slider(min=0, max=100, step=1, value=50,on_change=lambda e: self.on_page_change(e.value)).props(slider_props)
        
            with ui.splitter() as splitter:
                with splitter.before:
                    self.pdf_booklet_view=ui.html("pdf booklet").classes("w-full h-screen")
                with splitter.after as self.pdf_container:
                    self.pdf_split_view=ui.html("pdf_split").classes("w-full h-screen")
      
        await self.setup_footer()