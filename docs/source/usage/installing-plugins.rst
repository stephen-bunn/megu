Installing Plugins
==================

Plugins are stored as installed packages within a subdirectory in the plugin directory.
The subdirectory that these plugins are installed into defines the name of the plugin (not the package).

Take for example the following directory structure:

.. code-block:: text

   ~/.config/megu/plugins/
   └── megu_gfycat/                      # This is the plugin name
      ├── LICENSE
      ├── README.md
      ├── megu_gfycat/                   # Not this (this is the package name)
      │   ├── __init__.py
      │   ├── api.py
      │   ├── constants.py
      │   ├── guesswork.py
      │   ├── helpers.py
      │   ├── plugins/
      │   │   └── ...
      │   └── utils.py
      ├── megu_gfycat-0.1.0.dist-info/
      │   ├── INSTALLER
      │   ├── LICENSE
      │   ├── METADATA
      │   ├── RECORD
      │   ├── REQUESTED
      │   ├── WHEEL
      │   └── direct_url.json
      └── pyproject.toml


In this name of the the top-level ``megu_gfycat`` (within the ``plugins/`` directory) is the plugin name.
The nested ``megu_gfycat`` is the same name, but it refers to the installed package.

So installing plugins takes 2 steps:

1. Create a new directory within the plugin's folder.
2. Install a plugin package to the newly created plugin folder.

A helper method :func:`megu.plugin.manage.add_plugin` can automate this for you if you're not working in a containerized solution.
Behind the scenes, this method utilizes ``pip`` to install the given package to a newly created plugin directory using the same names as the given package URL.
Be sure to use URLs understood by ``pip`` if using this method.

.. code-block:: python

   from megu.plugin.manage import add_plugin

   add_plugin("git+https://github.com/stephen-bunn/megu-gfycat.git")


If you are working in a solution like Docker, you should be making use of the environment variable ``MEGU_PLUGIN_DIR`` to set a plugin directory and then use ``pip`` to install the desired package yourself.

.. code-block:: Docker

   ENV MEGU_PLUGIN_DIR=/.megu/plugins/
   RUN mkdir -p $MEGU_PLUGIN_DIR/megu_gfycat
   RUN python -m pip install --upgrade git+https://github.com/stephen-bunn/megu-gfycat.git --target $MEGU_PLUGIN_DIR/megu_gfycat


We include a fallback plugin :class:`megu.plugin.generic.GenericPlugin` that **assumes** the content can be fetched with a single resource using a single HTTP GET request.
If no plugins are provided, this generic plugin will always be used.
Of course, if it content can't be fetched using this naive approach, it will fail.
