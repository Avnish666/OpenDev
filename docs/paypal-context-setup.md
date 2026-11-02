# APIMatic PayPal Context Plugin setup

Verified 2026-11-02 in the current Codex Cloud task. This setup adds agent guidance
only: no PayPal SDK dependency, credentials, payment code, API call, or database
change was added.

## Official documentation and compatibility

- APIMatic installer: https://github.com/apimatic/context-plugins-installer
- Inspected installer source revision: `a5aadc36f683eae8d78f17e080a6a9ec52f880ad`.
- README documents `npx context-plugins install paypal`, Node >=18, Codex CLI
  detection on PATH, `--targets codex`, marketplace registration, and
  `codex plugin add <plugin>@<marketplace>`. Codex requires a new session to load
  newly installed plugins automatically.
- Official installed source: https://github.com/context-plugins/plugin-marketplace
  at revision `7cbdf85dc95f09d9ede8c5d349506686684fa0d4`, `plugins/paypal`.
  The manifest identifies APIMatic as author and https://context.apimatic.io/ as homepage.
- Installer package `context-plugins@0.12.0`; installed PayPal plugin **0.4.1**, MIT.
- Current runtime: Node v24.19.0, Codex CLI 0.163.0, Linux. Codex's plugin subcommands
  are present. Direct installation worked; no manual-copy fallback was needed.

## Exact steps and results

Read-only discovery included APIMatic's GitHub organization and the installer
README/source. An initial inspection of `apimatic/skills` found generic portal/SDK
skills, not the requested PayPal plugin; these were not installed.

```bash
git clone --depth 1 https://github.com/apimatic/context-plugins-installer.git /tmp/context-plugins-installer
cat /tmp/context-plugins-installer/README.md
node --version
codex --version
codex plugin --help
```

The first attempt below failed because Node fetch did not automatically use the
inherited cloud HTTPS proxy. No TLS verification was disabled.

```bash
CP_TELEMETRY=off CP_STATE_DIR=/workspace/paypal-context-state \
  npm exec --cache /workspace/npm-cache --yes --package=context-plugins@0.12.0 -- \
  context-plugins install paypal --targets codex --yes
```

The successful retry used Node's supported environment-proxy setting (commands
were executed with the cloud executor's approved network access):

```bash
cd /workspace/OpenDev
NODE_USE_ENV_PROXY=1 CP_TELEMETRY=off CP_STATE_DIR=/workspace/paypal-context-state \
  npm exec --cache /workspace/npm-cache --yes --package=context-plugins@0.12.0 -- \
  context-plugins install paypal --targets codex --yes
```

Installer output confirmed marketplace `context-plugins` added and
`paypal@context-plugins` installed into Codex. Only Codex was selected; telemetry
was disabled. npm cached the installer and its dependencies; no application
manifest/lockfile or application package was changed. No credentials were needed.

Verification:

```bash
codex plugin list --json
cat /workspace/paypal-context-state/installed.json
cat /home/agent/.codex/plugins/cache/context-plugins/paypal/0.4.1/plugin.json
find /home/agent/.codex/plugins/cache/context-plugins/paypal/0.4.1/skills -name SKILL.md
cat /home/agent/.codex/plugins/cache/context-plugins/paypal/0.4.1/skills/python/python-getting-started/SKILL.md
```

- Codex local registry returned `pluginId: paypal@context-plugins`, `version: 0.4.1`,
  `installed: true`, `enabled: true`.
- All three manifest skill roots exist and **29 SKILL.md files are readable**:
  Python 11, TypeScript 9, .NET 9. Manifest and representative Python getting-started/
  integration content were read by this task through filesystem tools.
- Python getting-started SHA256:
  `50a4b8904ee7d0264442ef333448edb49ac1b4858b3f2b5ba95e66de5b48c96d`.
- Codex reported a separate failure to fetch its ChatGPT remote plugin catalog;
  local installation/listing still succeeded. That warning does not verify remote
  catalog connectivity or account-wide plugin availability.
- Executor skill enumeration returned an empty list. **Automatic hot-loading into
  this already-running conversation is not verified.** Native installation is
  verified; direct reading of cached guidance works now. The documented activation
  step is to start a new Codex session. This is not a ChatGPT Apps connector or a
  new MCP payment tool.
- Fresh-task restoration/publication of this environment was not tested. These
  records are reproducible steps, not a claim that home-directory state survives
  every task. Recheck local registration and cached files in future tasks.

## Guidance available now

The cached plugin contains Python, TypeScript, and .NET guidance for getting
started, client initialization, OAuth client-credentials authentication, endpoint
calls, models, error handling, configuration/retries, testing, and integration
planning. Python also has file-handling and event-stream guidance.

For this FastAPI backend, start with
`skills/python/python-getting-started/SKILL.md`, then the relevant companion skills.
The entry point describes Orders (including create/capture), Payments/refunds,
Subscriptions, Transaction Search, and Vault; it links to source-grounded operation
maps and SDK code. It describes an APIMatic-generated Python SDK snapshot 2.29 at
https://github.com/context-plugins/paypal-python-sdk, not an SDK installed by this
setup. Contract facts must be reverified against the eventual pinned SDK source
before implementation; the plugin's version and the SDK's version are different.

The plugin contains workflow guidance on durable duplicate-operation claims,
provider idempotency, retries, typed errors, and testing. It does not establish
that PayPal webhook verification is implemented or that all Phase 2 API surfaces
are covered. PayPal-specific webhook verification still needs authoritative
provider documentation and explicit contract verification in the payment task.

Only Sandbox operations are authorized for this project. SDK credentials stay in
the backend. Do not install an SDK, request secrets, run payment smoke tests, or
create payment functionality as part of this guidance-only setup. Project rules
and the user's authorized scope take precedence over generic plugin workflows.
