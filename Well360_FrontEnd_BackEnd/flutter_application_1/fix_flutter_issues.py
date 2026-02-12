#!/usr/bin/env python3
"""
Automated Flutter Lint Fixer
Adds 'if (!mounted) return;' before context usage after await
"""

import re
import os
from pathlib import Path

# Files that need fixing (from flutter analyze output)
FILES_TO_FIX = [
    "lib/screens/hydration/lip_image_screen.dart",
    "lib/screens/hydration/form_screen.dart",
    "lib/screens/hydration/sequential_hydration_flow.dart",
    "lib/screens/fitness/fitness_home_screen.dart",
    "lib/screens/fitness/result_screen.dart",
    "lib/screens/auth/login_screen.dart",
    "lib/screens/auth/register_screen.dart",
    "lib/screens/mentalHealth/audio/audio_upload_screen.dart",
    "lib/screens/mentalHealth/video/camera_screen.dart",
]

def fix_context_usage(file_path):
    """
    Fix BuildContext usage after await by adding mounted checks
    """
    print(f"Fixing: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    modified = False
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if line uses context (ScaffoldMessenger, Navigator, etc.)
        uses_context = ('ScaffoldMessenger.of(context)' in line or
                       'Navigator.of(context)' in line or
                       'Navigator.pop(context)' in line or  
                       'Navigator.push(context)' in line or
                       'Theme.of(context)' in line or
                       'MediaQuery.of(context)' in line)
        
        if uses_context:
            # Look backwards to see if there's an await in the same function
            # and no mounted check yet
            j = i - 1
            has_await_before = False
            has_mounted_check = False
            indent = len(line) - len(line.lstrip())
            
            # Look back up to 20 lines or until we hit a function boundary
            for _ in range(20):
                if j < 0:
                    break
                prev_line = lines[j]
                
                # Stop if we hit a function declaration
                if 'void ' in prev_line or 'Future<' in prev_line:
                    break
                    
                if 'await ' in prev_line:
                    has_await_before = True
                    
                if 'if (!mounted) return;' in prev_line or 'if(!mounted)return;' in prev_line:
                    has_mounted_check = True
                    
                j -= 1
            
            # If there's an await before and no mounted check, add it
            if has_await_before and not has_mounted_check:
                # Add mounted check with same indentation as current line
                mounted_check = ' ' * indent + 'if (!mounted) return;'
                new_lines.append(mounted_check)
                modified = True
                print(f"  Added mounted check at line {i+1}")
        
        new_lines.append(line)
        i += 1
    
    if modified:
        # Write back
        with open(file_path, 'w', encoding='utf-8', newline='\r\n') as f:
            f.write('\n'.join(new_lines))
        print(f"  ✅ Fixed {file_path}")
        return True
    else:
        print(f"  ⏭️  No changes needed for {file_path}")
        return False

def main():
    print("=" * 60)
    print("  FLUTTER LINT AUTO-FIXER")
    print("=" * 60)
    print()
    
    fixed_count = 0
    skipped_count = 0
    
    for file_path_rel in FILES_TO_FIX:
        file_path = Path(file_path_rel)
        
        if not file_path.exists():
            print(f"⚠️  File not found: {file_path}")
            skipped_count += 1
            continue
        
        if fix_context_usage(file_path):
            fixed_count += 1
        else:
            skipped_count += 1
        print()
    
    print("=" * 60)
    print(f"  SUMMARY")
    print("=" * 60)
    print(f"  ✅ Fixed: {fixed_count}")
    print(f"  ⏭️  Skipped: {skipped_count}")
    print(f"  📝 Total: {len(FILES_TO_FIX)}")
    print()
    print("  Run 'flutter analyze' to verify fixes!")
    print("=" * 60)

if __name__ == "__main__":
    main()
