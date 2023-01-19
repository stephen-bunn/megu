Rules
=====

1. Plugin packages **MUST** start with a prefix of ``megu_``.
2. Plugin packages **MUST** expose at least 1 subclass of :class:`megu.plugin.base.BasePlugin`.
3. Plugins **MUST** provide a descriptive name.
4. Plugins **MUST** provide a set of handled domains.
5. Plugins **MUST** yield content from ``extract_content``.
6. Plugins **SHOULD** use environment variables for internal configuration.

   * We do not expose or provide any kind of configuration from the framework to the plugin.
     The plugin should be capable of reading in necessary configuration from the environment if necessary.

7. Plugins **SHOULD** only use the disk cache if absolutely necessary.
8. Plugins **SHOULD** avoid parsing HTML using BeautifulSoup_ whenever possible.
9. Plugins **SHOULD NOT** require API credentials for default functionality.
