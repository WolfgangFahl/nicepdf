'''
Created on 2023-09-09

@author: wf
'''
'''
Created on 2023-06-19

@author: wf
'''
import pdftool

class Version(object):
    """
    Version handling for pdftool
    """
    name = "pdftool"
    version = pdftool.__version__
    date = '2023-09-07'
    updated = '2023-09-09'
    description = 'PDF manipulation tool',
    
    authors = 'Wolfgang Fahl'
    
    doc_url="https://wiki.bitplan.com/index.php/pdftool"
    chat_url="https://github.com/WolfgangFahl/pdftool/discussions"
    cm_url="https://github.com/WolfgangFahl/pdftool"

    license = f'''Copyright 2023 contributors. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.'''
    
    longDescription = f"""{name} version {version}
{description}

  Created by {authors} on {date} last updated {updated}"""


