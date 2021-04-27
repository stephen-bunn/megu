.. _plugins:

=======
Plugins
=======

The following documentation will help to inform you how to write plugins that work well with this framework.
Plugins have 3 main concerns:

1. Determining if they can handle a given URL.
2. Generating :class:`~megu.models.content.Content` instances from a given URL.
3. Merging :class:`~megu.models.content.Manifest` artifacts into a single file.

On top of this, plugin packages should be all installable via ``pip`` if you want them to include other dependencies or to be automatically installable through the CLI.

We will cover how plugins handle each of these concerns, but first there are a few general rules to keep in mind.

.. include:: rules.rst

.. include:: writing-plugins.rst

.. include:: helpers.rst

.. include:: examples.rst

----

For more examples on what helpers you can make use of in your plugins, checkout the :mod:`megu.helpers` module.
Since plugins should all be installable, you can also include additional dependencies that get installed through setuptools.
