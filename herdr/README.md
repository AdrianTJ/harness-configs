# herdr

Config root: `$XDG_CONFIG_HOME/herdr/` (usually `~/.config/herdr/`).

herdr is the odd one out: it's a multiplexer that runs the *other* harnesses,
so its config is about orchestration — panes, keybindings, agent lifecycle
manifests — rather than about prompting a model.

| Repo path | Links to | What it is |
|---|---|---|
| `config.toml` | `.../herdr/config.toml` | Main config, including the `[keys]` section. |
| `modules/<name>/` | `.../herdr/plugins/config/<name>/` | Per-module config. |

Generate a fully-commented starting point with:

```sh
herdr --default-config > herdr/config.toml
```

## Verify the modules path

The `modules/` mapping in `links.conf` is inferred from herdr's documented
plugin config location (`$HERDR_PLUGIN_CONFIG_DIR`, which resolves to
`~/.config/herdr/plugins/config/<plugin-name>/` on Linux). Confirm it matches
what your herdr build actually reads before relying on it — if module code and
module config live in different places, split the manifest entry in two.

## Not linked

`session.json` and `herdr.log` are runtime state.
