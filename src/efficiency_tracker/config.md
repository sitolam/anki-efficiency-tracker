# Efficiency Tracker — configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `theme` | string | `"auto"` | Visual theme of the dashboard. One of `"auto"` (follow system), `"dark"`, or `"light"`. You can also cycle this from the dashboard's "Theme" button. |
| `good_threshold` | number | `70` | Efficiency percentage at which the indicator turns **green**. |
| `warn_threshold` | number | `45` | Below this percentage the indicator is **red**. Between this and `good_threshold` it is **amber**. |
| `show_toolbar_button` | boolean | `true` | Show an "Efficiency" link in Anki's top toolbar (next to Stats). Restart Anki after changing. |

After changing the threshold values, reopen the statistics window to see the
new colours.
