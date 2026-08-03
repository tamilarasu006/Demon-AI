import os
import re

tests_dir = "tests"

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Fix import module
    content = re.sub(r'import_module\("DEMON\.', 'import_module("OpenDEMON.', content)
    # Fix import DEMON
    content = re.sub(r'^import DEMON$', 'import OpenDEMON', content, flags=re.MULTILINE)
    # Fix from DEMON import
    content = re.sub(r'^from DEMON import', 'from OpenDEMON import', content, flags=re.MULTILINE)
    # Fix DEMON.channels
    content = content.replace("importlib.reload(DEMON.channels)", "importlib.reload(OpenDEMON.channels)")
    
    # Fix specific garbage at the end of files
    if "test_shell_exec.py" in filepath:
        content = content.replace('code"] == -1\n', '')
    if "test_code_interpreter_docker.py" in filepath:
        content = content.replace('ed_once_with(force=True)\n', '')
    if "test_stubs.py" in filepath:
        content = content.replace('() == []\n', '')
    if "test_config.py" in filepath:
        content = content.replace(' ds__\n', '')

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {filepath}")

for root, _, files in os.walk(tests_dir):
    for file in files:
        if file.endswith(".py"):
            fix_file(os.path.join(root, file))
