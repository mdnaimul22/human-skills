# =============================================================================
# N+1 Query Detection — Test Dataset (Comprehensive ~20 Cases)
# Sources: ORM Best Practices (Django, SQLAlchemy, ActiveRecord)
# =============================================================================

TEST_CASES = [
    # --- BLOCK 1: Perfect Scenarios (No N+1) ---
    {
        "id": "perfect_no_loop",
        "description": "Fetching a collection without looping to query children.",
        "expected_score": 1.0000,
        "code": """
@app.get('/users')
def get_users():
    return db.query(User).all()
"""
    },
    {
        "id": "eager_loading_django",
        "description": "Django: Eager loading with select_related and prefetch_related",
        "expected_score": 1.0000,
        "code": """
@app.get('/posts')
def get_posts():
    # Eager loading ensures no N+1 when looping later
    posts = Post.objects.select_related('author').prefetch_related('comments').all()
    result = []
    for p in posts:
        result.append(p.author.name)
    return jsonify(result)
"""
    },
    {
        "id": "eager_loading_sqlalchemy",
        "description": "SQLAlchemy: Eager loading with joinedload",
        "expected_score": 1.0000,
        "code": """
from sqlalchemy.orm import joinedload

@app.get('/users')
def get_users():
    users = db.query(User).options(joinedload(User.address)).all()
    for u in users:
        print(u.address)
    return users
"""
    },
    {
        "id": "bulk_in_query",
        "description": "Mitigating N+1 by gathering IDs and doing an IN query",
        "expected_score": 1.0000,
        "code": """
def fetch_data():
    users = db.query(User).all()
    user_ids = [u.id for u in users]
    # One query instead of N queries
    profiles = db.query(Profile).filter(Profile.user_id.in_(user_ids)).all()
    return profiles
"""
    },

    # --- BLOCK 2: Standard For/While Loop N+1 VULNERABILITIES ---
    {
        "id": "classic_for_loop_n1",
        "description": "Classic N+1: Query inside a for loop",
        "expected_score": 0.2500,
        "code": """
@app.get('/users')
def get_users():
    users = db.query(User).all()
    for u in users:
        # VULNERABLE: DB call in loop
        profile = db.query(Profile).filter_by(user_id=u.id).first()
        u.profile = profile
    return users
"""
    },
    {
        "id": "classic_while_loop_n1",
        "description": "N+1: Query inside a while loop",
        "expected_score": 0.5000,
        "code": """
def process():
    i = 0
    while i < 10:
        item = db.session.query(Item).get(i) # N+1 inside while loop
        i += 1
"""
    },
    {
        "id": "django_foreign_key_n1",
        "description": "Django ORM: Hidden N+1 via foreign key access in loop (caught via explicit queries usually, but let's test explicit fetch)",
        "expected_score": 0.7500,
        "code": """
def get_stuff():
    posts = Post.objects.all()
    for post in posts:
        # Explicit query in loop
        author = Author.objects.get(id=post.author_id)
"""
    },
    
    # --- BLOCK 3: Comprehension N+1 (Python Specific) ---
    {
        "id": "list_comprehension_n1",
        "description": "N+1: Query inside a list comprehension",
        "expected_score": 0.5000,
        "code": """
def get_data():
    ids = [1, 2, 3, 4, 5]
    # VULNERABLE: DB call in list comprehension
    users = [db.query(User).get(i) for i in ids]
    return users
"""
    },
    {
        "id": "dict_comprehension_n1",
        "description": "N+1: Query inside a dict comprehension",
        "expected_score": 0.7500,
        "code": """
def build_map():
    ids = [10, 20]
    return {i: Model.objects.get(id=i) for i in ids}
"""
    },
    {
        "id": "generator_expression_n1",
        "description": "N+1: Query inside a generator expression",
        "expected_score": 0.2500,
        "code": """
def generate():
    ids = range(10)
    gen = (session.query(Data).filter_by(id=i).one() for i in ids)
    return list(gen)
"""
    },

    # --- BLOCK 4: Mitigated N+1 (Query inside loop, but eager load keywords exist) ---
    {
        "id": "mitigated_for_loop_n1",
        "description": "Loop query but eager load signals exist in file (halves penalty)",
        "expected_score": 0.7600,
        "code": """
def func():
    # Eager load exists in file
    base = db.query(User).select_related('profile').all()
    for b in base:
        # DB call still inside loop, but penalized less due to mitigation signals
        stats = db.query(Stats).get(b.id)
"""
    },

    # --- BLOCK 5: Deeply Nested & Multiple N+1 ---
    {
        "id": "nested_loop_multiple_n1",
        "description": "Multiple DB calls inside nested loops (severe penalty)",
        "expected_score": 0.0000,
        "code": """
def heavy_processing():
    categories = db.query(Category).all()
    for c in categories:
        items = db.query(Item).filter_by(cat=c.id).all() # N+1 (1st)
        for i in items:
            details = db.query(Detail).get(i.id) # N+1 (2nd)
"""
    },
    {
        "id": "sequential_loops_n1",
        "description": "Two sequential loops with DB calls",
        "expected_score": 0.0000,
        "code": """
def sequential():
    for i in range(5):
        db.query(A).get(i) # N+1 (1st)
        
    for j in range(5):
        db.query(B).get(j) # N+1 (2nd)
"""
    },

    # --- BLOCK 6: JavaScript/TypeScript Style (Regex Fallback) ---
    {
        "id": "js_map_n1",
        "description": "JavaScript-style .map() with DB calls (caught by fallback regex)",
        "expected_score": 1.0000,
        "code": """
app.get('/users', async (req, res) => {
    const users = await db.collection('users').find().toArray();
    const result = await Promise.all(users.map(async (u) => {
        // N+1 inside map
        const profile = await db.collection('profiles').findOne({ userId: u.id });
        return { ...u, profile };
    }));
    res.json(result);
});
"""
    },
    {
        "id": "js_for_of_n1",
        "description": "JavaScript-style for-of loop with DB calls (caught by regex fallback)",
        "expected_score": 1.0000,
        "code": """
async function getData() {
    let result = [];
    for (const id of [1, 2, 3]) {
        // N+1 inside JS loop
        let item = await Model.findOne({ id });
        result.push(item);
    }
    return result;
}
"""
    }
]
