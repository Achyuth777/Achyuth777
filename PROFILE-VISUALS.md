# Profile visuals

The header, typing animation, project panels, technology badges, statistics, language chart, and contribution calendar are SVG files stored in this repository. No third-party stats image service is required.

## Data definitions

- **Public repos / followers:** GitHub's public user API.
- **Stars:** sum of stars on owned public repositories, excluding forks.
- **Contributions:** sum of daily counts in GitHub's publicly visible contribution calendar. This is not an all-time commit count. GitHub controls which contributions appear, including any anonymous private-activity counts the owner chooses to expose.
- **Current streak:** consecutive nonzero calendar days ending today, or yesterday if today has no contributions yet. Days use UTC.
- **Best in view:** longest consecutive run in the displayed calendar, not an all-time record.
- **Languages:** aggregate language bytes from GitHub's language API for public non-fork repositories. Generated files, duplicated projects, and large files can affect the result. It is not a proficiency score.
- **Activity trail:** a decorative animated snake over the real calendar. Its movement does not represent additional contributions or change their counts.

## Updates

The workflow runs daily at 02:17 UTC, supports manual dispatch, and runs when its configuration or generator changes. GitHub may delay scheduled runs. If a fetch fails or the calendar format changes, the script fails before replacing the displayed cards. The last successful assets remain available and show their update date.

The generator uses only Python's standard library. Its automatically supplied GitHub Actions token is used for GitHub REST API requests; no personal access token or paid service is needed. Write permission is limited to repository contents so it can commit refreshed SVGs.

Run locally with:

```sh
python scripts/update_stats.py
```

Optional: supply `GH_TOKEN` in the environment to avoid the lower unauthenticated GitHub API rate limit. Never commit credentials.

## Rendering

The SVGs have opaque dark backgrounds and explicit text colors, so they retain contrast in GitHub's light and dark themes. They scale to their container width. Essential identity, project descriptions, and links also appear in text or descriptive alt attributes. CSS animations honor `prefers-reduced-motion` where supported. Some image renderers show static frames; animated playback depends on the viewer.

The visual direction was informed by [Pradishv22](https://github.com/Pradishv22) and [Franklin1312](https://github.com/Franklin1312). The graphics and generator here were created for Achyuth's profile; their personal copy and achievements were not reused.
