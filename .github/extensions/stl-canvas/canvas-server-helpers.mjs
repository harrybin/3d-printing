export function createModelApiPayload({
    requested,
    resolved,
    parsed,
    content,
    mtime,
}) {
    return {
        path: requested,
        stats: {
            ...parsed,
            triangles: undefined,
            triangleColors: undefined,
            plates: undefined,
        },
        triangles: parsed.triangles || [],
        triangleColors: parsed.triangleColors || [],
        plates: parsed.plates || [],
        projectMetadata: parsed.projectMetadata || {},
        modelPath: resolved,
        content,
        mtime,
    };
}

export async function handleOrcaOpenRequest(req, res, {
    defaultModelPath,
    expectedNonce,
    validate,
    launch,
}) {
    try {
        let body = "";
        for await (const chunk of req) {
            body += chunk;
            if (body.length > 10000) throw new Error("Request body is too large.");
        }
        const input = JSON.parse(body || "{}");
        if (!expectedNonce || input.nonce !== expectedNonce) {
            res.statusCode = 403;
            res.setHeader("Content-Type", "application/json; charset=utf-8");
            res.end(JSON.stringify({ ok: false, error: "Forbidden" }));
            return;
        }
        const requestedPath = input.modelPath || defaultModelPath;
        const resolved = validate(requestedPath);
        const executable = await launch(resolved);
        res.setHeader("Content-Type", "application/json; charset=utf-8");
        res.end(JSON.stringify({ ok: true, executable, file: resolved }));
    } catch (error) {
        res.statusCode = 500;
        res.setHeader("Content-Type", "application/json; charset=utf-8");
        res.end(JSON.stringify({ ok: false, error: String(error) }));
    }
}
