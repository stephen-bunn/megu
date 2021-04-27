# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""An invalid plugin.

Because this plugin contains no exports that are subclasses of BasePlugin, this
module should contain no usable plugins in discovery.
"""


class MeguTestPlugin(object):
    ...
