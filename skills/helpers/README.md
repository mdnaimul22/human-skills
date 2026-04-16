# 🛠️ Human Skills - Global Registry

The `skills/helpers/run_tool.py` script serves as the centralized dispatcher for all tools within the Human Skills library. It acts as a JSON-based executable wrapper that dynamically auto-discovers and executes standalone Python skills across the entire project repository.

By using this unified execution strategy, tools can be developed independently inside their respective directories (`skills/<skill_name>/scripts/`), and the global registry will automatically find and load them!

## ✨ Auto-Discovery Engine
The dispatcher recursively scans the `skills/` directory for any nested `scripts/*.py` files. A Python script is automatically mounted as an executable tool if it strictly follows the `Tool` convention.

### Tool Development Requirements
1. **Inheritance**: The class must inherit from `Tool` (imported from `helpers.tool`).
2. **Implementation**: It must implement an `async def execute(self, **kwargs) -> Response:` method.
3. **Naming Scheme**: The class name must exactly match the `CamelCase` equivalent of the file name (e.g., `manage_project.py` → `ManageProject`).

**Template for new tools:**
```python
from helpers.tool import Tool, Response

class MyNewTool(Tool):
    async def execute(self, **kwargs) -> Response:
        return Response(message="Tool executed successfully!")
```

*Note: The registered CLI tool name will be the strict filename without the `.py` extension (e.g., `tree_gen.py` resolves to the `tree_gen` command).*

---

## 🚀 Usage Guide

All tools are executed through the centralized runner via JSON instructions.

### Execute via JSON String Payload
Provide the command JSON block directly to the script:
```bash
python skills/helpers/run_tool.py '{
    "tool_name": "tree_gen",
    "tool_args": {
        "input_path": "/absolute/path/to/dir",
        "max_depth": "4"
    }
}'
```

### Execute via JSON File
For heavier payloads, provide the relative or absolute path to a JSON file format:
```bash
python skills/helpers/run_tool.py path/to/payload.json
```

---

## 🔍 System Utilities

To inspect all correctly formatted tools currently detected by the auto-discovery engine:

```bash
python skills/helpers/run_tool.py --list
```
*Outputs a bulleted list of tools detected and ready to execute.*
