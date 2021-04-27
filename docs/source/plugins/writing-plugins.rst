Writing Plugins
===============

Plugins are built as subclasses of :class:`~megu.plugin.base.BasePlugin`.
So all plugin packages will need to have ``megu`` as a dependency at the very least.

For the following sections, I will be covering how to write an extremely basic plugin to extract media from posts in 4chan threads (since it's relatively straightforward).

The first thing we need is to define a subclass of ``BasePlugin``.

.. code-block:: python

   from megu import BasePlugin

   class ThreadPlugin(BasePlugin):
      ...


Plugin Name
~~~~~~~~~~~

The ``name`` property is required for all plugins.
It should be unique, human-friendly, and fully descriptive of the source the plugin handles.

In our case, we are created a 4chan thread plugin.

.. code-block:: python

   class ThreadPlugin(BasePlugin):

      name = "4chan Thread"


This property will be used for rendering of plugin information both in the framework as well as the CLI.

Domain Set
~~~~~~~~~~

The ``domains`` set is required for all plugins.
This is a :class:`~typing.Set` of strings of **ALL** subdomains that should be handled by the plugin.
If a given URL's domain is not present in this set, the plugin will not be used to handle that URL.

.. code-block:: python

   class ThreadPlugin(BasePlugin):

      name = "4chan Thread"
      domains = {"boards.4chan.org", "boards.4channel.org"}

Can Handle
~~~~~~~~~~

The :meth:`~megu.plugin.base.BasePlugin.can_handle` method is required and should take a :class:`~megu.models.types.Url` instance.
If the plugin can handle the URL, it should return a boolean True.
Otherwise, it should always return False.

.. code-block:: python

   class ThreadPlugin(BasePlugin):

      name = "4chan Thread"
      domains = {"boards.4chan.org", "boards.4channel.org"}
      pattern = re.compile(r"^https?:\/\/(?:(?:www|boards)\.)?4chan(?:nel)?\.org\/(?P<board>\w+)\/thread\/(?P<thread>\d+)")

      def can_handle(self, url: Url) -> bool:
         return self.pattern.match(url.url) is not None

Extract Content
~~~~~~~~~~~~~~~

Extracting content is the bulk of the functionality that should be provided by the plugin.
The goal of this method is to yield fully constructed :class:`~megu.models.content.Content` instances for the framework to handle.
This functionality should be exposed through the :meth:`~megu.plugin.base.BasePlugin.extract_content` method.

.. code-block:: python

   def extract_content(self, url: Url) -> Generator[Content, None, None]:
      ...

To "fail" the extraction of content, simply raise a :class:`ValueError` at any point.

.. code-block:: python

   def extract_content(self, url):
      match = self.pattern.match(url.url)
      if not match:
         raise ValueError(f"Failed to match url {url.url}")

In order to fetch information about what data is available from a given 4chan thread, we can request information from their API.
To ease the process of creating a session and requesting information from an HTTP endpoint, we include several helper functions in the :mod:`megu.helpers` module.

To open and use a requests_ session, you can use the :func:`megu.helpers.http_session` context manager.

.. code-block:: python

   from megu.helpers import http_session

   def extract_content(self, url):
      match = self.pattern.match(url.url)
      if not match:
         raise ValueError(f"Failed to match url {url.url}")

      with http_session() as session:
         ...


With this we can fetch information about the posts available from a thread by using the 4chan API.

.. code-block:: python

   with http_session() as session:
      groups = match.groupdict()

      api_response = session.get(f"https://a.4cdn.org/{groups['board']}/thread/{groups['thread']}.json")
      if api_response.status_code != 200:
         raise ValueError(f"Failed to fetch API details for 4chan board {groups['board']} thread {groups['thread']}")

      for post in api_response.json()["posts"]:
         ...

Now that we have a list of post details, we need to start yielding :class:`~megu.models.content.Content` instances for each post with media attachments.
The first thing we should do is filter out posts that don't have attached files.

.. code-block:: python

   for post in api_response.json()["posts"]:
      # skip posts with no file details
      if post.get("filename") is None or post.get("ext") is None:
         continue

      ...

There are several sections that need to be included when constructing content to yield.
Some of these are optional.

Resources
+++++++++

The way we describe *how* to fetch content from a site is through a list of resources.
In our use case, we need resources to describe the requests that need to be made to download some content to the local file system.
Lucky for us, 4chan serves content in a really straightforward manner.

.. code-block:: python

   from megu import HttpResource, HttpMethod

   for post in api_response.json()["posts"]:
      # ... skip posts with no file details ...

      # construct HttpResource for image
      image_url = f"https://i.4cdn.org/{groups['board']}/{post['tim']}{post['ext']}"
      image_resource = HttpResource(method=HttpMethod.GET, url=image_url)

This :class:`~megu.models.http.HttpResource` means that a single HTTP GET request to the provided URL will be used to download the content to the local file system.

Metadata
++++++++

The post details have a good amount of information that might be useful for filtering or naming later on.
We can attach these details in a fairly structured way using the :class:`~megu.models.content.Meta` type.

.. code-block:: python

   from megu import Meta

   for post in api_response.json()["posts"]:
      # ... skip posts with no file details ...
      # ... construct HttpResource for image ...

      # construct Meta for content
      meta = Meta(
         id=str(post["no"]),
         description=post.get("com"),
         publisher=post.get("name"),
         published_at=(datetime.fromtimestamp(post["time"]) if "time" in post else None),
         filename=post.get("filename"),
         thumbnail=f"https://i.4cdn.org/{groups['board']}/{post['tim']}s.jpg"
      )

Checksums
+++++++++

If checksums are available for the remote media, we can also include them in our content instances.
4chan provides base64 encoded MD5 checksums for attachments on posts.

.. code-block:: python

   from megu import Checksum, HashType

   for post in api_response.json()["posts"]:
      # ... skip posts with no file details ...
      # ... construct HttpResource for image ...
      # ... construct Meta for content ...

      # get the MD5 checksum for image
      image_checksum = Checksum(type=HashType.MD5, hash=b64decode(post["md5"]).hex())


Content
+++++++

Constructing content also needs some additional properties to describe the content.
Before we get into the individual properties, checkout the example below:

.. code-block:: python

   from mimetypes import guess_type

   for post in api_response.json()["posts"]:
      # ... skip posts with no file details ...
      # ... construct HttpResource for image ...
      # ... construct Meta for content ...
      # ... get the MD5 checksum for image ...

      yield Content(
         id=f"4chan-{groups['board']}-{post['no']}",
         url=url.url,
         quality=1.0,
         size=post["fsize"],
         type=guess_type(image_url),
         resources=[image_resource],
         meta=meta,
         checksums=[image_checksum],
         extra=post
      )


* ``id``
   Is a unique identifier for the content regardless of the quality.
   There can be multiple content entries that use the *same* id but of different qualities.
   For example, an image may have a thumbnail.
   Both the image and the thumbnail represent the same remote content, so their ids are the same.
   However, their qualities are different.

* ``url``
   Is the string source URL where the content was extracted from.
   In most all cases this should just be the URL provided to the :meth:`~megu.plugin.base.BasePlugin.extract_content` method.

* ``quality``
   Is a floating point number that represents the quality of the content in relation to other content using the same ``id``.
   The higher the number, the better quality the content is.
   Note that this number is relative to other content qualities.
   For example, the source image may use a quality of ``1.0`` and the thumbnail for that same image may be ``0.0``.

* ``size``
   Is the size (in bytes) that will be taken up on the local file system if all resources are downloaded.
   There is *some* flexibility with this value, but try to get as close the the actual value as possible.

* ``type``
   Is the `mimetype <https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types>`_ of the content being fetched.
   This can usually be determined by the :func:`mimetypes.guess_type` function when given the resource URL.
   However, you may need to construct this yourself depending on the type of resource the content uses.

* ``resources``
   Is a list of :class:`~megu.models.content.Resource` instances to use to download the remote content to the local file system.
   For each resource defined in this list, a request will be made and the response will be downloaded and bundled as an artifact in a manifest.
   This means that the number of resources provided in the content should be the same number of artifacts downloaded as a manifest.

* ``meta``
   Is a :class:`~megu.models.content.Meta` instance containing metadata taken from the media content host.
   This includes various descriptive information about the content that is not vital to downloading the content.

* ``checksums``
   Is a list of :class:`~megu.models.content.Checksum` instances used to verify the fetched content.

* ``extra``
   Is a dictionary of miscellaneous data that can be used to store whatever data you might want.
   Keep it reasonable though.


So we end up with an implementation of :meth:`~megu.plugin.base.BasePlugin.extract_content` that looks like the following:

.. code-block:: python

   class ThreadPlugin(BasePlugin):

      name = "4chan Thread"
      domains = {"boards.4chan.org", "boards.4channel.org"}
      pattern = re.compile(r"^https?:\/\/(?:(?:www|boards)\.)?4chan(?:nel)?\.org\/(?P<board>\w+)\/thread\/(?P<thread>\d+)")

      def can_handle(self, url: Url) -> bool:
         return self.pattern.match(url.url) is not None

      def extract_content(self, url):
         match = self.pattern.match(url.url)
         if not match:
            raise ValueError(f"Failed to match url {url.url}")

         with http_session() as session:
            groups = match.groupdict()

            api_response = session.get(f"https://a.4cdn.org/{groups['board']}/thread/{groups['thread']}.json")
            if api_response.status_code != 200:
               raise ValueError(f"Failed to fetch API details for 4chan board {groups['board']} thread {groups['thread']}")

            for post in api_response.json()["posts"]:
               # skip posts with no file details
               if post.get("filename") is None or post.get("ext") is None:
                  continue

               # construct HttpResource for image
               image_url = f"https://i.4cdn.org/{groups['board']}/{post['tim']}{post['ext']}"
               image_resource = HttpResource(method=HttpMethod.GET, url=image_url)

               # construct Meta for content
               meta = Meta(
                  id=str(post["no"]),
                  description=post.get("com"),
                  publisher=post.get("name"),
                  published_at=(datetime.fromtimestamp(post["time"]) if "time" in post else None),
                  filename=post.get("filename"),
                  thumbnail=f"https://i.4cdn.org/{groups['board']}/{post['tim']}s.jpg"
               )

               # get the MD5 checksum for image
               image_checksum = Checksum(type=HashType.MD5, hash=b64decode(post["md5"]).hex())

               yield Content(
                  id=f"4chan-{groups['board']}-{post['no']}",
                  url=url.url,
                  quality=1.0,
                  size=post["fsize"],
                  type=guess_type(image_url),
                  resources=[image_resource],
                  meta=meta,
                  checksums=[image_checksum],
                  extra=post
               )

Now that we have yielded the fully constructed content, the rest of the framework can take it from there.

Merge Manifest
~~~~~~~~~~~~~~

The final concern a plugin needs to address is merging the downloaded manifest into a single file.
For most use cases were content is downloaded with a **single** resource, the "merging" process is just moving the file to a new name.

This functionality is handled by the :meth:`~megu.plugin.base.BasePlugin.merge_manifest` method.
It should take in a :class:`~megu.models.content.Manifest` instance as well as a :class:`pathlib.Path` instance.
This method will do whatever is necessary to merge the artifacts included in the manifest to the given path.
Finally, the method should return the path that the manifest artifacts were merged to (typically the provided path).

.. code-block:: python

   def merge_manifest(self, manifest: Manifest, to_path: Path) -> Path:
      if len(manifest.artifacts) != 1:
         raise ValueError(f"{self.__class__.__name__} expects only one artifact")

      _, only_artifact = manifest.artifacts[0]
      only_artifact.rename(to_path)

      return to_path


This merging process could be much more complicated depending on the complexity of the resource that were requested in the content.
For example, if we were downloading fragments of video, we might need to utilize FFMPEG to merge the fragments together.

So we finally end up with a plugin that looks like the following:

.. code-block:: python

   class ThreadPlugin(BasePlugin):

      name = "4chan Thread"
      domains = {"boards.4chan.org", "boards.4channel.org"}
      pattern = re.compile(r"^https?:\/\/(?:(?:www|boards)\.)?4chan(?:nel)?\.org\/(?P<board>\w+)\/thread\/(?P<thread>\d+)")

      def can_handle(self, url: Url) -> bool:
         return self.pattern.match(url.url) is not None

      def extract_content(self, url):
         # ... <snipped> ...
         ...

      def merge_manifest(self, manifest: Manifest, to_path: Path) -> Path:
         if len(manifest.artifacts) != 1:
            raise ValueError(f"{self.__class__.__name__} expects only one artifact")

         _, only_artifact = manifest.artifacts[0]
         only_artifact.rename(to_path)

         return to_path


This plugin of course is very naive and is likely not considering all the different types of responses that could occur against the API.
For a more concrete example of plugins, checkout the following examples.
