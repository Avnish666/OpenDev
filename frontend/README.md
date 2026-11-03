# OpenDev frontend

React/TypeScript/Vite UI for public campaigns, financial transparency, roadmap,
maintainer outcomes, analytics and cited accountability chat.

Use Node 24 and `npm ci` here. `npm test`, both `tsc --noEmit -p tsconfig.app.json`
and `tsconfig.node.json`, `npm run lint` and `npm run build` are the checks.
`VITE_API_URL` is public configuration; an empty value uses same-origin `/api`.

For the credential-free synthetic local demo use the [root README](../README.md)
and [demo setup](../docs/demo-setup.md). The root command `node frontend/demo.mjs`
starts a guarded loopback-only Community server with a fixed local API proxy.
Normal `npm run dev` does not automatically supply that demo proxy.

Optional Studio installation and terms are isolated in `studio/`; normal installs
and Community builds exclude Studio/Enterprise. Do not put backend keys in Vite,
suppress evaluation warnings or treat a trial as public deployment authorization.
Public deployment remains NO-GO; see [final handoff](../docs/phase7-final-handoff.md).
