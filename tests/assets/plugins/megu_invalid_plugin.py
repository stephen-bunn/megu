# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""An invalid plugin.

Because this plugin contains no exports that are subclasses of BasePlugin, this
module should contain no usable plugins in discovery.
"""


class MeguTestPlugin(object):
    ...
