# Project Setup Skill

A comprehensive guide for creating and configuring Agent Zero projects.

## Overview

This skill provides complete guidance for setting up Agent Zero projects, including:
- Project creation (empty or Git-based)
- Custom instructions and configuration
- Memory management (isolated or shared)
- Knowledge base integration
- Agent configuration
- Secrets and variables management

## File Structure

```
project-setup/
├── SKILL.md                    # Main skill documentation
├── README.md                   # This file
├── templates/                  # Configuration templates
│   ├── project.json           # Project configuration template
│   └── instructions-example.md # Instructions template
├── scripts/                    # Helper scripts (optional)
└── docs/                       # Additional documentation (optional)
```

## Quick Start

1. **Load the skill**: The skill is automatically loaded when you mention project setup tasks
2. **Follow the guide**: SKILL.md contains step-by-step instructions
3. **Use templates**: Copy and customize templates from the `templates/` directory

## Key Features

### 1. Project Creation
- Create empty projects from scratch
- Clone Git repositories directly into projects
- Automatic configuration merging for existing `.a0proj/` folders

### 2. Instructions System
- Main instructions field in project configuration
- Additional instruction files in `.a0proj/instructions/`
- Automatic concatenation and injection into agent context

### 3. Memory Management
- **Own memory**: Isolated vector database per project
- **Global memory**: Shared memory pool across related projects

### 4. Knowledge Base
- Custom knowledge files in `.a0proj/knowledge/`
- Automatic documentation indexing from `/docs/`
- Support for PDF, text, CSV, HTML, JSON, and Markdown

### 5. Agent Configuration
- Project-specific subagent profiles
- Custom system prompts per profile
- Model and temperature settings

### 6. Security
- Project-scoped secrets in `.a0proj/secrets.env`
- Non-sensitive variables in `.a0proj/variables.env`
- Automatic Git exclusion for secrets

## Use Cases

### Multi-Client Agency Work
```
/usr/projects/client-acme/
/usr/projects/client-globex/
/usr/projects/client-initech/
```
Each with isolated memory, credentials, and instructions.

### Multi-Language Development
```
/usr/projects/python-ml-research/
/usr/projects/nodejs-webapp/
/usr/projects/go-microservices/
```
Each with language-specific patterns and tools.

### Domain-Specific Work
```
/usr/projects/finance-automation/
/usr/projects/marketing-analytics/
/usr/projects/hr-automation/
```
Each with domain terminology and regulations.

## Templates

### project.json
Complete project configuration template with all available options.

### instructions-example.md
Template for writing clear, effective project instructions.

## Best Practices

1. **Be Specific**: Write detailed instructions with clear paths and quality standards
2. **Use Isolated Memory**: Default to "own memory" for client work
3. **Never Commit Secrets**: Keep `.a0proj/secrets.env` out of version control
4. **Organize Knowledge**: Use `/docs/` for documentation, `.a0proj/knowledge/` for reference
5. **Update Regularly**: Keep instructions current as project scope evolves

## Example Workflow

1. Create project via Dashboard
2. Write comprehensive instructions
3. Set memory mode to "own" (for client work)
4. Add relevant knowledge files
5. Configure project-specific agents
6. Add API keys and credentials
7. Start working with full context!

## Troubleshooting

### Project Not Activating
- Check project exists in `/a0/usr/projects/`
- Verify `project.json` is valid JSON
- Try refreshing the interface

### Instructions Not Working
- Ensure instructions are in the correct field
- Check for markdown syntax errors
- Verify project is actually active

### Memory Issues
- Check memory mode setting
- Verify vector_db directory exists
- Try clearing and rebuilding memory

## Contributing

To improve this skill:

1. Edit SKILL.md to add or improve instructions
2. Add new templates to `templates/`
3. Create helper scripts in `scripts/`
4. Update this README with any changes

## License

MIT License - Feel free to use and modify for your needs.

## Support

For issues or questions about Agent Zero projects, refer to the main documentation or create an issue in the repository.