# Test cases for Error Handling Quality
# Scoring formula: 
#   Base: 0.0
#   Specificity: (specific / total) * 0.20
#   Global Handlers: +0.20
#   JSON Response: +0.15
#   Logging: +0.20
#   No Traceback Leak: +0.10 (or -0.15 if leak)
#   DB Failure Handling: +0.15
#   Penalties: Bare (-0.10), Swallowed (-0.12), No handling at all (-0.10)

TEST_CASES = [
    {
        "id": "perfect_error_handling",
        "description": "Specific exceptions, logging, JSON, DB protection, and global handler",
        "code": """
@app.errorhandler(HTTPException)
def handle_error(e):
    return jsonify({"error": "An error occurred"}), 500

def create_user():
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        logger.exception("DB Integrity Error")
        return jsonify({"status": "error", "message": "User exists"}), 400
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({"status": "error", "message": "Invalid input provided"}), 422
""",
        "expected_score": 1.0 # 0.20(spec) + 0.20(global) + 0.15(json) + 0.20(log) + 0.10(no_leak) + 0.15(db) = 1.0
    },
    {
        "id": "silent_swallow_bare",
        "description": "Bare except that silently swallows exceptions (Terrible)",
        "code": """
def risky_op():
    try:
        x = 1 / 0
    except:
        pass
""",
        "expected_score": 0.0 # Ratio: 0/1 * 0.2 = 0. -0.10(bare) - 0.12(swallow) + 0.10(no leak) = -0.12 -> max(0, -0.12) = 0.0
    },
    {
        "id": "traceback_leakage",
        "description": "Broad exception with traceback leak to client",
        "code": """
def get_data():
    try:
        res = db.fetch()
    except Exception as e:
        return {"error": traceback.format_exc()}
""",
        "expected_score": 0.0 # Ratio 0/1. Leak penalty -0.15. No logging 0. No DB 0. Score: -0.15 -> 0.0
    },
    {
        "id": "broad_with_logging",
        "description": "Broad exception handling but with proper logging and JSON response",
        "code": """
def process():
    try:
        do_work()
    except Exception as e:
        logger.error(f"Failed: {e}")
        return jsonify({"message": "internal error"})
""",
        "expected_score": 0.45 # Ratio 0/1. Logging +0.20. JSON +0.15. No Leak +0.10. = 0.45
    },
    {
        "id": "minimal_db_protection",
        "description": "Only DB protection without logging or global handlers",
        "code": """
def save():
    try:
        db.execute("INSERT...")
    except OperationalError:
        db.rollback()
        return {"status": "failed"}
""",
        "expected_score": 0.60 # Ratio 1/1 * 0.20. JSON +0.15. DB +0.15. No Leak +0.10. = 0.60
    },
    {
        "id": "fastapi_global_handler",
        "description": "FastAPI style exception handler for custom validation errors",
        "code": """
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(status_code=400, content={"detail": exc.errors()})
""",
        "expected_score": 0.35 
    },
    {
        "id": "nested_try_except_good",
        "description": "Properly nested try-except with logging at each level",
        "code": """
def nested_op():
    try:
        try:
            call_api()
        except ConnectionError:
            logger.warning("Retrying...")
            call_api()
    except RequestException as e:
        logger.error(f"External API failed: {e}")
        return {"error": "service unavailable"}
""",
        "expected_score": 0.65 
    },
    {
        "id": "django_transaction_atomic",
        "description": "Django style transaction management with specific error catching",
        "code": """
from django.db import transaction
def create_order():
    try:
        with transaction.atomic():
            Order.objects.create(id=1)
    except IntegrityError:
        transaction.rollback()
        return Response({"status": "error"}, status=400)
""",
        "expected_score": 0.60 
    },
    {
        "id": "broad_exception_with_repr_leak",
        "description": "Broad exception catching and returning repr(e) to client (Leak)",
        "code": """
def get_user():
    try:
        return User.objects.get(id=1)
    except Exception as e:
        return {"debug": repr(e)}
""",
        "expected_score": 0.0 
    },
    {
        "id": "multiple_specific_exceptions",
        "description": "Catching multiple specific exceptions in a single block",
        "code": """
def load_config():
    try:
        with open('config.json') as f:
            data = json.load(f)
    except (FileNotFoundError, PermissionError) as e:
        logger.error(f"Config error: {e}")
        return jsonify({"error": "config_missing"})
""",
        "expected_score": 0.65 
    },
    {
        "id": "ellipsis_swallow",
        "description": "Swallowing exceptions using Ellipsis (...) - modern but bad",
        "code": """
def ignore_errors():
    try:
        do_something()
    except Exception:
        ...
""",
        "expected_score": 0.0 
    },
    {
        "id": "sqlalchemy_rollback_pattern",
        "description": "Typical SQLAlchemy session management with rollback and close",
        "code": """
def save_item(item):
    try:
        session.add(item)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        return {"error": "db_error"}
    finally:
        session.close()
""",
        "expected_score": 0.60 
    },
    {
        "id": "broad_exception_with_logging_only",
        "description": "Broad exception with logging but no JSON response structure",
        "code": """
def run():
    try:
        main_loop()
    except Exception as e:
        logger.exception("Crashed")
""",
        "expected_score": 0.30 
    },
    {
        "id": "traceback_print_exc_leak",
        "description": "Using traceback.print_exc() which might leak to logs/stdout",
        "code": """
def execute():
    try:
        run_command()
    except Exception as e:
        traceback.print_exc()
        return "Internal Error"
""",
        "expected_score": 0.0 
    },
    {
        "id": "custom_exception_handling",
        "description": "Catching a custom domain-specific exception",
        "code": """
def checkout():
    try:
        cart.process()
    except InsufficientFundsError as e:
        return jsonify({"error": "no_money"})
""",
        "expected_score": 0.45 
    },
    {
        "id": "bare_except_with_logging",
        "description": "Bare except with logging (Better than nothing, but still bad)",
        "code": """
def unsafe():
    try:
        work()
    except:
        logger.error("Something went wrong")
""",
        "expected_score": 0.20 
    },
    {
        "id": "good_retry_loop",
        "description": "A retry loop with proper error handling and backoff",
        "code": """
def fetch_with_retry():
    for i in range(3):
        try:
            return requests.get(URL)
        except RequestException:
            logger.warning(f"Attempt {i} failed")
            time.sleep(1)
    return None
""",
        "expected_score": 0.50 
    },
    {
        "id": "base_exception_catch",
        "description": "Catching BaseException (Very broad, usually bad practice)",
        "code": """
def kill_proof():
    try:
        infinite_loop()
    except BaseException:
        logger.critical("Captured BaseException!")
""",
        "expected_score": 0.30 
    },
    {
        "id": "fastapi_http_exception",
        "description": "Raising and catching HTTPException in FastAPI",
        "code": """
def get_item(id):
    try:
        return db.get(id)
    except HTTPException:
        raise
""",
        "expected_score": 0.30 
    },
    {
        "id": "multi_framework_error_middleware",
        "description": "Express-like or Custom middleware error handler structure",
        "code": """
class ErrorMiddleware:
    def __init__(self, app):
        self.app = app
    async def __call__(self, scope, receive, send):
        try:
            await self.app(scope, receive, send)
        except Exception as e:
            logger.error(f"Middleware caught: {e}")
            await send({"type": "http.response.start", "status": 500})
""",
        "expected_score": 0.50 
    }
]
