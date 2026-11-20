import { NextRequest, NextResponse } from "next/server";

const API_INTERNAL_URL = (
  process.env.API_INTERNAL_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

let cachedIdToken: { token: string; expiresAt: number } | null = null;

/**
 * Obtiene un token OIDC de servicio desde el Metadata Server de Google Cloud Run
 * para llamadas autenticadas servicio-a-servicio (cymbal-riesgo-web -> cymbal-riesgo-api)
 * cuando la política organizacional bloquea 'allUsers'.
 */
async function getCloudRunIdToken(audience: string): Promise<string | null> {
  if (!audience.startsWith("https://")) {
    return null;
  }
  const now = Date.now();
  if (cachedIdToken && cachedIdToken.expiresAt > now) {
    return cachedIdToken.token;
  }
  try {
    const metadataUrl =
      "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience=" +
      encodeURIComponent(audience);
    const res = await fetch(metadataUrl, {
      headers: { "Metadata-Flavor": "Google" },
      signal: AbortSignal.timeout(1500),
    });
    if (!res.ok) return null;
    const token = (await res.text()).trim();
    if (!token) return null;
    cachedIdToken = { token, expiresAt: now + 45 * 60 * 1000 };
    return token;
  } catch {
    return null;
  }
}

async function proxyToApi(
  req: NextRequest,
  context: { params: Promise<{ path: string[] }> }
): Promise<NextResponse> {
  const { path } = await context.params;
  const targetUrl = `${API_INTERNAL_URL}/api/v1/${path.join("/")}${req.nextUrl.search}`;

  const forwardHeaders = new Headers();
  const passThrough = [
    "content-type",
    "accept",
    "x-cymbal-role",
    "x-cymbal-user",
    "authorization",
  ];
  for (const key of passThrough) {
    const val = req.headers.get(key);
    if (val) forwardHeaders.set(key, val);
  }

  // En Cloud Run con IAM privado, inyecta ID token de servicio si el cliente no envió Bearer
  if (!forwardHeaders.has("authorization")) {
    const idToken = await getCloudRunIdToken(API_INTERNAL_URL);
    if (idToken) {
      forwardHeaders.set("authorization", `Bearer ${idToken}`);
    }
  }

  const hasBody = !["GET", "HEAD"].includes(req.method.toUpperCase());
  const body = hasBody ? await req.arrayBuffer() : undefined;

  try {
    const upstream = await fetch(targetUrl, {
      method: req.method,
      headers: forwardHeaders,
      body,
      cache: "no-store",
    });

    const responseHeaders = new Headers();
    const contentType = upstream.headers.get("content-type");
    if (contentType) responseHeaders.set("content-type", contentType);
    const latency = upstream.headers.get("x-response-time-ms");
    if (latency) responseHeaders.set("x-response-time-ms", latency);
    const slo = upstream.headers.get("x-slo-target-ms");
    if (slo) responseHeaders.set("x-slo-target-ms", slo);

    return new NextResponse(upstream.body, {
      status: upstream.status,
      headers: responseHeaders,
    });
  } catch (err) {
    return NextResponse.json(
      {
        detail:
          err instanceof Error
            ? `No se pudo contactar cymbal-riesgo-api: ${err.message}`
            : "Error de conexión con cymbal-riesgo-api.",
      },
      { status: 502 }
    );
  }
}

export const GET = proxyToApi;
export const POST = proxyToApi;
export const PATCH = proxyToApi;
export const PUT = proxyToApi;
export const DELETE = proxyToApi;
