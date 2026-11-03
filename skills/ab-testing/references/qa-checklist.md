# Storefront QA checklist (this skill's own checks)

Read this in Stage 3 step 3, or when QA was deferred to production because no preview was possible (Stage 5 step 2). All checks run in the person's Edge (`browser_actions`), with real clicks only: Cowork's browser cannot run page scripts, so nothing is checked "out of sight" through a script; what can't be seen in the page or its DOM is said as not checked.

Check the test's `surface` pages (URLs in the run-level `surfaces`) first. Use only what any storefront has, so it works on every platform:

- **Add to cart** through the real button (`dom_click`), then the cart count and the cart page; afterwards remove only the line you added (`references/site-validation.md`, "Cart round trip").
- **Product options** through the real inputs, comparing the shown price and image with the page's own product data in the DOM (structured data or the product JSON in the page).
- **Key page loads:** the page renders (screenshot), no broken images or obvious horizontal overflow in the screenshot, no error text in the DOM. JavaScript console errors and failed network requests cannot be read in Cowork: list them as not checked.
- **On-screen error messages.**
- **The change itself:** the control (A) matches the live site; the variation's code is present in the page or theme (the flag key, the new snippet or element in `get_dom`); B as section 3 of `references/build/stage-3-qa.md` allows. Desktop in the person's window; mobile as inferred (no phone-size view), or the person's narrowed window when they choose, captioned as such.

Use Shopify storefront endpoints (`/cart.js`, `/products/<handle>.js`) only when the store is Shopify, opened as pages with `navigate_to` + `get_dom` (read-only).

Never type into payment fields or place an order; remove only the cart lines you added.
