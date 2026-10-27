"""Start investaround from a plain script, e.g. Wing's main entry point.

Running ``investaround/__main__.py`` directly fails on its relative
imports; this launcher imports the package properly.  Same options as
``python -m investaround``.
"""

from investaround.__main__ import main

if __name__ == "__main__":
    main()
