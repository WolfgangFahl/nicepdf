"""
Created on 2023-09-12

@author: wf
"""

import dataclasses
import json

from ngwidgets.basetest import Basetest

from nicepdf.version import Version


class TestVersion(Basetest):
    """
    test the version dataclass
    """

    def test_version(self):
        """
        test the version handling
        """
        version = Version()
        debug = True
        version_dict = dataclasses.asdict(version)
        version_json = json.dumps(version_dict, indent=2)
        if debug:
            print(version_json)
