"""
Created on 2023-09-09

@author: wf
"""
from typing import Optional
from nicegui import ui, Client
from ngwidgets.webserver import NiceGuiWebserver
import os
from nicepdf.version import Version


class WebServer(NiceGuiWebserver):
    """
    WebServer class that manages the server 
    
    """

    def __init__(self):
        """Constructs all the necessary attributes for the WebServer object."""
        self.is_local=False
         
        @ui.page('/')
        async def home(client: Client):
            return await self.home(client)
    
        
    def setup_menu(self):
        """Adds a link to the project's GitHub page in the web server's menu."""
        with ui.header() as self.header:
            self.link_button("home","/","home")
            self.link_button("github",Version.cm_url,"bug_report")
            self.link_button("chat",Version.chat_url,"chat")
            self.link_button("help",Version.doc_url,"help")
    
    def setup_footer(self):
        """
        setup the footer
        """
        with ui.footer() as self.footer:
            ui.label("(c)2023 Wolfgang Fahl")
            ui.link("Powered by nicegui","https://nicegui.io/").style("color: #fff") 
          
    async def home(self, client:Client):
        """Generates the home page with a pdf view"""
        self.setup_menu()
        self.setup_footer()
       
    def run(self, args):
        """Runs the UI of the web server.

        Args:
            args (list): The command line arguments.
        """
        self.args=args
        self.input=args.input
        self.is_local=args.local
        self.root_path=os.path.abspath(args.root_path) 
        self.render_on_load=args.render_on_load
        ui.run(title=Version.name, host=args.host, port=args.port, show=args.client,reload=False)
