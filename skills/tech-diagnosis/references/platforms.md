# Stack trace classification by platform

Read the section for the store's platform before fetching or classifying any error, in a scan and in a diagnosis. Take from it the merchant, platform, vendor and telemetry paths. Use "Generic" when the platform isn't one of the four named, or when the store runs a headless or custom frontend.

Every frame falls into one class:

- **Merchant code**: the store owns it and can edit it. An error with at least one merchant frame is fixable.
- **Platform code**: core platform infrastructure. Not fixable by the merchant or any app vendor. Discard.
- **Vendor code**: a third party with its own support channel. Share with the vendor.
- **Telemetry**: analytics, pixel and beacon scripts. Discard silently.

**HTTP errors without a JavaScript stack trace.** On every platform, any 4XX or 5XX error with no JavaScript stack trace is Platform and is discarded.

## Telemetry on every platform

- `connect.facebook.net/`: Meta Pixel
- `www.google-analytics.com/`: Google Analytics
- `cdn.heapanalytics.com/`: Heap
- `js.posthog.com/`: PostHog
- `snap.licdn.com/`: LinkedIn Insight Tag
- `sc-static.net/`: Snapchat Pixel
- `bat.bing.com/`: Microsoft/Bing Ads
- `cdn.segment.com/`: Segment
- `cdn.amplitude.com/`: Amplitude
- `analytics.tiktok.com/`: TikTok Pixel

## Shopify

**Merchant code (fixable)**

- `cdn.shopify.com/s/files/`: theme assets (JS, CSS, images) served through the Shopify CDN
- `cdn.shopify.com/s/trekkie/`: theme analytics snippets
- The store's own domain (e.g. `store.myshopify.com` or a custom domain) for any inline scripts

**Platform code (discard; Shopify core infrastructure only)**

- `cdn.shopify.com/shopifycloud/`: Shopify platform scripts
- `cdn.shopify.com/s/shopifycloud/`: same
- `checkout.shopify.com/`: Shopify checkout
- `monorail-edge.shopifysvc.com/`: Shopify analytics infrastructure
- `*.shopifysvc.com/`: internal Shopify service endpoints

**Vendor code (share with vendor)**: anything with its own support channel that isn't merchant-owned or telemetry, including Shopify-built products that run independently of core infrastructure.

- `*.shopifyapps.com/`: Shopify app platform endpoints (each app has its own support)
- `shop.app/`: Shop app (a separate Shopify product with its own support)
- `pay.shopify.com/`: Shop Pay (a separate product)
- `static.klaviyo.com/`, `static-tracking.klaviyo.com/`: Klaviyo
- `heyethos.com/`: Hey Ethos (loyalty)
- `yotpo.com/`, `loox.io/`: reviews apps
- Any third-party CDN not matching the store domain or the Shopify core infrastructure above

**Telemetry, in addition to the shared list**

- `heapanalytics.com/`, `heap-api.com/`: Heap API endpoints
- `cdn.shopify.com/shopifycloud/analytics-next/`: Shopify analytics beacon

**Headless or custom frontend.** If this Shopify store runs a headless frontend (Next.js, Remix, Hydrogen and so on), theme asset paths won't match the patterns above. Merchant code will be on the store's own CDN (Vercel, AWS CloudFront and so on). Classify with "Generic" below.

**HTTP errors without a stack trace** on Shopify are most commonly bot or abuse protection (403, 429) or missing assets (404).

## Magento / Adobe Commerce

**Merchant code (fixable)**

- `pub/static/frontend/[Vendor]/[ThemeName]/`: the merchant's custom theme
- `app/design/frontend/[Vendor]/[ThemeName]/`: theme source files
- Custom modules in `app/code/[Vendor]/`: merchant or agency-built modules

**Platform code (not fixable by merchant)**

- `pub/static/frontend/Magento/`: Magento core frontend modules
- `lib/web/`: Magento core JS libraries
- `pub/static/adminhtml/`: admin panel code
- `vendor/magento/`: Magento core (Composer-installed)

**Vendor code (share with vendor)**

- `vendor/[ThirdParty]/`: third-party extensions installed through Composer
- Any external CDN scripts not matching the store domain

**Telemetry, in addition to the shared list**

- `omtrdc.net/`: Adobe Analytics (common on Adobe Commerce)
- `demdex.net/`: Adobe Audience Manager

**HTTP errors without a stack trace** on Magento are typically access control (403), rate limiting (429) or missing static assets (404).

## WooCommerce / WordPress

**Merchant code (fixable)**

- `/wp-content/themes/[active-theme]/`: the merchant's active theme
- `/wp-content/themes/[child-theme]/`: child theme overrides
- Custom plugins built for this store in `/wp-content/plugins/[custom-plugin]/`

**Platform code (not fixable by merchant)**

- `/wp-includes/`: WordPress core
- `/wp-content/plugins/woocommerce/`: WooCommerce core
- `/wp-admin/`: admin scripts

**Vendor code (share with vendor)**

- `/wp-content/plugins/[third-party-plugin]/`: third-party plugins (Klaviyo for WooCommerce and so on)
- External CDN scripts not matching the store domain

**Plugin or theme.** Errors in `/wp-content/plugins/` may be fixable if the plugin is merchant-owned or agency-built, or vendor issues if it is a purchased or free third-party plugin. Use the plugin name to decide ownership; merchant-built plugins are usually named after the store or agency.

**HTTP errors without a stack trace** on WooCommerce are typically access control (403), rate limiting (429) or security plugin blocks (Wordfence and so on).

## BigCommerce

**Merchant code (fixable)**

- Store theme assets served from the store's own domain or the BigCommerce CDN under the merchant's store path
- Stencil theme JS files, typically at paths like `/assets/js/` or `/theme/`
- Custom scripts added through Script Manager that reference the store domain

**Platform code (not fixable by merchant)**

- `cdn11.bigcommerce.com/`: BigCommerce platform CDN (core scripts, checkout)
- `login.bigcommerce.com/`: authentication infrastructure
- BigCommerce checkout scripts (not editable on standard plans)

**Vendor code (share with vendor)**

- External scripts added through Script Manager from third-party domains
- Any CDN not matching BigCommerce or the store domain

**HTTP errors without a stack trace** on BigCommerce are typically DDoS protection (403), API rate limits (429) or missing assets (404).

## Generic / headless / custom

Without reliable path patterns, classify by what can be identified.

**Telemetry, in addition to the shared list**

- `static.ads-twitter.com/`: Twitter/X Pixel
- `heapanalytics.com/`, `heap-api.com/`: Heap API endpoints

**Known vendor scripts (share with vendor).** Whatever the platform, these are always third-party and not fixable by the merchant:

- `static.klaviyo.com/`: Klaviyo
- `googletagmanager.com/`: Google Tag Manager
- `cdn.shopify.com/shopifycloud/`: Shopify platform (even in headless)
- Any recognisable marketing, reviews, support or payments CDN

**Error type as the primary classifier**, when the stack trace origin is unclear:

- **JS error types** (TypeError, ReferenceError, RangeError and so on): likely code-level; treat as a fixable candidate.
- **HTTP error types** (any 4XX or 5XX) with no JS stack trace: infrastructure or platform; classify as Platform and discard.

**Frames on the store's own domain.** If a frame points to the store's own domain or a CDN that clearly serves the merchant's app (Vercel deployment URLs for a known merchant project, for example), treat it as merchant code and fixable.

**When uncertain.** If an error can't be classified with confidence, surface it as a fixable candidate and say in its evidence sentence that the origin is unclear and the fix may need developer investigation.
