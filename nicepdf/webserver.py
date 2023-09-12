"""
Created on 2023-09-09

@author: wf
"""
from nicegui import ui, Client
import os
from nicepdf.version import Version
from ngwidgets.file_selector import FileSelector
from ngwidgets.input_webserver import InputWebserver
from ngwidgets.webserver import WebserverConfig
from scipy.constants._constants import arcminute

class WebServer(InputWebserver):
    """
    WebServer class that manages the server 
    
    """

    def __init__(self):
        """Constructs all the necessary attributes for the WebServer object."""
        copy_right="(c)2023 Wolfgang Fahl"
        config=WebserverConfig(copy_right=copy_right,version=Version())
        InputWebserver.__init__(self,config=config)
         
        @ui.page('/')
        async def home(client: Client):
            return await self.home(client)
             
    async def home(self, client:Client):
        """Generates the home page with a pdf view"""
        self.setup_menu()
        with ui.element("div").classes("w-full"):
            with ui.splitter() as splitter:
                with splitter.before:
                    self.example_selector=FileSelector(path=self.root_path,handler=self.read_and_optionally_render)
                    self.input_input=ui.input(
                         value=self.input,
                         on_change=self.input_changed).props("size=100")
                    self.tool_button(tooltip="reload",icon="refresh",handler=self.reload_file)    
                    if self.is_local:
                        self.tool_button(tooltip="open",icon="file_open",handler=self.open_file)
                with splitter.after:
                    self.pdf_desc=ui.html("")
            with ui.splitter() as splitter:
                with splitter.before:
                    self.pdf_booklet_view=ui.html("pdf booklet")
                with splitter.after as self.video_container:
                    self.pdf_split_view=ui.html("pdf_split")
        slider_props='label-always'
        self.page_slider = ui.slider(min=0, max=100, step=1, value=50,on_change=lambda e: self.mark_trackpoint_at_index(e.value))        .props(slider_props)
   
        self.setup_footer()