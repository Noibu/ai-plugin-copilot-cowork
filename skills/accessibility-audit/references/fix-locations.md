# Where a violation gets fixed in code

Read this only when drafting pull requests. Use the Shopify section when the store's platform is Shopify, and the generic section for any other platform or a headless or custom frontend.

One violation appearing on several pages is one shared-component fix, not several.

## Shopify

| Violation type | Usual location |
|---|---|
| Colour contrast | `assets/*.css` / `*.scss.liquid`; `config/settings_data.json` only if merchant-editable through the theme editor |
| Nested interactive controls (4.1.2) | `sections/header.liquid`, `snippets/mega-menu.liquid` |
| Heading hierarchy (1.3.1) | the section rendering the heading: swap the tag, keep the class |
| Missing alt text (1.1.1) | product and collection card snippets: `{{ image.alt \| escape }}` with a fallback, `alt=""` for decorative images. If `image.alt` itself is empty, that is not a templating fix; log it as `needs-investigation`; don't invent text |
| Missing focus indicators (2.4.7) | the global stylesheet: `:focus-visible`, never `outline: none` without a replacement |
| Unlabelled form controls | the form snippet: `<label>` or `aria-label`, not a placeholder |
| Hidden-but-present content | the offending snippet: `display: none`, or remove it |
| Country or currency selector in footer | `sections/footer.liquid` and the localisation snippets |

Most violations are theme-level (`sections/`, `snippets/`, `assets/*.css`, `layout/theme.liquid`).

**Rules**

- Never touch `checkout.liquid` or anything under `checkout/`.
- Never edit `config/settings_data.json` for merchant-managed values. File the finding and describe the setting to change.
- Contrast fixes: state the computed before and after ratio ("#8A8A8A → #6E6E6E on #FFFFFF: 3.9:1 → 5.1:1").
- Prefer additive CSS over deleting existing rules.
- If there is a build step, or the repository doesn't match the live theme structure: stop and report the mismatch.
- A headless frontend (Next.js, Remix, Hydrogen): the theme paths above don't apply. Classify by component role with the generic section.

## Generic, unknown or headless

1. Take the violation's selector, class or id from the finding.
2. If GitHub is connected, search the repository for it before guessing:
   - One clear match → that file is the fix location.
   - Matches across several files or templates → a shared component; high leverage; the same "one fix, many pages" logic as a known platform.
   - No searchable match (a build-generated class, for example) → classify by component role, below.
3. If the search comes up empty, classify by component role:
   - Shared nav or header pattern → fix there; it affects every page rendering it.
   - Repeated template (product card, listing row, form) → fix in the template.
   - Global style (contrast, focus) → the stylesheet, not the markup.
   - One-off page-level element → lower leverage; note it as such.

Can't map it confidently either way? Log it as `needs-investigation` with the selector, rule id and criterion. Don't guess.
