Data Descriptors
================

First things first, we need to define some common data descriptors.

* | :class:`~megu.models.types.Url`
  | Wraps a basic string URL in a furl_ for better manipulation of the provided URL.
  | This is really a basic type that is used to unify the communication of a URL throughout the package.

* | :class:`~megu.models.content.Content`
  | Defines some media content discovered on a site (image, video, audio, etc.).
  | A content instance has several data descriptors within it:

   * | :class:`~megu.models.content.Meta`
     | Describes some site-provided metadata about the content.

   * | :class:`~megu.models.content.Checksum`
     | Describes some validation checksum for the locally fetched content.

* | :class:`~megu.models.content.Resource`
  | Defines a resource that can be fetched to help reproduce some content locally.
  | This is an abstract definition, concrete implementations such as :class:`~megu.models.http.HttpResource` should be used within content instances.

* | :class:`~megu.models.content.Manifest`
  | Defines a grouping of locally fetched resources that can be merged to reproduce some content.
