"""
Created on 2023-09-09

@author: wf
"""

from dataclasses import dataclass

import nicepdf


@dataclass
class Version:
    """
    Version handling for nicepdf
    """

    name = "nicepdf"
    version = nicepdf.__version__
    date = "2023-09-07"
    updated = "2024-05-21"
    description = "PDF manipulation tool - e.g. booklet conversion/posterizing"

    authors = "Wolfgang Fahl"

    doc_url = "https://wiki.bitplan.com/index.php/nicepdf"
    chat_url = "https://github.com/WolfgangFahl/nicepdf/discussions"
    cm_url = "https://github.com/WolfgangFahl/nicepdf"

    license = f"""Copyright 2023-2024 contributors. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied."""

    longDescription = f"""{name} version {version}
{description}

  Created by {authors} on {date} last updated {updated}"""
