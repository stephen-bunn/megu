<div class="LogoContainer">
  <img src="_static/assets/images/megu-icon.svg" alt="Megu Logo" />
</div>

# Megu

> A plugin-centric HTTP media extractor and downloader.

Megu intends to power a personal media extraction framework for various media-hosting sites.
This framework provides the abstractions necessary to adequately and fully describe content hosted by these sites.

These content descriptors can be generated by various third-party plugins that are tailor-made for certain sites.
Using this plugin-based approach removes the technical overhead necessary for this framework.
This framework is **only** concerned with calling plugins, using the described content produced by plugins, validating it, and reproducing it to the local filesystem.
Discovering and extracting content descriptors for concrete media-hosting sites is the concern of plugins.

```{toctree}
installation
usage
plugins
```

```{toctree}
---
maxdepth: 2
---

reference
```