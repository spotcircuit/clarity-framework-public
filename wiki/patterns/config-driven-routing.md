# Config-Driven Routing

Put routing logic in configuration, not code. When the routing rules change, update a config file or YAML entry instead of modifying application code, running tests, and redeploying.

## The pattern

Define routing rules as data. The application reads the rules and applies them. Adding a new route means adding a config entry, not a code change.

```yaml
# deploy_routing.yaml
routes:
  - match: { deploy_target: "cloudflare" }
    handler: cloudflare_deployer
    config:
      api_token_env: CLOUDFLARE_API_TOKEN
      account_id_env: CLOUDFLARE_ACCOUNT_ID

  - match: { deploy_target: "vercel" }
    handler: vercel_deployer
    config:
      token_env: VERCEL_TOKEN

  - match: { deploy_target: "auto" }
    handler: auto_select
    priority: [cloudflare_deployer, vercel_deployer]
    rule: "first configured provider wins"

  - match: { deploy_target: "none" }
    handler: skip
    note: "local preview only, no deployment"
```

## Router implementation

```python
class ConfigRouter:
    def __init__(self, routes: list[dict]):
        self._routes = routes

    def resolve(self, **context) -> dict:
        """Find the first matching route for the given context."""
        for route in self._routes:
            if all(context.get(k) == v for k, v in route["match"].items()):
                return route
        raise NoRouteError(f"No route matches: {context}")
```

## Real example: site-builder deploy resolution

The site-builder uses this pattern for choosing where to deploy generated sites. From the expertise.yaml:

```
Auto-selection priority:
1. If user explicitly picks "cloudflare" or "vercel", use that
2. If "auto" or unset: prefer Cloudflare if configured, else Vercel
3. If "none": skip deployment entirely (local preview only)
```

This is config, not a chain of if/else statements. Adding a new deploy target (Netlify, S3, etc.) means adding a config entry and a deployer module. The pipeline orchestrator does not change.

## Real example: Node-RED flow routing (Acme Integration)

The push agent routes flow deployments based on configuration:

```yaml
deployment:
  environments:
    staging:
      tenant_id_env: STAGING_TENANT_ID
      auto_deploy: true
    production:
      tenant_id_env: PROD_TENANT_ID
      auto_deploy: false  # manual promotion only
```

Adding a new environment (QA, load-test, demo) means adding a YAML entry. The push agent reads the config and deploys accordingly. No code changes needed.

## When to use it

- Multiple deployment targets or environments
- Feature flags and A/B routing
- Multi-tenant systems where tenants have different configurations
- Any place where `if provider == "x"` chains are growing

## When not to use it

- Simple two-way decisions that will not grow
- Performance-critical hot paths where config lookup overhead matters
- Routing logic that requires complex computation (use code, not config)

## Related

- [Correlation ID](correlation-id.md) -- Route decisions can be logged with correlation IDs for debugging
- [Idempotency Guard](idempotency-guard.md) -- Idempotency TTL can be configured per-route
