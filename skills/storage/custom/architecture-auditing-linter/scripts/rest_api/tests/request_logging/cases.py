# =============================================================================
# Structured Request Logging — Test Dataset
#
# Sources:
#   - Google API Design Guide (AIP-0151: observability, AIP-0162: request IDs)
#   - Microsoft REST API Guidelines (request-id, correlation ID)
#   - GitHub REST API conventions (X-GitHub-Request-Id header)
#   - OpenTelemetry specification (trace context propagation)
#   - OWASP Logging Cheat Sheet (no sensitive data in logs)
#
# Scoring model (additive, max 1.0):
#   0.25 — Request ID / correlation ID generated and propagated
#   0.25 — Structured logger + method + path + status all logged
#   0.20 — Latency / response time logged
#   0.15 — X-Request-ID header returned to client
#   0.10 — Middleware / lifecycle hook present
#   0.05 — Structured format (JSON or key=value fields)
#
# Penalty:
#   -0.30 — print() used for request logging
#    0.00 — Sensitive data (password/token) in log lines (OWASP critical)
# =============================================================================

TEST_CASES = [

    # =========================================================================
    # BLOCK 1 — Perfect Structured Logging (score = 1.0)
    # Request ID + structured logger + method/path/status + latency + X-header.
    # =========================================================================

    {
        "id": "perfect_fastapi_middleware",
        "description": "FastAPI middleware: uuid request_id, logger, method/path/status, latency, X-Request-ID",
        "expected_score": 1.0,
        "code": """
import uuid, time, logging
logger = logging.getLogger("api")

@app.middleware("http")
async def log_requests(request, call_next):
    request_id = str(uuid.uuid4())
    start = time.time()
    response = await call_next(request)
    latency_ms = round((time.time() - start) * 1000, 2)
    logger.info(
        "request_id=%s method=%s path=%s status=%d latency_ms=%.2f",
        request_id, request.method, str(request.url.path),
        response.status_code, latency_ms,
    )
    response.headers["X-Request-ID"] = request_id
    return response
""",
    },

    {
        "id": "perfect_flask_before_after",
        "description": "Flask before/after_request: uuid, logger, method/path/status, latency, X-Request-ID",
        "expected_score": 1.0,
        "code": """
import uuid, time, logging
logger = logging.getLogger("flask.app")

@app.before_request
def start_timer():
    g.start_time = time.time()
    g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

@app.after_request
def log_request(response):
    latency_ms = (time.time() - g.start_time) * 1000
    logger.info(
        "request_id=%s method=%s path=%s status=%d latency_ms=%.2f",
        g.request_id, request.method, request.path,
        response.status_code, latency_ms,
    )
    response.headers["X-Request-ID"] = g.request_id
    return response
""",
    },

    {
        "id": "perfect_express_morgan",
        "description": "Express: morgan JSON format + uuid X-Request-ID header propagation",
        "expected_score": 0.8,
        "code": """
const morgan = require('morgan');
const { v4: uuidv4 } = require('uuid');

app.use((req, res, next) => {
    req.requestId = req.headers['x-request-id'] || uuidv4();
    res.setHeader('X-Request-ID', req.requestId);
    next();
});

morgan.token('request-id', (req) => req.requestId);
app.use(morgan(JSON.stringify({
    requestId: ':request-id',
    method: ':method',
    url: ':url',
    status: ':status',
    latencyMs: ':response-time',
})));
""",
    },

    {
        "id": "perfect_spring_filter",
        "description": "Spring OncePerRequestFilter: MDC request_id, method, path, status, latency",
        "expected_score": 1.0,
        "code": """
@Component
public class RequestLoggingFilter extends OncePerRequestFilter {
    private static final Logger log = LoggerFactory.getLogger(RequestLoggingFilter.class);

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                     HttpServletResponse response,
                                     FilterChain chain) throws ServletException, IOException {
        String requestId = Optional.ofNullable(request.getHeader("X-Request-ID"))
            .orElse(UUID.randomUUID().toString());
        MDC.put("requestId", requestId);
        long start = System.currentTimeMillis();
        try {
            chain.doFilter(request, response);
        } finally {
            long latency = System.currentTimeMillis() - start;
            log.info("method={} path={} status={} latency_ms={} request_id={}",
                request.getMethod(), request.getRequestURI(),
                response.getStatus(), latency, requestId);
            response.addHeader("X-Request-ID", requestId);
            MDC.clear();
        }
    }
}
""",
    },

    # =========================================================================
    # BLOCK 2 — Good but Missing Latency (score = 0.6–0.8)
    # =========================================================================

    {
        "id": "good_missing_latency",
        "description": "Structured logging: request_id, method, path, status — but no latency",
        "expected_score": 0.8,
        "code": """
import uuid, logging
logger = logging.getLogger("api")

@app.middleware("http")
async def log_requests(request, call_next):
    request_id = str(uuid.uuid4())
    response = await call_next(request)
    logger.info(
        "request_id=%s method=%s path=%s status=%d",
        request_id, request.method, str(request.url.path), response.status_code,
    )
    response.headers["X-Request-ID"] = request_id
    return response
""",
    },

    {
        "id": "good_missing_xheader",
        "description": "Structured logging: request_id, method, path, status, latency — no X-Request-ID header returned",
        "expected_score": 0.55,
        "code": """
import uuid, time, logging
logger = logging.getLogger("api")

@app.middleware("http")
async def log_requests(request, call_next):
    start = time.time()
    response = await call_next(request)
    latency_ms = round((time.time() - start) * 1000, 2)
    logger.info(
        "method=%s path=%s status=%d latency_ms=%.2f",
        request.method, str(request.url.path),
        response.status_code, latency_ms,
    )
    return response
""",
    },

    # =========================================================================
    # BLOCK 3 — Basic Logging Only (score = 0.25)
    # Logger present, method+path logged — no request_id, latency, or header.
    # =========================================================================

    {
        "id": "basic_logger_no_id",
        "description": "Basic logger with method+path only — no request_id, no latency, no X-header",
        "expected_score": 0.25,
        "code": """
import logging
logger = logging.getLogger(__name__)

@app.before_request
def log_incoming():
    logger.info(f"Request: {request.method} {request.path}")
""",
    },

    # =========================================================================
    # BLOCK 4 — No Logging (score = 0.0)
    # Routes present but zero request lifecycle logging.
    # =========================================================================

    {
        "id": "no_logging_flask",
        "description": "Flask routes with no before_request, after_request, or logger",
        "expected_score": 0.0,
        "code": """
@app.get("/orders")
def list_orders():
    return jsonify(orders=[])
""",
    },

    {
        "id": "no_logging_express",
        "description": "Express: no morgan, no logger, no request lifecycle tracking",
        "expected_score": 0.0,
        "code": """
app.get('/users', (req, res) => {
    res.json({ users: [] });
});
""",
    },

    # =========================================================================
    # BLOCK 5 — Security Violations (score = 0.0)
    # OWASP Logging Cheat Sheet: sensitive data must never appear in log lines.
    # =========================================================================

    {
        "id": "sensitive_password_in_log",
        "description": "OWASP VIOLATION: password logged in plain text → instant 0.0",
        "expected_score": 0.0,
        "code": """
import logging
logger = logging.getLogger("auth")
logger.info("Login attempt: password=%s", password)
""",
    },

    {
        "id": "sensitive_token_in_log",
        "description": "OWASP VIOLATION: Authorization token logged → instant 0.0",
        "expected_score": 0.0,
        "code": """
import logging
logger = logging.getLogger("api")
token = request.headers.get("Authorization")
logger.info("Request %s %s token=%s", request.method, request.path, token)
""",
    },

    # =========================================================================
    # BLOCK 6 — print() Anti-Pattern (score = 0.0)
    # print() used for request logging — invisible in production.
    # =========================================================================

    {
        "id": "print_for_logging",
        "description": "print() used for request lifecycle — anti-pattern, no severity, invisible in prod",
        "expected_score": 0.0,
        "code": """
@app.before_request
def log_request():
    print(f"method={request.method} path={request.path}")

@app.after_request
def log_response(response):
    print(f"status={response.status_code}")
    return response
""",
    },

]
