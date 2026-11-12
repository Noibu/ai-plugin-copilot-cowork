# ai-plugin-copilot

Official Noibu AI plugin for Microsoft 365 Copilot Cowork. It connects Cowork to a store's session, error and conversion data in Noibu, and adds nine skills that work from that data.

| Skill | What it does |
| --- | --- |
| `store-pulse` | A read on the store's last 24 hours: headline numbers and the purchase funnel |
| `checkout-analysis` | Where shoppers drop off in checkout, and what changed |
| `product-analysis` | Which products and collections are winning or losing |
| `segment-analysis` | How devices, countries and channels convert |
| `tech-diagnosis` | The highest-value errors and slow pages, and how to fix one |
| `ab-testing` | Finds test ideas from Noibu data, then builds and starts a picked test |
| `accessibility-audit` | Starts Noibu's WCAG scan on the busiest pages and ranks the findings you bring back |
| `build-business-context` | Interviews you and saves a business-context file to Noibu |
| `querying-noibu-data` | The reference the other skills use for calling Noibu's tools |

## Status

Preview. Not every skill has been run end to end in a Cowork tenant, and two have not been run at all:

- `ab-testing`: the finder, the Shopify theme preview and the live-code check are untested.
- `accessibility-audit`: Noibu's tools can start a scan but cannot return its results, so the skill reports findings only once you paste them in.

Cowork cannot open a store's pages or run code in them. Every skill works from Noibu's data and tools; where a page has to be looked at, the skill gives you the link and what to check.

## Layout

The repository root is the app package.

```
manifest.json         the app manifest
color.png, outline.png
noibu-mcp-tools.json  the Noibu connector's tool list (a snapshot of what Noibu's server offers)
skills/<skill>/       SKILL.md, references/, and scripts/card.py for the skills that show a report card
```

## Build the package

Zip the package files from the repository root:

```shell
zip -r noibu-cowork.zip manifest.json color.png outline.png noibu-mcp-tools.json skills -x '*.DS_Store' -x '*__pycache__*'
```

Upload that zip to Cowork. Raise `version` in `manifest.json` before uploading a changed package.

## Limits to keep in mind

Cowork enforces these silently:

- A `SKILL.md` over 20,000 characters is cut off.
- A skill keeps 20 companion files; any past the 20th, in path order, are dropped.
- A skill can only read files inside its own folder, and folders are one level deep (`references/`, `scripts/`).

`scripts/card.py` is the same file in every skill that has one. Change it in all of them together.

`noibu-mcp-tools.json` has to be refreshed when the tools on Noibu's server change; Cowork reads tool descriptions from it.
