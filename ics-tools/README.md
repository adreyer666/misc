# CalDAV UID fixer

Due to relaxed interpretation of the CalDAV (and CardDAV) specifications some tools use "random" (hopefully unique) strings as UID identifiers.
This tool replaces any `UID` with non-alphanumeric characters with a *generated UUID* and saves the old `UID` as `XUID`.


