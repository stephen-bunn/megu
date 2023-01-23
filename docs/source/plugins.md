(plugins)=

# Plugins

The functionality of discovering content from specific sites for this library comes from plugins.
Plugins should be domain-specific and must inherit from the {class}`~megu.plugin.base.BasePlugin` asbtract class.

Overall, plugins have 3 main responsibilities:

1. Determining if they can handle a given URL.
2. Discovering content and generating instances of {class}`~megu.models.Content` from a given URL.
3. Writing downloaded artifacts from a given {class}`~megu.models.ContentManifest` to a single file.

:::{important}
Plugins should all be installable via [`pip`](https://pypi.org/project/pip/) if you want them to be able to include other dependencies or to be automatically installable through the Megu CLI.
:::

## Plugin Rules

1. Plugin packages **MUST** start with a prefix of `megu_`.
2. Plugin packages **MUST** register at least 1 subclass of {class}`~megu.plugin.base.BasePlugin`.
3. Plugins **MUST** provide a descriptive human readable name.
4. Plugins **MUST** provide a set of handled domain patterns.
5. Plugins **MUST** yield content from their `iter_content` method.
6. Plugins **SHOULD NOT** require API credentials for default functionality.

## Writing Plugins

Plugins are built as subclasses of {class}`~megu.plugin.base.BasePlugin`.
So all plugin packages will need to have `megu` as a dependency at the very least.

For the following sections, I will be covering how to write an extremely basic plugin to extract media from posts in 4chan threads (since it's relatively straightforward).

The first thing we need is to define a subclass of `BasePlugin`

```python
from megu.plugin.base import BasePlugin

class ThreadPlugin(BasePlugin):
    ...
```

### `name`

The `name` property is required for all plugins.
It should be unique, human-friendly, and fully descriptive of the source the plugin handles.

In our case, we are creating a 4chan thread plugin.

:::{important}
Both the [plugin name](#name) and the [plugin domains](#domains) properties should be decorated (`@property`) class properties.
:::

```python
class ThreadPlugin(BasePlugin):

    @property
    def name(self) -> str:
        return "4chan Thread"
```

This property will be used for rendering of plugin information both in the framework as well as the CLI.

### `domains`

The `domains` set is required for all plugins.
This is a {class}`set` of strings of **ALL** subdomain patterns that should be handled by the plugin.
If a given URL's domain is not present in this set, the plugin will not be used to handle that URL.

This domain pattern uses {mod}`fnmatch` for URL hostname comparison.

:::{important}
Both the [plugin name](#name) and the [plugin domains](#domains) properties should be decorated (`@property`) class properties.
:::

```python
class ThreadPlugin(BasePlugin):

    @property
    def name(self) -> str:
        return "4chan Thread"

    @property
    def domains(self) -> set[str]:
        return {"boards.4chan.org", "boards.4channel.org"}
```

### `can_handle`

The {meth}`~megu.plugin.base.BasePlugin.can_handle` method is required and should take a {class}`~megu.models.types.URL` instance.
If the plugin can handle the URL, it should return a boolean True.
Otherwise, it should always return False.

```python
PATTERN = re.compile(r"^https?:\/\/(?:(?:www|boards)\.)?4chan(?:nel)?\.org\/(?P<board>\w+)\/thread\/(?P<thread>\d+)")

class ThreadPlugin(BasePlugin):

    @classmethod
    def can_handle(cls, url: URL) -> bool:
        return PATTERN.match(str(url)) is not None
```

### `iter_content`

Discovering content is the bulk of the functionality that should be provided by the plugin.
The goal of this method is to yield fully constructed {class}`~megu.models.Content` instances for the framework to handle.
This functionality should be exposed through the {meth}`~megu.plugin.base.BasePlugin.iter_content` method.

```python
def iter_content(self, url: URL) -> Generator[Content, None, None]:
    ...
```

To "fail" the extraction of content, simply raise a {class}`ValueError` at any point.

```python
def iter_content(self, url: URL) -> Generator[Content, None, None]:
    match = self.pattern.match(str(url))
    if not match:
        raise ValueError(f"Failed to match url {url}")
```

In order to fetch information about what data is available from a given 4chan thread, we can request information from their API.
To ease the process of creating a session and requesting information from an HTTP endpoint, we include several helper functions in the {mod}`~megu.helpers` module.

To open and use a [httpx](https://www.python-httpx.org/) session, you can use the {func}`megu.helpers.http_session` context manager.

With this we can fetch information about the posts available from a thread by using the 4chan API.

```python
from megu.helpers import http_session

def extract_content(self, url: URL) -> Generator[Content, None, None]:
    match = self.pattern.match(str(url))
    if not match:
        raise ValueError(f"Failed to match url {url}")

    with http_session() as session:
        groups = match.groupdict()

        api_response = session.get(f"https://a.4cdn.org/{groups['board']}/thread/{groups['thread']}.json")
        if api_response.status_code != 200:
            raise ValueError(f"Failed to fetch API details for 4chan board {groups['board']} thread {groups['thread']}")

        for post in api_response.json()["posts"]:
            # skip posts with no file details
            if post.get("filename") is None or post.get("ext") is None:
                continue
```

Now that we have a list of post details, we need to start yielding {class}`~megu.models.Content` instances for each post with media attachments.

There are several sections that need to be included when constructing content to yield.
Some of these are optional.

#### Content Resources

The way we describe _how_ to fetch content from a site is through a list of resources.
In our use case, we need resources to describe the requests that need to be made to download some content to the local file system.
Lucky for us, 4chan serves content in a really straightforward manner.

```python
from megu.models import HTTPResource

for post in api_response.json()["posts"]:
    # ... skip posts with no file details ...

    # construct HTTPResource for image
    image_resource = HTTPResource("GET", f"https://i.4cdn.org/{groups['board']}/{post['tim']}{post['ext']}")
```

This {class}`~megu.models.HTTPResource` means that a single HTTP GET request to the provided URL will be used to download the content to the local file system.

#### Content Metadata

The post details have a good amount of information that might be useful for filtering or naming later on.
We can attach these details in a fairly structured way using the {class}`~megu.models.ContentMetadata` type.

```python
from megu.models import ContentMetadata, URL

for post in api_response.json()["posts"]:
    # ... skip posts with no file details ...
    # ... construct HttpResource for image ...

    # construct Meta for content
    meta = ContentMetadata(
       id=str(post["no"]),
       description=post.get("com"),
       publisher=post.get("name"),
       published_at=(datetime.fromtimestamp(post["time"]) if "time" in post else None),
       filename=post.get("filename"),
       thumbnail=URL(f"https://i.4cdn.org/{groups['board']}/{post['tim']}s.jpg")
    )
```

#### Content Checksums

If checksums are available for the remote media, we can also include them in our content instances using the {class}`~megu.models.ContentChecksum` type.
4chan provides base64 encoded MD5 checksums for attachments on posts.

```python
from megu.models import ContentChecksum

for post in api_response.json()["posts"]:
    # ... skip posts with no file details ...
    # ... construct HttpResource for image ...
    # ... construct Meta for content ...

    # get the MD5 checksum for image
    image_checksum = ContentChecksum("md5", b64decode(post["md5"]).hex())
```

#### Content

Constructing content also needs some additional properties to describe the content.
Before we get into the individual properties, checkout the example below:

```python
from mimetypes import guess_type

for post in api_response.json()["posts"]:
    # ... skip posts with no file details ...
    # ... construct HttpResource for image ...
    # ... construct Meta for content ...
    # ... get the MD5 checksum for image ...

    yield Content(
        id=f"4chan-{groups['board']}-{post['no']}-image",
        group=f"4chan-{groups['board']}-{post['no']}",
        name="Post Image",
        url=url.url,
        quality=1.0,
        size=post["fsize"],
        type=guess_type(image_url),
        resources=[image_resource],
        meta=meta,
        checksums=[image_checksum],
        extra=post
    )
```

See {ref}`usage` for more details about each property in the {class}`~megu.models.Content` class.
Now that we have yielded the fully constructed content, the rest of the framework can take it from there in order to download this content.

### `write_content`

The final concern a plugin needs to address is merging the downloaded manifest into a single file.
For most use cases were content is downloaded with a **single** resource, the "merging" process is just moving the file to a new name.

This functionality is handled by the {meth}`~megu.plugin.base.BasePlugin.write_content` method.
It should take in a {class}`~megu.models.ContentManifest` instance as well as a {class}`~pathlib.Path` instance.
This method will do whatever is necessary to merge the artifacts included in the manifest to the given path.
Finally, the method should return the path that the manifest artifacts were merged to (typically the provided path).

```python
def write_content(self, manifest: ContentManifest, to_path: Path) -> Path:
    _, artifacts = manifest
    if len(artifacts) != 1:
        raise ValueError(f"{self.__class__.__name__} expects only one artifact")

    _, only_artifact = artifacts[0]
    only_artifact.rename(to_path)

    return to_path
```

This merging process could be much more complicated depending on the complexity of the resource that were requested in the content.
For example, if we were downloading fragments of video, we might need to utilize FFMPEG to merge the fragments together.

:::{note}
The above 4chan example plugin is very naive and is likely not considering all the different types of responses that could occur against the API.
:::

## Helpers

To assist you with building the functionality of a plugin, several helper methods are exposed from the {mod}`~megu.helpers` module.

### HTTP Sesssion

Very likely you will need to make requests to get information from the user provided URL.
In this situation you can utilize the {func}`~megu.helpers.http_session` context manager to automatically open and close a requests session for your requests.

```python
from megu.helpers import http_session

with http_session() as session:
    resp = session.get("https://example.com")
    if resp.status_code != 200:
        raise ValueError(f"Received invalid status code {resp.status_code}")

    # ... handle response data ...
```

### Disk Cache

If you are interacting with an API, it is very likely you will need to persist access tokens or other miscellaneous data for future runs of the framework.
Rather than build your own caching functionality, we provide a helper {func}`~megu.helpers.disk_cache` context manager to provide you access to a simple persistent caching layer.

You **MUST** provide a unique cache name to use the disk cache.
It is typically best to simply use your plugin's package name as the cache name.
Please read through the package documentation for information on the enforced naming conventions.

```python
from megu.helpers import disk_cache

with disk_cache("my-plugin") as cache:
    cache.set('key', 'value', expire=5) # set a cached key that expires in 5 seconds

    value = cache.get('key')
    assert value == 'value'
```

:::{important}
You should only be using this helper if your plugin **absolutely** must persist information between run of the CLI or the framework.
We would like to avoid throwing additional data onto a user's system where not necessary.
:::

### Temporary Files / Directories

If you need a temporary file or directory to work from, you can use the {func}`~megu.helpers.temporary_file` or {func}`~megu.helpers.temporary_directory` context managers.
You must also provide a prefix as the first argument to both these context managers.
This should likely just be your plugin's package name.

```python
from megu.helpers import temporary_file, temporary_directory

with temporary_file("my-plugin", "w") as temp_file:
    # note that the return value is a tuple containing the path and file handle
    (temp_filepath, temp_fileio) = temp_file
    assert temp_filepath.is_file()

with temporary_directory("my-plugin") as temp_dir:
    # note the return value is just the directory path
    assert temp_dir.is_dir()
```
