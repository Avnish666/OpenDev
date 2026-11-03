# License and notice review record

This file inventories inspected declarations and remaining owner actions. It is not
a license grant, legal opinion or authorization to redistribute the application.
**No root LICENSE was added** because contributor/application rights and the owner's
intended grant have not been authorized. Public distribution remains blocked.

| Component | Inspected declaration / evidence | Remaining action |
| --- | --- | --- |
| OpenDev application | No authorized root LICENSE/whole-app notices decision | Owner/contributors choose and authorize compatible licensing; add exact license text and attributions after review, including earlier published artifacts. |
| Bryntum Community 8.0.0-beta.1 | Installed Community package metadata declares MIT; main lockfile inventory | Preserve actual vendor copyright/license notices; confirm intended Community package/beta use and current competition rules. |
| AG Grid/Charts Community | Community package metadata declares MIT; versions in root lockfile | Preserve package notices; do not call this AG Studio or silently add Enterprise. |
| Optional AG Studio 3.0.0 / Enterprise | Commercial/evaluation declarations in the separate Studio graph; trial notices visible | Verify actual local evaluation terms, permitted recording/disclosure and any intended public entitlement. Keep isolated/default disabled. No public license is verified. |
| pypdfium2 5.14.0 / PDFium | Apache-2.0/BSD-style wrapper and bundled dependency licenses; `../phase7-pdfium-license-review.json` records 18 actual notice hashes | Notice hashes match the installed wheel. Preserve PDFium/build/dependency notices, including relevant attribution/source provisions; owner distribution signoff remains open. |
| pypdf / Pillow / HTTPX | BSD-style / MIT-CMU / BSD-style declarations in current inventory | Preserve exact installed notices and verify bundled/transitive code. |
| psycopg / binary libpq dependencies | LGPL declarations and bundled native libraries | Review wheel/native library notices and redistribution/source obligations; do not infer them from a short metadata field. |
| Tesseract / Leptonica / Debian/Python/Node base | Native runtime/system packages, additional notices | Preserve `/usr/share/doc/*/copyright`, relevant native notices and reviewed image inventory; full OS CVE and distribution audit remains open. |
| APIMatic PayPal Context Plugin 0.4.1 | Prior documented MIT declaration, development guidance only | Preserve required attribution where applicable and verify sponsor evidence requirements; no invented runtime SDK dependency. |

The current image no longer installs PyMuPDF/MuPDF, verified by existing image smoke.
That runtime replacement does not decide obligations associated with prior artifacts
or the whole application. Historical phase reports describe the old engine and are
not current dependency declarations.

[Current dependency inventory](dependency-license-inventory.json) includes installed
Python runtime/test dependency closure and root frontend lock entries. It is not a
complete OS SBOM, legal signoff or proof of zero vulnerabilities. Default lock and
Docker context exclude commercial Studio/Enterprise; the optional graph remains
separate. Test/build success and trial banners never supply public rights.

Before any public package, video or deployment, the owner must review the actual
scope of distribution, actual vendor terms, contributor consent, all relevant notice
text and current sponsor rules. Leave unverified checklist entries open rather than
inventing an accepted license decision.
