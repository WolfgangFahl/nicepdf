"""
Created on 2023-09-09

@author: wf
"""

import os

from ngwidgets.file_selector import FileSelector
from ngwidgets.input_webserver import InputWebserver, InputWebSolution
from ngwidgets.progress import NiceguiProgressbar
from ngwidgets.webserver import WebserverConfig
from nicegui import Client, app, run, ui

from nicepdf.pdftool import PDFTool
from nicepdf.version import Version


class NicePdfWebServer(InputWebserver):
    """
    WebServer for NicePdf

    """

    @classmethod
    def get_config(cls) -> WebserverConfig:
        copy_right = "(c)2023-2024 Wolfgang Fahl"
        config = WebserverConfig(
            copy_right=copy_right,
            version=Version(),
            short_name="nicepdf",
            default_port=9861,
        )
        server_config = WebserverConfig.get(config)
        server_config.solution_class = NicePdfSolution
        return server_config

    def __init__(self):
        """Constructs all the necessary attributes for the WebServer object."""
        InputWebserver.__init__(self, config=NicePdfWebServer.get_config())

    @classmethod
    def examples_path(cls) -> str:
        # the root directory (default: examples)
        path = os.path.join(os.path.dirname(__file__), "../nicepdf_examples")
        path = os.path.abspath(path)
        return path

    def configure_run(self):
        super(NicePdfWebServer, self).configure_run()
        self.from_binder = self.args.from_binder
        self.allowed_urls = [self.examples_path(), self.root_path]


class NicePdfSolution(InputWebSolution):
    """
    NicePdf Solution
    """

    def __init__(self, webserver: NicePdfWebServer, client: Client):
        """
        Initialize the NicePdfSolution.

        Args:
            webserver (NicePdfWebserver): The webserver instance associated with this context.
            client (Client): The client instance this context is associated with.
        """
        super().__init__(webserver, client)  # Call to the superclass constructor
        self.input_source = None
        self.output_path = None
        self.allowed_urls = self.webserver.allowed_urls
        self.from_binder = self.webserver.from_binder

    def configure_settings(self):
        """
        add additional settings
        """
        ui.checkbox("from binder", value=self.from_binder).bind_value(
            self, "from_binder"
        )

    def on_page_change(self, page_num: int):
        """
        switch to the given page
        """
        pass

    def update_progress(self):
        """ """
        self.progressbar.update(1)

    async def unbooklet(self):
        """
        convert the booklet pdf to a plain pdf
        """
        if self.input_source:
            pdftool = PDFTool(self.input_source, self.output_path, debug=self.debug)
            pdftool.from_binder = self.from_binder
            self.progressbar.total = pdftool.get_total_steps()
            self.progressbar.reset()
            await run.io_bound(pdftool.split_booklet_style, self.progressbar)
            await self.render()

    async def poster(self):
        """
        create a poster
        """
        self.poster_path = self.input.replace(".pdf", f"-poster.pdf")
        pdftool = PDFTool(self.input_source, self.poster_path, debug=self.debug)
        pdftool.poster()
        self.show_pdf(self.pdf_split_view, self.poster_path)

    def show_pdf(self, view, file_path):
        """
        show the given pdf in the given ui.html view
        """
        if os.path.exists(file_path):
            url = app.add_static_file(local_file=file_path)
            html = (
                f'<embed src="{url}" type="application/pdf" width="100%" height="100%">'
            )
        else:
            html = "-"
        view.content = html

    async def render(self, _click_args=None):
        """
        render my pdf file
        """
        try:
            self.input_source = self.input
            ui.notify(f"rendering {self.input_source}")
            self.show_pdf(self.pdf_booklet_view, self.input)
            debug_suffix = "_debug" if self.debug else ""
            self.output_path = self.input.replace(".pdf", f"-A4{debug_suffix}.pdf")

            self.show_pdf(self.pdf_split_view, self.output_path)

        except BaseException as ex:
            self.solution.handle_exception(ex)

    async def home(self):
        """
        Generates the home page with a pdf view
        """

        def show():
            with ui.splitter() as splitter:
                with splitter.before:
                    extensions = {"pdf": ".pdf"}
                    filter_func = lambda item_name: not ("-A4" in item_name)
                    self.pdf_selector = FileSelector(
                        path=self.root_path,
                        extensions=extensions,
                        handler=self.read_and_optionally_render,
                        filter_func=filter_func,
                    )
                    self.input_input = ui.input(
                        value=self.input, on_change=self.input_changed
                    ).props("size=100")
                    with ui.row():
                        self.tool_button(
                            tooltip="reload", icon="refresh", handler=self.reload_file
                        )
                        self.tool_button(
                            tooltip="poster",
                            icon="insert_page_break",
                            handler=self.poster,
                        )
                        self.tool_button(
                            tooltip="un-booklet",
                            icon="import_contacts",
                            handler=self.unbooklet,
                        )
                        if self.is_local:
                            self.tool_button(
                                tooltip="open", icon="file_open", handler=self.open_file
                            )
                with splitter.after:
                    self.pdf_desc = ui.html("")
            slider_props = "label-always"
            self.page_slider = ui.slider(
                min=0,
                max=100,
                step=1,
                value=50,
                on_change=lambda e: self.on_page_change(e.value),
            ).props(slider_props)
            self.progressbar = NiceguiProgressbar(100, "work on PDF pages", "steps")

            with ui.splitter() as splitter:
                with splitter.before:
                    self.pdf_booklet_view = ui.html("pdf booklet").classes(
                        "w-full h-screen"
                    )
                with splitter.after as self.pdf_container:
                    self.pdf_split_view = ui.html("pdf_split").classes(
                        "w-full h-screen"
                    )

        await self.setup_content_div(show)
