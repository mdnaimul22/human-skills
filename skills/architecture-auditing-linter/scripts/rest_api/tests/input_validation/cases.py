# =============================================================================
# Input Validation — Test Dataset (Comprehensive ~20 Cases)
# Sources: OWASP API Security Top 10 (API3, API8), Google API Validation Rules
# =============================================================================

TEST_CASES = [
    # --- BLOCK 1: Schema Validation (Pydantic, Marshmallow, DRF) ---
    {
        "id": "pydantic_strict_schema",
        "description": "FastAPI/Pydantic strict schema validation (Google API style)",
        "expected_score": 0.3000,
        "code": """
from pydantic import BaseModel, Field, EmailStr
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    age: int = Field(gt=18)

@app.post("/users")
def create_user(user: UserCreate):
    return user.dict()
"""
    },
    {
        "id": "marshmallow_validation",
        "description": "Flask/Marshmallow schema validation",
        "expected_score": 0.3000,
        "code": """
from marshmallow import Schema, fields, validate

class ItemSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1))
    price = fields.Float(validate=validate.Range(min=0))

@app.route('/items', methods=['POST'])
def add_item():
    schema = ItemSchema()
    result = schema.load(request.json)
    return jsonify(result)
"""
    },
    {
        "id": "drf_serializer_validation",
        "description": "Django REST Framework ModelSerializer validation",
        "expected_score": 0.3000,
        "code": """
from rest_framework import serializers

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['title', 'content']
        
    def validate_title(self, value):
        if len(value) < 5: raise serializers.ValidationError("Too short")
        return value
"""
    },
    {
        "id": "wtforms_validation",
        "description": "WTForms validation (legacy but standard)",
        "expected_score": 0.3000,
        "code": """
from wtforms import Form, StringField, validators

class RegistrationForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])

@app.route('/register', methods=['POST'])
def register():
    form = RegistrationForm(request.form)
    if form.validate():
        pass
"""
    },

    # --- BLOCK 2: XSS and Injection Prevention (OWASP API8) ---
    {
        "id": "xss_bleach_sanitization",
        "description": "XSS sanitization using bleach",
        "expected_score": 0.1500,
        "code": """
import bleach

@app.post("/comments")
def post_comment():
    raw_html = request.json.get("content")
    clean_html = bleach.clean(raw_html)
    return clean_html
"""
    },
    {
        "id": "html_escape_xss",
        "description": "XSS prevention using html.escape",
        "expected_score": 0.1500,
        "code": """
import html

@app.post("/bio")
def update_bio():
    bio = html.escape(request.json.get("bio"))
    return bio
"""
    },
    {
        "id": "orm_sql_injection_safe",
        "description": "Safe DB queries using ORM (implicit SQLi protection)",
        "expected_score": 0.1500,
        "code": """
@app.get("/users/<id>")
def get_user(id):
    # ORM automatically parameterizes queries
    user = session.query(User).filter(User.id == id).first()
    return user
"""
    },
    {
        "id": "parameterised_raw_sql_safe",
        "description": "Safe raw SQL using parameterised queries",
        "expected_score": 0.1500,
        "code": """
@app.get("/users")
def get_user():
    user_id = request.args.get("id")
    # Parameterised -> safe
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    return cursor.fetchone()
"""
    },
    {
        "id": "critical_raw_sql_injection_penalty",
        "description": "CRITICAL: String formatted raw SQL vulnerability (OWASP Injection)",
        "expected_score": 0.0000,
        "code": """
@app.post("/login")
def login():
    username = request.json.get("user")
    # VULNERABLE: String interpolation in SQL
    conn.execute(f"SELECT * FROM users WHERE username='{username}'")
    return "OK"
"""
    },

    # --- BLOCK 3: File Upload Security ---
    {
        "id": "file_upload_validated_secure",
        "description": "Secure file upload with extension and filename validation",
        "expected_score": 0.1500,
        "code": """
from werkzeug.utils import secure_filename

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg'}

@app.post("/upload")
def upload_file():
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(filename)
"""
    },
    {
        "id": "file_upload_mimetype_check",
        "description": "File upload checking mimetype",
        "expected_score": 0.1500,
        "code": """
@app.post("/upload")
def upload_avatar():
    file = request.files['avatar']
    if file.mimetype not in ['image/jpeg', 'image/png']:
        return "Invalid", 400
    file.save('/tmp/avatar')
"""
    },
    {
        "id": "file_upload_unvalidated_penalty",
        "description": "CRITICAL: Unvalidated file upload (RCE risk)",
        "expected_score": 0.1500,
        "code": """
@app.post("/upload")
def upload():
    # VULNERABLE: Saving exactly as uploaded without checks
    file = request.files['document']
    file.save(f"/uploads/{file.filename}")
"""
    },

    # --- BLOCK 4: Request Size Limits (DOS Prevention) ---
    {
        "id": "max_content_length_set",
        "description": "DOS prevention: Flask MAX_CONTENT_LENGTH",
        "expected_score": 0.1000,
        "code": """
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB

@app.post("/data")
def receive_data():
    return "OK"
"""
    },
    {
        "id": "fastapi_request_size_limit",
        "description": "DOS prevention: Checking content-length header manually",
        "expected_score": 0.0000,
        "code": """
@app.post("/data")
def receive_data():
    length = request.headers.get("Content-Length")
    if int(length) > 1000000:
        return 413
    return "OK"
"""
    },

    # --- BLOCK 5: Manual Validation Checks ---
    {
        "id": "manual_validation_heavy",
        "description": "Manual input validation with multiple checks (if >= 3 checks)",
        "expected_score": 0.0800,
        "code": """
@app.post("/submit")
def submit():
    data = request.json
    if not isinstance(data.get('age'), int): return 400
    if len(data.get('name', '')) < 3: return 400
    if data.get('status') not in ['active', 'inactive']: return 400
    if not data.get('email'): return 400
    return "OK"
"""
    },
    {
        "id": "manual_validation_light",
        "description": "Manual input validation with few checks (1-2 checks)",
        "expected_score": 0.0000,
        "code": """
@app.post("/update")
def update():
    data = request.json
    if len(data.get('title')) > 100:
        return 400
    return "OK"
"""
    },

    # --- BLOCK 6: Complete Secure Example vs Complete Insecure Example ---
    {
        "id": "perfect_validation_overall",
        "description": "Combines schema, ORM, XSS, and size limits (Max score)",
        "expected_score": 0.7000,
        "code": """
from pydantic import BaseModel
import bleach

app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024

class Comment(BaseModel):
    text: str

@app.post("/comments")
def add_comment(comment: Comment):
    clean_text = bleach.clean(comment.text)
    db.session.add(DBComment(text=clean_text))
    db.session.commit()
    return "Created", 201
"""
    },
    {
        "id": "zero_validation_pure_json",
        "description": "Trusting client input completely (0 score)",
        "expected_score": 0.3000,
        "code": """
@app.post("/stuff")
def add_stuff():
    # Trusting JSON completely, no schema, no checks
    data = request.json
    db.insert(data)
    return "OK"
"""
    }
]
