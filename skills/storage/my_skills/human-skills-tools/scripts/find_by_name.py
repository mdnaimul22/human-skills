import os
import subprocess
from typing import List, Dict, Any, Optional

from .helpers.tool import Tool, Response
from .helpers.print_style import PrintStyle
from .helpers.errors import handle_error


class FindByName(Tool):
    """Tool for finding files by name or pattern."""

    async def execute(self, **kwargs) -> Response:
        search_directory = kwargs.get("search_directory")
        pattern = kwargs.get("pattern", "*")
        file_type = kwargs.get("type", "any").lower()
        max_depth = kwargs.get("max_depth", None)
        extensions = kwargs.get("extensions", [])
        excludes = kwargs.get("excludes", [])
        full_path = kwargs.get("full_path", False)
        
        # Validate inputs
        if not search_directory:
            return Response(message="Error: search_directory parameter is required", break_loop=False)
        
        if not os.path.isdir(search_directory):
            return Response(message=f"Error: Directory '{search_directory}' does not exist", break_loop=False)
        
        # Build the find command
        try:
            cmd = ["find", search_directory]
            
            # Add depth limit if specified
            if max_depth is not None:
                cmd.extend(["-maxdepth", str(max_depth)])
            
            # Add type filter
            if file_type == "file":
                cmd.extend(["-type", "f"])
            elif file_type == "directory":
                cmd.extend(["-type", "d"])
            
            # Add name pattern
            if pattern != "*":
                if full_path:
                    cmd.extend(["-path", pattern])
                else:
                    cmd.extend(["-name", pattern])
            
            # Add extension filters
            if extensions:
                extension_conditions = []
                for ext in extensions:
                    if not ext.startswith("."):
                        ext = f".{ext}"
                    extension_conditions.append(f"-name \"*{ext}\"")
                
                if extension_conditions:
                    cmd.append("(")
                    cmd.append(extension_conditions[0])
                    for condition in extension_conditions[1:]:
                        cmd.extend(["-o", condition])
                    cmd.append(")")
            
            # Add exclude patterns
            for exclude in excludes:
                cmd.extend(["-not", "-path", f"*/{exclude}/*"])
            
            # Execute the command
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                if stderr:
                    raise Exception(f"Find error: {stderr}")
            
            # Parse and format results
            results = [line.strip() for line in stdout.splitlines() if line.strip()]
            
            # Get file information
            file_info = []
            for path in results:
                try:
                    stat = os.stat(path)
                    is_dir = os.path.isdir(path)
                    
                    info = {
                        "path": path,
                        "is_directory": is_dir,
                        "size": stat.st_size if not is_dir else None,
                        "modified": stat.st_mtime,
                    }
                    
                    file_info.append(info)
                except Exception as e:
                    # Skip files that can't be accessed
                    continue
            
            # Format the response
            response = self._format_find_results(file_info, search_directory, pattern)
            
            # Log the action
            self.log.update(content=f"Found {len(file_info)} items matching '{pattern}' in {search_directory}")
            
            return Response(message=response, break_loop=False)
            
        except Exception as e:
            handle_error(e)
            return Response(message=f"Error executing find: {str(e)}", break_loop=False)
    
    def _format_find_results(self, file_info, search_directory, pattern):
        """Format find results for display."""
        if not file_info:
            return f"No files found matching '{pattern}' in {search_directory}"
        
        response = f"Found {len(file_info)} results\n"
        
        # Sort by path
        file_info.sort(key=lambda x: x["path"])
        
        # Display results
        for info in file_info:
            path = info["path"]
            rel_path = os.path.relpath(path, search_directory)
            
            if info["is_directory"]:
                response += f"{rel_path} (directory)\n"
            else:
                size = info["size"]
                size_str = f"{size} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                response += f"{rel_path} ({size_str})\n"
        
        # Truncate if there are too many results
        if len(file_info) > 50:
            response += f"\n[{len(file_info) - 50} more results not shown]\n"
        
        return response
