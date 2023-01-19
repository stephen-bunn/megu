Fetching Content
================

There are 6 steps to fetching content from a URL to the local filesystem in this framework:

1. Discover the plugin best suited to get content from a given URL.
2. Iterate over available content from a given URL using the discovered plugin.
3. Filter down what content should be fetched.
4. Get the best suited downloader for the filtered content.
5. Download the content using the downloader to produce a manifest of artifacts.
6. Merge the downloaded manifest of artifacts to reproduce the content from the given URL.

We provide a module :mod:`megu.services` which exposes some helpful functions to reduce the boilerplate necessary to implement each of these steps.

Plugin Discovery
~~~~~~~~~~~~~~~~

To discover the best plugin to handle a given URL, you can use the :func:`~megu.services.get_plugin` function.
Depending on what plugins you have available, it will attempt to eagerly determine if a plugin can handle the given URL.
Otherwise, this function will provide the fallback :class:`megu.plugin.generic.GenericPlugin` instance as the *best suited* plugin.

.. code-block:: python

   from megu.services import get_plugin

   URL = "https://gfycat.com/pepperyvictoriousgalah-wonder-woman-1984-i-like-to-party"

   plugin = get_plugin(URL)
   # If megu-gfycat is installed, will return "Gfycat Basic" plugin
   # Otherwise, will return "Generic Plugin"


Content Iteration
~~~~~~~~~~~~~~~~~

Now that you have the best plugin for the given URL, you need to invoke the plugin's extraction logic to get :class:`~megu.models.content.Content` entries that can be downloaded.
You can use the :func:`~megu.services.iter_content` iterator to invoke a plugin with a URL.

.. code-block:: python

   from megu.services import iter_content

   for content in iter_content(URL, plugin):
      ...
      # iterates over available content from the given URL as lazily as possible

This iterator will yield all content extracted by the plugin within the for loop.
These content entries *may* be many instances of the same content using different qualities.
To reduce what content is handled, we need to filter the results down a bit.

Content Filtering
~~~~~~~~~~~~~~~~~

Filtering content can be done using the functions provided in the :mod:`megu.filters` module.
The most simple :func:`~megu.filters.best_content` filter will only take unique content with the highest indicated quality.
This filter can be applied directly to the call of ``iter_content`` to reduce any required nesting.

.. code-block:: python

   from megu.services import iter_content
   from megu.filters import best_content

   for content in best_content(iter_content(URL, plugin)):
      ...
      # filters out content from the content iterator

Note that in order to determine which content is the best, this filter is greedy with the ``iter_content`` generator.

Downloader Discovery
~~~~~~~~~~~~~~~~~~~~

With the content extracted from the plugin, we need to get the best suited downloader for the content.
You can use the :func:`~megu.services.get_downloader` to get the most appropriate downloader.

.. code-block:: python

   from megu.services import get_downloader

   downloader = get_downloader(content)

The downloader is determined by the type of resources specified by the content.
By default, this downloader will fallback to the :class:`~megu.download.http.HttpDownloader` if no downloader can handle the given content.

Content Download
~~~~~~~~~~~~~~~~

The provided downloaders will produce a :class:`~megu.models.content.Manifest` instance.
Otherwise, downloading the content can be done right from the :meth:`~megu.download.base.BaseDownloader.download_content` method.

.. code-block:: python

   manifest = downloader.download_content(content)


Manifest Merge
~~~~~~~~~~~~~~

The final step is to merge the downloaded manifest to a file path.
You can use the :func:`~megu.services.merge_manifest` function to help you.
Note that this step is a *little* weird as the plugin actually provides the manifest merging functionality.
For this purpose, we need to provide the ``plugin`` instance back into the function along with the fetched manifest.

.. code-block:: python

   from megu.services import merge_manifest

   merge_manifest(plugin, manifest, Path("~/Downloads/", content.filename).expanduser())


Altogether, the full content fetching script can be written as the following:

.. code-block:: python

   from pathlib import Path
   from megu.services import get_plugin, get_downloader, iter_content, merge_manifest
   from megu.filters import best_content

   URL = "https://gfycat.com/pepperyvictoriousgalah-wonder-woman-1984-i-like-to-party"

   plugin = get_plugin(URL)
   for content in best_content(iter_content(URL, plugin)):
       downloader = get_downloader(content)
       manifest = downloader.download_content(content)
       to_path = merge_manifest(
          plugin,
          manifest,
          Path("~/Downloads/", content.filename).expanduser()
       )
       print(f"Downloaded {content.id} to {to_path}")


This of course is skipping over any kind of content de-duplication and checking if the content is already present or cached on the local filesystem.
But, this is pretty lightweight solution for fetching content from a given URL using this framework.
