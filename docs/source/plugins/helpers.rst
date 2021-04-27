Helpers
=======

To assist you with building the functionality of a plugin, several helper methods are exposed from the :mod:`megu.helpers` module.

HTTP requests
~~~~~~~~~~~~~

Very likely you will need to make requests to get information from the user provided URL.
In this situation you can utilize the :func:`megu.helpers.http_session` context manager to automatically open and close a requests session for your requests.

.. code-block:: python

   from megu.helpers import http_session

   with http_session() as session:
      resp = session.get("https://example.com")
      if resp.status_code != 200:
         raise ValueError(f"Received invalid status code {resp.status_code}")

      # ... handle response data ...


Beautiful Soup
~~~~~~~~~~~~~~

From fetched HTML data from a given URL, you may need to parse and search through the elements to find specific data properties.
To handle this you should always be using BeautifulSoup_.
We provide a quick helper function :func:`megu.helpers.get_soup` that will automatically construct a ``BeautifulSoup`` instance from some given HTML markup for you.

.. code-block:: python

   from megu.helpers import http_session, get_soup

   with http_session() as session:
      resp = session.get("https://example.com")
      soup = get_soup(resp.text)

      soup.find_all('a') # find all `<a>` elements


Disk Cache
~~~~~~~~~~

If you are interacting with an API, it is very likely you will need to persist access tokens or other miscellaneous data for future runs of the framework.
Rather than build your own caching functionality, we provide a helper :func:`megu.helpers.disk_cache` context manager to provide you access to a simple persistent caching layer.

You **MUST** provide a unique cache name to use the disk cache.
It is typically best to simply use your plugin's package name as the cache name.
Please read through the package documentation for information on the enforced naming conventions.

.. code-block:: python

   from megu.helpers import disk_cache

   with disk_cache("my-plugin") as cache:
      cache.set('key', 'value', expire=5) # set a cached key that expires in 5 seconds

      value = cache.get('key')
      assert value == 'value'

.. important::
   You should only be using this helper if your plugin **absolutely** must persist information between run of the CLI or the framework.
   We would like to avoid throwing additional data onto a user's system where not necessary.


Temporary Files / Directories
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you need a temporary file or directory to work from, you can use the :func:`megu.helpers.temporary_file` or :func:`megu.helpers.temporary_directory` context managers.
You must also provide a prefix as the first argument to both these context managers.
This should likely just be your plugin's package name.

.. code-block:: python

   from megu.helpers import temporary_file, temporary_directory

   with temporary_file("my-plugin", "w") as temp_file:
      # note that the return value is a tuple containing the path and file handle
      (temp_filepath, temp_fileio) = temp_file
      assert temp_filepath.is_file()

   with temporary_directory("my-plugin") as temp_dir:
      # note the return value is just the directory path
      assert temp_dir.is_dir()


Noops
~~~~~

If you ever need a `noop <https://en.wikipedia.org/wiki/NOP_(code)>`_ class or function you can use the :class:`megu.helpers.noop_class` or :func:`megu.helpers.noop` respectively.


.. code-block:: python

   from megu.helpers import noop_class, noop

   inst = noop_class()
   inst.do_something() # returns None

   noop() # returns None
