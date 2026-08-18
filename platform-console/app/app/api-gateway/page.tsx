import Nav from "@/components/Nav";

export default function ApiGatewayPage() {
  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">
          API Gateway Rate Limiting
        </h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          This page documents a real, enforced control &mdash; it does not
          configure anything itself. The limit is enacted entirely by Istio
          at the ingress gateway&apos;s data plane, the same layer AWS API
          Gateway throttling, GCP Cloud Endpoints quotas, and Azure API
          Management rate-limit policies occupy in their respective
          ecosystems.
        </p>

        <div className="card mb-8 p-6">
          <h2 className="mb-4 text-base font-medium text-white">
            Configured limit
          </h2>
          <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-gray-500">Scope</dt>
              <dd className="text-gray-200">
                platform-console route only (<code>platform-console-root</code>)
              </dd>
            </div>
            <div>
              <dt className="text-gray-500">Enforcement point</dt>
              <dd className="text-gray-200">istio-ingressgateway</dd>
            </div>
            <div>
              <dt className="text-gray-500">Mechanism</dt>
              <dd className="text-gray-200">
                envoy.filters.http.local_ratelimit (token bucket)
              </dd>
            </div>
            <div>
              <dt className="text-gray-500">Rate</dt>
              <dd className="text-gray-200">20 requests / 60s per gateway worker</dd>
            </div>
            <div>
              <dt className="text-gray-500">Bucket</dt>
              <dd className="text-gray-200">
                max_tokens 20, tokens_per_fill 20, fill_interval 60s
              </dd>
            </div>
            <div>
              <dt className="text-gray-500">Over-limit response</dt>
              <dd className="text-gray-200">
                429 Too Many Requests, header <code>x-local-rate-limit: true</code>
              </dd>
            </div>
          </dl>
        </div>

        <div className="card mb-8 p-6">
          <h2 className="mb-3 text-base font-medium text-white">
            Why the Grafana route on the same gateway is unaffected
          </h2>
          <p className="text-sm text-gray-300">
            <code>platform.local</code> is served by two VirtualServices on
            the same shared <code>platform-console-gateway</code>:{" "}
            <code>grafana-route</code> (<code>/grafana/*</code>) and{" "}
            <code>platform-console-ingress</code> (catch-all{" "}
            <code>/</code>, named route <code>platform-console-root</code>).
            The rate limit is installed as two EnvoyFilters: one inserts the
            local_ratelimit HTTP filter into the gateway&apos;s filter chain
            with no bucket configured (a no-op everywhere by default); the
            second merges a <code>typed_per_filter_config</code> override
            onto exactly the <code>platform-console-root</code> route by
            name. No other route on the shared gateway carries that
            override, so Grafana traffic is untouched.
          </p>
        </div>

        <div className="card p-6">
          <h2 className="mb-3 text-base font-medium text-white">
            Source of truth &amp; verification
          </h2>
          <p className="text-sm text-gray-300">
            The full EnvoyFilter definitions live in{" "}
            <code>k8s/ratelimit.yaml</code>. The route name they target is
            defined in <code>k8s/gateway.yaml</code>. Enforcement was
            verified live against the real ingress gateway: a 35-request
            burst against <code>platform.local</code> returned{" "}
            <code>307</code> for the first 20 requests, then real{" "}
            <code>429</code> responses (with{" "}
            <code>x-local-rate-limit: true</code>) for the rest, and a
            request issued after waiting past the 60s fill_interval
            succeeded again (<code>307</code>) &mdash; see{" "}
            <code>README.md</code> and{" "}
            <code>evidence/control-evidence-bundle.json</code> (control{" "}
            <code>rate-limiting-enforced</code>) for the full transcript.
          </p>
        </div>
      </main>
    </>
  );
}
