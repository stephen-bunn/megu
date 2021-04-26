.. _configuration:
.. _appdirs: https://pypi.org/project/appdirs/

Configuration
=============

All configuration used internally by the tool is ready from the
:class:`~megu.config.MeguConfig` instance.
This object contains mostly metadata, and some unique temporary directory paths to
use for storing downloaded artifacts.

Within this config, there are three directories that can be overridden by environment
variables.

| ``MEGU_PLUGIN_DIR`` **The directory where plugins are stored.**
| By default this value is set to ``{user config dir}/megu/plugins``.
   The actual path to the user's config directory depends on the OS being used.
   Checkout appdirs_ for more information.

| ``MEGU_LOG_DIR`` **The directory where logs are stored.**
| By default this value is set to ``{user log dir}/megu``.
   The actual path to the user's log directory depends on the OS being used.
   Checkout appdirs_ for more information.

| ``MEGU_CACHE_DIR`` **The directory where persistent caches are stored.**
| By default this value is set to ``{user cache dir}/megu``
   The actual path to the user's cache directory depends on the OS being used.
   Checkout appdirs_ for more information.

