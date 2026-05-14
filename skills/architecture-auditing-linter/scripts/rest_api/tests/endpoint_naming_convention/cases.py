# =============================================================================
# Endpoint Naming Convention — Comprehensive Test Dataset
#
# Scope: ONLY evaluates whether the URL path follows REST naming conventions.
# Out of scope: HTTP method correctness, caching, error handling, rate limiting.
#
# Scoring Formula (start from 1.0, deduct penalties):
#   Verb in path segment          : -0.25 per verb segment
#   camelCase (consolidated)      : -0.20
#   snake_case (consolidated)     : -0.10
#   Uppercase letters             : -0.20
#   Singular collection resource  : -0.15
#   Nesting depth > 4 levels      : -0.10 per extra level
#   Trailing slash                : -0.10
#   File extension in path        : -0.20
#   Special characters (!@#$+.)   : -0.20
#   Consecutive slashes           : -0.20
#   CRUD verb disguised as noun   : -0.20
#   Bad version format            : -0.15
#   Version not at root           : -0.10
#   Non-integer version           : -0.10
#   Bad path param naming         : -0.10 per param
#   Redundant resource in param   : -0.05 per param
#   Query param embedded in path  : -0.25
#   Action without /actions/      : -0.15
#   Non-descriptive param name    : -0.10 per param
#   Minimum score floor           : 0.0
# =============================================================================

TEST_CASES = [

    # =========================================================================
    # BLOCK 1 — Perfect Cases (score = 1.0)
    # These are the gold standard. Nothing to penalize.
    # =========================================================================

    {
        "id": "perfect_plural_kebab",
        "description": "Standard lowercase kebab-case plural collection",
        "violations": [],
        "code": '@app.get("/user-profiles")',
        "expected_score": 1.0
    },
    {
        "id": "perfect_root",
        "description": "Root path — always valid",
        "violations": [],
        "code": '@app.get("/")',
        "expected_score": 1.0
    },
    {
        "id": "perfect_param_after_plural",
        "description": "Plural collection followed by path param — correct REST pattern",
        "violations": [],
        "code": '@app.get("/users/{id}")',
        "expected_score": 1.0
    },
    {
        "id": "perfect_versioned",
        "description": "Version prefix at root, plural resource",
        "violations": [],
        "code": '@app.get("/v1/users")',
        "expected_score": 1.0
    },
    {
        "id": "perfect_nested_two_levels",
        "description": "Two-level nesting — parent resource / child resource",
        "violations": [],
        "code": '@app.get("/users/{id}/orders")',
        "expected_score": 1.0
    },
    {
        "id": "perfect_nested_three_levels",
        "description": "Three-level nesting — still within depth limit",
        "violations": [],
        "code": '@app.get("/users/{id}/orders/{order_id}/items")',
        "expected_score": 1.0
    },
    {
        "id": "perfect_nested_four_levels",
        "description": "Four-level nesting — exactly at the depth limit",
        "violations": [],
        "code": '@app.get("/orgs/{id}/teams/{team_id}/members/{member_id}")',
        "expected_score": 1.0
    },
    {
        "id": "perfect_action_namespace",
        "description": "Action endpoint correctly under /actions/ namespace",
        "violations": [],
        "code": '@app.post("/actions/recalculate-scores")',
        "expected_score": 1.0
    },
    {
        "id": "perfect_resource_action",
        "description": "Resource-scoped action under /actions/",
        "violations": [],
        "code": '@app.post("/users/{id}/actions/activate")',
        "expected_score": 1.0
    },
    {
        "id": "perfect_versioned_nested",
        "description": "Versioned API with nested resource",
        "violations": [],
        "code": '@app.get("/v2/products/{id}/reviews")',
        "expected_score": 1.0
    },
    {
        "id": "perfect_hyphenated_resource",
        "description": "Multi-word resource using kebab-case",
        "violations": [],
        "code": '@app.get("/order-items/{id}")',
        "expected_score": 1.0
    },
    {
        "id": "perfect_singleton_sub_resource",
        "description": "Singleton sub-resource (profile of a user) — singular is correct here",
        "violations": [],
        "code": '@app.get("/users/{id}/profile")',
        "expected_score": 1.0
    },
    {
        "id": "perfect_health_check",
        "description": "Standard health check endpoint — technical keyword exception",
        "violations": [],
        "code": '@app.get("/health")',
        "expected_score": 1.0
    },
    {
        "id": "perfect_metrics",
        "description": "Standard metrics endpoint — technical keyword exception",
        "violations": [],
        "code": '@app.get("/metrics")',
        "expected_score": 1.0
    },
    {
        "id": "perfect_search_under_resource",
        "description": "Search as sub-resource — acceptable pattern",
        "violations": [],
        "code": '@app.get("/products/search")',
        "expected_score": 1.0
    },
    {
        "id": "perfect_v2_new_resource",
        "description": "v2 versioned resource with kebab-case",
        "violations": [],
        "code": '@app.get("/v2/payment-methods")',
        "expected_score": 1.0
    },

    # =========================================================================
    # BLOCK 2 — Verb in Path (-0.25 per verb segment)
    # =========================================================================

    {
        "id": "verb_get_prefix",
        "description": "Verb 'get' as path prefix",
        "violations": ["verb_in_path: get"],
        "code": '@app.get("/get-users")',
        "expected_score": 0.75
    },
    {
        "id": "verb_fetch_prefix",
        "description": "Verb 'fetch' as path prefix",
        "violations": ["verb_in_path: fetch"],
        "code": '@app.get("/fetch-orders")',
        "expected_score": 0.75
    },
    {
        "id": "verb_create_prefix",
        "description": "Verb 'create' in path",
        "violations": ["verb_in_path: create"],
        "code": '@app.post("/create-user")',
        "expected_score": 0.75
    },
    {
        "id": "verb_update_prefix",
        "description": "Verb 'update' in path",
        "violations": ["verb_in_path: update"],
        "code": '@app.put("/update-profile")',
        "expected_score": 0.75
    },
    {
        "id": "verb_delete_in_path",
        "description": "Verb 'delete' explicitly in path",
        "violations": ["verb_in_path: delete"],
        "code": '@app.delete("/delete-record/{id}")',
        "expected_score": 0.75
    },
    {
        "id": "verb_list_prefix",
        "description": "Verb 'list' as path segment",
        "violations": ["verb_in_path: list"],
        "code": '@app.get("/list-products")',
        "expected_score": 0.75
    },
    {
        "id": "verb_add_prefix",
        "description": "Verb 'add' as path segment",
        "violations": ["verb_in_path: add"],
        "code": '@app.post("/add-item")',
        "expected_score": 0.75
    },
    {
        "id": "verb_remove_in_path",
        "description": "Verb 'remove' in path",
        "violations": ["verb_in_path: remove"],
        "code": '@app.delete("/remove-member/{id}")',
        "expected_score": 0.75
    },
    {
        "id": "verb_submit_in_path",
        "description": "Verb 'submit' as path segment",
        "violations": ["verb_in_path: submit"],
        "code": '@app.post("/submit-form")',
        "expected_score": 0.75
    },
    {
        "id": "verb_process_in_path",
        "description": "Verb 'process' as path segment",
        "violations": ["verb_in_path: process"],
        "code": '@app.post("/process-payment")',
        "expected_score": 0.75
    },
    {
        "id": "two_verbs_in_path",
        "description": "Two verb segments in path (-0.25 each)",
        "violations": ["verb_in_path: get", "verb_in_path: list"],
        "code": '@app.get("/get-and-list-users")',
        "expected_score": 0.50
    },
    {
        "id": "verb_and_camel",
        "description": "Verb 'fetch' + camelCase compound penalty",
        "violations": ["verb_in_path: fetch", "camelCase"],
        "code": '@app.get("/fetchUserProfiles")',
        "expected_score": 0.55
    },
    {
        "id": "verb_check_in_path",
        "description": "Verb 'check' in path",
        "violations": ["verb_in_path: check"],
        "code": '@app.get("/check-status")',
        "expected_score": 0.75
    },
    {
        "id": "verb_verify_in_path",
        "description": "Verb 'verify' in path",
        "violations": ["verb_in_path: verify"],
        "code": '@app.post("/verify-token")',
        "expected_score": 0.75
    },
    {
        "id": "verb_send_in_path",
        "description": "Verb 'send' in path",
        "violations": ["verb_in_path: send"],
        "code": '@app.post("/send-notification")',
        "expected_score": 0.75
    },
    {
        "id": "verb_generate_in_path",
        "description": "Verb 'generate' in path",
        "violations": ["verb_in_path: generate"],
        "code": '@app.post("/generate-report")',
        "expected_score": 0.75
    },
    {
        "id": "verb_export_in_path",
        "description": "Verb 'export' in path",
        "violations": ["verb_in_path: export"],
        "code": '@app.get("/export-data")',
        "expected_score": 0.75
    },
    {
        "id": "verb_import_in_path",
        "description": "Verb 'import' in path",
        "violations": ["verb_in_path: import"],
        "code": '@app.post("/import-records")',
        "expected_score": 0.75
    },

    # =========================================================================
    # BLOCK 3 — Casing Violations
    # camelCase: -0.20 | snake_case: -0.10 | Uppercase: -0.20
    # =========================================================================

    {
        "id": "camel_case_single_word",
        "description": "camelCase single compound word",
        "violations": ["camelCase"],
        "code": '@app.get("/userProfiles")',
        "expected_score": 0.80
    },
    {
        "id": "camel_case_nested",
        "description": "camelCase in nested path",
        "violations": ["camelCase"],
        "code": '@app.get("/users/{id}/orderItems")',
        "expected_score": 0.80
    },
    {
        "id": "snake_case_single",
        "description": "snake_case in single segment",
        "violations": ["snake_case"],
        "code": '@app.get("/user_profiles")',
        "expected_score": 0.90
    },
    {
        "id": "snake_case_nested",
        "description": "snake_case in nested path",
        "violations": ["snake_case"],
        "code": '@app.get("/users/{id}/order_items")',
        "expected_score": 0.90
    },
    {
        "id": "uppercase_first_letter",
        "description": "First letter uppercase",
        "violations": ["uppercase"],
        "code": '@app.get("/Users")',
        "expected_score": 0.80
    },
    {
        "id": "uppercase_full_segment",
        "description": "Full uppercase segment",
        "violations": ["uppercase"],
        "code": '@app.get("/USERS")',
        "expected_score": 0.80
    },
    {
        "id": "uppercase_nested",
        "description": "Uppercase in nested path segment",
        "violations": ["uppercase"],
        "code": '@app.get("/users/{id}/Orders")',
        "expected_score": 0.80
    },
    {
        "id": "mixed_camel_and_snake",
        "description": "Mixed camelCase and snake_case in same path — camel penalty dominates",
        "violations": ["camelCase"],
        "code": '@app.get("/userProfiles/order_items")',
        "expected_score": 0.80
    },
    {
        "id": "pascal_case_segment",
        "description": "PascalCase — treated as uppercase violation",
        "violations": ["uppercase"],
        "code": '@app.get("/UserProfiles")',
        "expected_score": 0.80
    },
    {
        "id": "screaming_snake_case",
        "description": "SCREAMING_SNAKE_CASE — both uppercase and snake violations",
        "violations": ["uppercase", "snake_case"],
        "code": '@app.get("/USER_PROFILES")',
        "expected_score": 0.70
    },

    # =========================================================================
    # BLOCK 4 — Plurality Violations (-0.15)
    # Collection endpoint must use plural nouns.
    # =========================================================================

    {
        "id": "singular_collection",
        "description": "Singular noun for a collection resource",
        "violations": ["singular_resource"],
        "code": '@app.get("/user")',
        "expected_score": 0.85
    },
    {
        "id": "singular_nested_collection",
        "description": "Singular noun for nested collection",
        "violations": ["singular_resource"],
        "code": '@app.get("/users/{id}/order")',
        "expected_score": 0.85
    },
    {
        "id": "singular_versioned",
        "description": "Singular noun in versioned path",
        "violations": ["singular_resource"],
        "code": '@app.get("/v1/product")',
        "expected_score": 0.85
    },
    {
        "id": "singular_hyphenated",
        "description": "Singular compound noun with hyphen",
        "violations": ["singular_resource"],
        "code": '@app.get("/order-item")',
        "expected_score": 0.85
    },
    {
        "id": "param_after_singular",
        "description": "Singular collection with param — plural expected before param",
        "violations": ["singular_resource"],
        "code": '@app.get("/product/{id}")',
        "expected_score": 0.85
    },
    {
        "id": "plural_but_wrong_form",
        "description": "Irregular plural used correctly — 'people' is plural of 'person'",
        "violations": [],
        "code": '@app.get("/people")',
        "expected_score": 1.0
    },
    {
        "id": "singleton_sub_resource_correct",
        "description": "Singleton sub-resource — singular is semantically correct here",
        "violations": [],
        "code": '@app.get("/users/{id}/avatar")',
        "expected_score": 1.0
    },

    # =========================================================================
    # BLOCK 5 — Nesting Depth Violations (-0.10 per level over 4)
    # =========================================================================

    {
        "id": "depth_five_levels",
        "description": "Five levels of nesting — one level over limit",
        "violations": ["nesting_depth: +1"],
        "code": '@app.get("/orgs/{id}/depts/{did}/teams/{tid}/members")',
        "expected_score": 0.90
    },
    {
        "id": "depth_six_levels",
        "description": "Six levels of nesting — two levels over limit",
        "violations": ["nesting_depth: +2"],
        "code": '@app.get("/orgs/{id}/depts/{did}/teams/{tid}/members/{mid}")',
        "expected_score": 0.80
    },
    {
        "id": "depth_seven_levels",
        "description": "Seven levels of nesting — three levels over limit",
        "violations": ["nesting_depth: +3"],
        "code": '@app.get("/orgs/{id}/depts/{did}/teams/{tid}/members/{mid}/tasks")',
        "expected_score": 0.70
    },
    {
        "id": "depth_eight_levels",
        "description": "Eight levels of nesting — four levels over limit",
        "violations": ["nesting_depth: +4"],
        "code": '@app.get("/a/{id}/b/{bid}/c/{cid}/d/{did}/e/{eid}")',
        "expected_score": 0.60
    },
    {
        "id": "depth_exactly_four",
        "description": "Exactly four levels — no penalty",
        "violations": [],
        "code": '@app.get("/users/{id}/orders/{order_id}")',
        "expected_score": 1.0
    },

    # =========================================================================
    # BLOCK 6 — Trailing Slash (-0.10)
    # =========================================================================

    {
        "id": "trailing_slash_simple",
        "description": "Trailing slash on simple resource",
        "violations": ["trailing_slash"],
        "code": '@app.get("/users/")',
        "expected_score": 0.90
    },
    {
        "id": "trailing_slash_nested",
        "description": "Trailing slash on nested resource",
        "violations": ["trailing_slash"],
        "code": '@app.get("/users/{id}/orders/")',
        "expected_score": 0.90
    },
    {
        "id": "trailing_slash_versioned",
        "description": "Trailing slash after versioned resource",
        "violations": ["trailing_slash"],
        "code": '@app.get("/v1/products/")',
        "expected_score": 0.90
    },
    {
        "id": "trailing_slash_with_other_violation",
        "description": "Trailing slash combined with verb",
        "violations": ["trailing_slash", "verb_in_path: get"],
        "code": '@app.get("/get-users/")',
        "expected_score": 0.65
    },

    # =========================================================================
    # BLOCK 7 — File Extension in Path (-0.20)
    # =========================================================================

    {
        "id": "json_extension",
        "description": "File extension .json in path",
        "violations": ["file_extension: .json"],
        "code": '@app.get("/users.json")',
        "expected_score": 0.80
    },
    {
        "id": "xml_extension",
        "description": "File extension .xml in path",
        "violations": ["file_extension: .xml"],
        "code": '@app.get("/data.xml")',
        "expected_score": 0.80
    },
    {
        "id": "csv_extension",
        "description": "File extension .csv in path",
        "violations": ["file_extension: .csv"],
        "code": '@app.get("/reports.csv")',
        "expected_score": 0.80
    },
    {
        "id": "html_extension",
        "description": "File extension .html in path",
        "violations": ["file_extension: .html"],
        "code": '@app.get("/pages/index.html")',
        "expected_score": 0.80
    },
    {
        "id": "pdf_extension",
        "description": "File extension .pdf in path",
        "violations": ["file_extension: .pdf"],
        "code": '@app.get("/invoices/{id}.pdf")',
        "expected_score": 0.80
    },

    # =========================================================================
    # BLOCK 8 — Special Characters in Path (-0.20)
    # =========================================================================

    {
        "id": "exclamation_in_path",
        "description": "Exclamation mark in path segment",
        "violations": ["special_chars: !"],
        "code": '@app.get("/users!list")',
        "expected_score": 0.80
    },
    {
        "id": "at_sign_in_path",
        "description": "@ sign in path segment",
        "violations": ["special_chars: @"],
        "code": '@app.get("/users/@me")',
        "expected_score": 0.80
    },
    {
        "id": "plus_in_path",
        "description": "Plus sign as separator in path",
        "violations": ["special_chars: +"],
        "code": '@app.get("/order+items")',
        "expected_score": 0.80
    },
    {
        "id": "dot_as_separator",
        "description": "Dot used as path segment separator (not extension)",
        "violations": ["special_chars: ."],
        "code": '@app.get("/order.items")',
        "expected_score": 0.80
    },
    {
        "id": "dollar_in_path",
        "description": "Dollar sign in path segment",
        "violations": ["special_chars: $"],
        "code": '@app.get("/users/$admin")',
        "expected_score": 0.80
    },
    {
        "id": "hash_in_path",
        "description": "Hash in path segment",
        "violations": ["special_chars: #"],
        "code": '@app.get("/items/#featured")',
        "expected_score": 0.80
    },

    # =========================================================================
    # BLOCK 9 — Consecutive Slashes (-0.20)
    # =========================================================================

    {
        "id": "double_slash_start",
        "description": "Double slash at the start",
        "violations": ["consecutive_slashes"],
        "code": '@app.get("//users")',
        "expected_score": 0.80
    },
    {
        "id": "double_slash_middle",
        "description": "Double slash in the middle of path",
        "violations": ["consecutive_slashes"],
        "code": '@app.get("/users//orders")',
        "expected_score": 0.80
    },
    {
        "id": "triple_slash",
        "description": "Triple slash in path",
        "violations": ["consecutive_slashes"],
        "code": '@app.get("/users///orders")',
        "expected_score": 0.80
    },

    # =========================================================================
    # BLOCK 10 — CRUD Verb Disguised as Noun (-0.20)
    # The action is hidden in a noun form but clearly names a CRUD operation.
    # =========================================================================

    {
        "id": "crud_noun_deletion",
        "description": "'deletion' as resource noun — CRUD verb disguised",
        "violations": ["crud_noun: deletion"],
        "code": '@app.delete("/user-deletion")',
        "expected_score": 0.80
    },
    {
        "id": "crud_noun_creation",
        "description": "'creation' as resource noun",
        "violations": ["crud_noun: creation"],
        "code": '@app.post("/user-creation")',
        "expected_score": 0.80
    },
    {
        "id": "crud_noun_update",
        "description": "'updation' as resource noun",
        "violations": ["crud_noun: updation"],
        "code": '@app.put("/profile-updation")',
        "expected_score": 0.80
    },
    {
        "id": "crud_noun_removal",
        "description": "'removal' as resource noun",
        "violations": ["crud_noun: removal"],
        "code": '@app.delete("/item-removal/{id}")',
        "expected_score": 0.80
    },
    {
        "id": "crud_noun_getter",
        "description": "'getter' suffix — CRUD operation as noun",
        "violations": ["crud_noun: getter"],
        "code": '@app.get("/user-getter")',
        "expected_score": 0.80
    },
    {
        "id": "crud_noun_fetcher",
        "description": "'fetcher' suffix — CRUD operation as noun",
        "violations": ["crud_noun: fetcher"],
        "code": '@app.get("/data-fetcher")',
        "expected_score": 0.80
    },

    # =========================================================================
    # BLOCK 11 — Versioning Violations
    # bad format: -0.15 | version not at root: -0.10 | non-integer: -0.10
    # =========================================================================

    {
        "id": "version_word_format",
        "description": "Full word 'version' instead of 'v{n}'",
        "violations": ["bad_version_format"],
        "code": '@app.get("/version1/users")',
        "expected_score": 0.85
    },
    {
        "id": "version_at_end",
        "description": "Version segment at the end of path — not at root",
        "violations": ["version_not_at_root"],
        "code": '@app.get("/users/v1")',
        "expected_score": 0.90
    },
    {
        "id": "version_in_middle",
        "description": "Version segment in the middle of path",
        "violations": ["version_not_at_root"],
        "code": '@app.get("/users/v2/orders")',
        "expected_score": 0.90
    },
    {
        "id": "version_decimal",
        "description": "Decimal version number — non-integer",
        "violations": ["non_integer_version"],
        "code": '@app.get("/v1.2/users")',
        "expected_score": 0.90
    },
    {
        "id": "version_alpha",
        "description": "Alphabetic version label — non-integer",
        "violations": ["non_integer_version"],
        "code": '@app.get("/vBeta/users")',
        "expected_score": 0.90
    },
    {
        "id": "version_word_and_not_root",
        "description": "Full word version AND not at root — compound penalty",
        "violations": ["bad_version_format", "version_not_at_root"],
        "code": '@app.get("/users/version2/orders")',
        "expected_score": 0.75
    },
    {
        "id": "no_version_fine",
        "description": "No versioning — perfectly acceptable",
        "violations": [],
        "code": '@app.get("/products")',
        "expected_score": 1.0
    },

    # =========================================================================
    # BLOCK 12 — Path Parameter Naming Violations
    # camelCase param: -0.10 | redundant resource in param: -0.05 | non-descriptive: -0.10
    # =========================================================================

    {
        "id": "param_camel_case",
        "description": "Path param in camelCase — should be snake_case",
        "violations": ["param_camelCase: userId"],
        "code": '@app.get("/users/{userId}")',
        "expected_score": 0.90
    },
    {
        "id": "param_camel_case_nested",
        "description": "Nested path with camelCase param",
        "violations": ["param_camelCase: orderId"],
        "code": '@app.get("/users/{id}/orders/{orderId}")',
        "expected_score": 0.90
    },
    {
        "id": "param_uppercase",
        "description": "Uppercase path param name",
        "violations": ["param_uppercase: ID"],
        "code": '@app.get("/users/{ID}")',
        "expected_score": 0.90
    },
    {
        "id": "param_redundant_resource",
        "description": "Redundant resource name in param — /users/{user_id} is redundant",
        "violations": ["param_redundant: user_id"],
        "code": '@app.get("/users/{user_id}")',
        "expected_score": 0.95
    },
    {
        "id": "param_non_descriptive_x",
        "description": "Non-descriptive single-letter param 'x'",
        "violations": ["param_non_descriptive: x"],
        "code": '@app.get("/users/{x}")',
        "expected_score": 0.90
    },
    {
        "id": "param_non_descriptive_n",
        "description": "Non-descriptive single-letter param 'n'",
        "violations": ["param_non_descriptive: n"],
        "code": '@app.get("/items/{n}")',
        "expected_score": 0.90
    },
    {
        "id": "param_numbered_non_descriptive",
        "description": "Numbered non-descriptive param 'id2'",
        "violations": ["param_non_descriptive: id2"],
        "code": '@app.get("/items/{id2}")',
        "expected_score": 0.90
    },
    {
        "id": "param_two_camel_params",
        "description": "Two camelCase params — double penalty",
        "violations": ["param_camelCase: userId", "param_camelCase: orderId"],
        "code": '@app.get("/users/{userId}/orders/{orderId}")',
        "expected_score": 0.80
    },
    {
        "id": "param_correct_snake",
        "description": "Correct snake_case param in nested path",
        "violations": [],
        "code": '@app.get("/users/{id}/orders/{order_id}")',
        "expected_score": 1.0
    },

    # =========================================================================
    # BLOCK 13 — Query Param Embedded in Path Pattern (-0.25)
    # =========================================================================

    {
        "id": "query_param_in_path_pattern",
        "description": "Query string embedded as part of the path definition",
        "violations": ["query_in_path"],
        "code": '@app.get("/users?id=1")',
        "expected_score": 0.75
    },
    {
        "id": "query_param_multiple_in_path",
        "description": "Multiple query params embedded in path definition",
        "violations": ["query_in_path"],
        "code": '@app.get("/products?category=shoes&size=10")',
        "expected_score": 0.75
    },
    {
        "id": "query_filter_in_path",
        "description": "Filter logic embedded as query string in path",
        "violations": ["query_in_path"],
        "code": '@app.get("/orders?status=pending")',
        "expected_score": 0.75
    },

    # =========================================================================
    # BLOCK 14 — Action Endpoint Without /actions/ Prefix (-0.15)
    # Actions that mutate state should live under /actions/ or be POST verbs.
    # =========================================================================

    {
        "id": "action_without_namespace_activate",
        "description": "Action 'activate' directly on resource — missing /actions/",
        "violations": ["action_without_namespace"],
        "code": '@app.post("/users/{id}/activate")',
        "expected_score": 0.85
    },
    {
        "id": "action_without_namespace_deactivate",
        "description": "Action 'deactivate' directly on resource — missing /actions/",
        "violations": ["action_without_namespace"],
        "code": '@app.post("/users/{id}/deactivate")',
        "expected_score": 0.85
    },
    {
        "id": "action_without_namespace_publish",
        "description": "Action 'publish' directly on resource — missing /actions/",
        "violations": ["action_without_namespace"],
        "code": '@app.post("/posts/{id}/publish")',
        "expected_score": 0.85
    },
    {
        "id": "action_without_namespace_approve",
        "description": "Action 'approve' directly on resource — missing /actions/",
        "violations": ["action_without_namespace"],
        "code": '@app.post("/orders/{id}/approve")',
        "expected_score": 0.85
    },
    {
        "id": "action_without_namespace_resend",
        "description": "Action 'resend' directly on resource",
        "violations": ["action_without_namespace"],
        "code": '@app.post("/emails/{id}/resend")',
        "expected_score": 0.85
    },
    {
        "id": "action_correct_with_namespace",
        "description": "Action correctly placed under /actions/ — no penalty",
        "violations": [],
        "code": '@app.post("/posts/{id}/actions/publish")',
        "expected_score": 1.0
    },
    {
        "id": "action_correct_global_namespace",
        "description": "Global action correctly under /actions/ namespace",
        "violations": [],
        "code": '@app.post("/actions/sync-inventory")',
        "expected_score": 1.0
    },

    # =========================================================================
    # BLOCK 15 — Compound / Multiple Violations
    # Real-world bad endpoints often combine multiple issues.
    # =========================================================================

    {
        "id": "compound_verb_singular_snake",
        "description": "Verb + singular + snake_case — three violations",
        "violations": ["verb_in_path: get", "singular_resource", "snake_case"],
        "code": '@app.get("/get_user")',
        "expected_score": 0.50
    },
    {
        "id": "compound_camel_singular",
        "description": "camelCase + singular resource",
        "violations": ["camelCase", "singular_resource"],
        "code": '@app.get("/userProfile")',
        "expected_score": 0.65
    },
    {
        "id": "compound_verb_camel_trailing",
        "description": "Verb + camelCase + trailing slash",
        "violations": ["verb_in_path: create", "camelCase", "trailing_slash"],
        "code": '@app.post("/createUserProfile/")',
        "expected_score": 0.45
    },
    {
        "id": "compound_deep_nest_verb",
        "description": "Deep nesting + verb in path",
        "violations": ["nesting_depth: +2", "verb_in_path: get"],
        "code": '@app.get("/orgs/{id}/depts/{did}/teams/{tid}/members/{mid}/get-tasks")',
        "expected_score": 0.45
    },
    {
        "id": "compound_special_char_camel",
        "description": "Special character + camelCase",
        "violations": ["special_chars: !", "camelCase"],
        "code": '@app.get("/userList!active")',
        "expected_score": 0.60
    },
    {
        "id": "compound_extension_verb",
        "description": "File extension + verb in path",
        "violations": ["file_extension: .json", "verb_in_path: get"],
        "code": '@app.get("/get-users.json")',
        "expected_score": 0.55
    },
    {
        "id": "compound_version_not_root_camel",
        "description": "Version not at root + camelCase",
        "violations": ["version_not_at_root", "camelCase"],
        "code": '@app.get("/userProfiles/v1")',
        "expected_score": 0.70
    },
    {
        "id": "compound_param_camel_and_verb",
        "description": "camelCase param + verb in path",
        "violations": ["param_camelCase: userId", "verb_in_path: get"],
        "code": '@app.get("/get-users/{userId}")',
        "expected_score": 0.65
    },
    {
        "id": "compound_all_casing_violations",
        "description": "Uppercase + snake_case combined — both penalties apply",
        "violations": ["uppercase", "snake_case"],
        "code": '@app.get("/USER_PROFILES")',
        "expected_score": 0.70
    },
    {
        "id": "compound_three_verbs",
        "description": "Three verb segments — extreme case",
        "violations": ["verb_in_path: get", "verb_in_path: and", "verb_in_path: list"],
        "code": '@app.get("/get-and-list-and-fetch-users")',
        "expected_score": 0.25
    },
    {
        "id": "compound_query_in_path_and_verb",
        "description": "Query param in path + verb in path",
        "violations": ["query_in_path", "verb_in_path: get"],
        "code": '@app.get("/get-users?role=admin")',
        "expected_score": 0.50
    },
    {
        "id": "worst_case_endpoint",
        "description": "Multiple critical violations — real world legacy horror",
        "violations": [
            "verb_in_path: fetchAll",
            "camelCase",
            "trailing_slash",
            "file_extension: .json",
            "crud_noun",
        ],
        "code": '@app.get("/fetchAllUserDeletion/.json/")',
        "expected_score": 0.0
    },

    # =========================================================================
    # BLOCK 16 — Framework Variety
    # Same naming rules apply regardless of framework syntax.
    # =========================================================================

    {
        "id": "django_perfect",
        "description": "Django path() with perfect naming",
        "violations": [],
        "code": 'path("users/<int:id>/orders/", view)',
        "expected_score": 1.0
    },
    {
        "id": "django_verb_in_path",
        "description": "Django path() with verb in URL",
        "violations": ["verb_in_path: get"],
        "code": 'path("get-users/", view)',
        "expected_score": 0.75
    },
    {
        "id": "django_snake_case",
        "description": "Django path() with snake_case URL",
        "violations": ["snake_case"],
        "code": 'path("user_profiles/", view)',
        "expected_score": 0.90
    },
    {
        "id": "express_perfect",
        "description": "Express router with perfect naming",
        "violations": [],
        "code": 'router.get("/products/:id/reviews", handler)',
        "expected_score": 1.0
    },
    {
        "id": "express_camel_case",
        "description": "Express router with camelCase path",
        "violations": ["camelCase"],
        "code": 'router.get("/userProfiles/:id", handler)',
        "expected_score": 0.80
    },
    {
        "id": "express_verb_in_path",
        "description": "Express router with verb in path",
        "violations": ["verb_in_path: create"],
        "code": 'router.post("/create-order", handler)',
        "expected_score": 0.75
    },
    {
        "id": "gin_perfect",
        "description": "Gin router with perfect naming",
        "violations": [],
        "code": 'r.GET("/orders/:id/items", handler)',
        "expected_score": 1.0
    },
    {
        "id": "gin_uppercase_resource",
        "description": "Gin router with uppercase resource",
        "violations": ["uppercase"],
        "code": 'r.GET("/Orders/:id", handler)',
        "expected_score": 0.80
    },
    {
        "id": "spring_perfect",
        "description": "Spring @GetMapping with perfect naming",
        "violations": [],
        "code": '@GetMapping("/users/{id}/orders")',
        "expected_score": 1.0
    },
    {
        "id": "spring_camel_case",
        "description": "Spring @GetMapping with camelCase path",
        "violations": ["camelCase"],
        "code": '@GetMapping("/userOrders/{userId}")',
        "expected_score": 0.80
    },
    {
        "id": "spring_verb_in_path",
        "description": "Spring @PostMapping with verb in path",
        "violations": ["verb_in_path: update"],
        "code": '@PostMapping("/update-profile")',
        "expected_score": 0.75
    },
    {
        "id": "flask_perfect",
        "description": "Flask route() with perfect naming",
        "violations": [],
        "code": "@app.route('/v1/user-profiles/<int:id>', methods=['GET'])",
        "expected_score": 1.0
    },
    {
        "id": "flask_trailing_slash",
        "description": "Flask route() with trailing slash",
        "violations": ["trailing_slash"],
        "code": "@app.route('/users/', methods=['GET'])",
        "expected_score": 0.90
    },

    # =========================================================================
    # BLOCK 17 — False Positive / Edge Cases
    # Words that look like verbs or violations but are actually correct.
    # =========================================================================

    {
        "id": "fp_search_as_sub_resource",
        "description": "'search' looks like a verb but accepted as sub-resource",
        "violations": [],
        "code": '@app.get("/products/search")',
        "expected_score": 1.0
    },
    {
        "id": "fp_filter_as_sub_resource",
        "description": "'filter' could be a verb but acceptable as sub-resource endpoint",
        "violations": [],
        "code": '@app.get("/reports/filter")',
        "expected_score": 1.0
    },
    {
        "id": "fp_health_technical_keyword",
        "description": "'health' is a technical keyword — not a verb, no penalty",
        "violations": [],
        "code": '@app.get("/health")',
        "expected_score": 1.0
    },
    {
        "id": "fp_status_technical_keyword",
        "description": "'status' is a technical keyword — acceptable as endpoint",
        "violations": [],
        "code": '@app.get("/status")',
        "expected_score": 1.0
    },
    {
        "id": "fp_me_alias",
        "description": "'/users/me' — 'me' is an accepted alias for current user",
        "violations": [],
        "code": '@app.get("/users/me")',
        "expected_score": 1.0
    },
    {
        "id": "fp_plural_looks_singular",
        "description": "'news' is already plural — no penalty",
        "violations": [],
        "code": '@app.get("/news")',
        "expected_score": 1.0
    },
    {
        "id": "fp_series_already_plural",
        "description": "'series' is already plural — no penalty",
        "violations": [],
        "code": '@app.get("/series/{id}")',
        "expected_score": 1.0
    },
    {
        "id": "fp_v1_not_a_verb",
        "description": "'v1' should not be treated as a verb or violation",
        "violations": [],
        "code": '@app.get("/v1/orders")',
        "expected_score": 1.0
    },
    {
        "id": "fp_id_param_not_redundant",
        "description": "'{id}' after resource is not redundant — correct minimal form",
        "violations": [],
        "code": '@app.get("/orders/{id}")',
        "expected_score": 1.0
    },
    {
        "id": "fp_kebab_not_special_char",
        "description": "Hyphen is the correct separator — should not trigger special_chars",
        "violations": [],
        "code": '@app.get("/user-profiles/{id}/order-items")',
        "expected_score": 1.0
    },
]