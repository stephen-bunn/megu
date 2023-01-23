<div style="padding: 1rem; margin-bottom: 1rem; display: flex; justify-content: center;">
  <img alt="Megu Logo" src="docs/source/_static/assets/images/megu-icon.svg"/>
</div>

# Megu

**Plugin-based HTTP media discovery and downloader framework.**

```python
from pathlib import Path
from megu import fetch

next(fetch("https://www.google.com/", Path("~/Downloads/").expanduser()))
```
