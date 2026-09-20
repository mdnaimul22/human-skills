import os
import stat
import datetime
from typing import List, Dict, Any, Optional

from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle
from python.helpers.errors import handle_error


class ListDir(Tool):
    """Tool for listing directory contents with detailed information."""

    async def execute(self, **kwargs) -> Response:
        directory_path = kwargs.get("directory_path")
        
        # Validate inputs
        if not directory_path:
            return Response(message="Error: directory_path parameter is required", break_loop=False)
        
        if not os.path.isdir(directory_path):
            return Response(message=f"Error: '{directory_path}' is not a valid directory", break_loop=False)
        
        try:
            # Get directory contents
            entries = os.listdir(directory_path)
            
            # Sort entries (directories first, then files)
            entries.sort(key=lambda x: (0 if os.path.isdir(os.path.join(directory_path, x)) else 1, x.lower()))
            
            # Format the results
            response = self._format_directory_listing(directory_path, entries)
            
            # Log the action
            self.log.update(content=f"Listed contents of {directory_path} ({len(entries)} items)")
            
            return Response(message=response, break_loop=False)
            
        except Exception as e:
            handle_error(e)
            return Response(message=f"Error listing directory: {str(e)}", break_loop=False)
    
    def _format_directory_listing(self, directory_path: str, entries: List[str]) -> str:
        """Format directory listing for display."""
        if not entries:
            return f"Directory '{directory_path}' is empty"
        
        response = f"Contents of '{directory_path}':\n\n"
        response += "| Name | Type | Size | Modified | Permissions |\n"
        response += "|------|------|------|----------|------------|\n"
        
        for entry in entries:
            full_path = os.path.join(directory_path, entry)
            
            try:
                # Get file/directory information
                stat_info = os.stat(full_path)
                
                # Determine type
                if os.path.isdir(full_path):
                    entry_type = "Directory"
                    size = self._count_directory_items(full_path)
                    size_str = f"{size} items"
                else:
                    entry_type = "File"
                    size = stat_info.st_size
                    size_str = self._format_size(size)
                
                # Format modification time
                mod_time = datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M")
                
                # Format permissions
                perms = self._format_permissions(stat_info.st_mode)
                
                response += f"| {entry} | {entry_type} | {size_str} | {mod_time} | {perms} |\n"
                
            except Exception as e:
                # Handle errors for individual entries
                response += f"| {entry} | Error | N/A | N/A | {str(e)} |\n"
        
        return response
    
    def _count_directory_items(self, directory_path: str) -> int:
        """Count the number of items in a directory (recursively)."""
        try:
            count = 0
            for _, _, files in os.walk(directory_path):
                count += len(files)
            return count
        except Exception:
            return 0
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size for display."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def _format_permissions(self, mode: int) -> str:
        """Format file permissions for display."""
        perms = ""
        perms += "r" if mode & stat.S_IRUSR else "-"
        perms += "w" if mode & stat.S_IWUSR else "-"
        perms += "x" if mode & stat.S_IXUSR else "-"
        perms += "r" if mode & stat.S_IRGRP else "-"
        perms += "w" if mode & stat.S_IWGRP else "-"
        perms += "x" if mode & stat.S_IXGRP else "-"
        perms += "r" if mode & stat.S_IROTH else "-"
        perms += "w" if mode & stat.S_IWOTH else "-"
        perms += "x" if mode & stat.S_IXOTH else "-"
        return perms
