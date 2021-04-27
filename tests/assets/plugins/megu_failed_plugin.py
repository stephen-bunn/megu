# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""A failed plugin.

This plugin should be completely skipped in plugin discovery.
Since importing this plugin fails, there should be no trace of it in discovery.
"""

raise RuntimeError("Forceful failure when imported")
