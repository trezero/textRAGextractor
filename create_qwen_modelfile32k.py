import subprocess
import sys
import os
import re

# --- Configuration ---
BASE_MODEL = "qwen3:14b"
NEW_TAG_SUFFIX = "-32k" # Added to the base model name for the new tag
NEW_MODEL_NAME = f"{BASE_MODEL}{NEW_TAG_SUFFIX}"
NEW_MODLEFILE_NAME = f"{NEW_MODEL_NAME.replace(':', '_')}.Modelfile" # e.g., qwen3_14b-32k.Modelfile
TARGET_NUM_CTX = 32768
# --- End Configuration ---

def get_original_modelfile(model_name):
    """Fetches the original modelfile content using 'ollama show'."""
    print(f"Fetching original Modelfile for {model_name}...")
    try:
        # Use shell=True cautiously, ensure model_name is safe (it is here)
        # Using list form is safer if model_name could be user input
        # result = subprocess.run(['ollama', 'show', model_name, '--modelfile'],
        #                         capture_output=True, text=True, check=True)
        
        # Using shell=True might be necessary if 'ollama' isn't directly in PATH sometimes
        # Be aware of security implications if model_name came from untrusted input
        cmd = f"ollama show {model_name} --modelfile"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True, encoding='utf-8')
        
        print("Successfully fetched original Modelfile.")
        return result.stdout
    except FileNotFoundError:
        print(f"Error: 'ollama' command not found. Is Ollama installed and in your PATH?", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error executing 'ollama show':", file=sys.stderr)
        print(f"Command: {e.cmd}", file=sys.stderr)
        print(f"Return Code: {e.returncode}", file=sys.stderr)
        print(f"Output:\n{e.stderr}", file=sys.stderr)
        if "model 'qwen3:14b' not found" in e.stderr:
             print(f"\nSuggestion: Pull the model first using 'ollama pull {model_name}'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

def create_new_modelfile_content(original_content, target_ctx):
    """Parses the original content and creates the new Modelfile content."""
    print("Generating new Modelfile content...")
    new_lines = []
    template_content = []
    in_template_block = False
    from_line = None
    parameter_lines = []

    original_lines = original_content.strip().split('\n')

    for line in original_lines:
        stripped_line = line.strip()

        if stripped_line.upper().startswith("FROM "):
            from_line = line # Keep original formatting
        elif stripped_line.upper().startswith("PARAMETER "):
            # Exclude existing num_ctx parameter
            if not stripped_line.upper().startswith("PARAMETER NUM_CTX"):
                 parameter_lines.append(line) # Keep original formatting
        elif stripped_line.upper().startswith("TEMPLATE "):
            in_template_block = True
            # Handle potential inline template vs multiline ``` or """
            match = re.match(r"TEMPLATE\s+(\"\"\"|''')(.*)", stripped_line, re.IGNORECASE | re.DOTALL)
            if match:
                delimiter = match.group(1)
                template_content.append(line) # Keep the starting line
                # Check if template ends on the same line
                if stripped_line.endswith(delimiter):
                   in_template_block = False
            else:
                 # Simple template without quotes? Unlikely for complex ones but handle
                 template_content.append(line)
                 in_template_block = False # Assume single line if no delimiter

        elif in_template_block:
            template_content.append(line)
            # Check if this line ends the template block
            if stripped_line.endswith('"""') or stripped_line.endswith("'''"):
                in_template_block = False
        # Keep other directives like LICENSE, SYSTEM, ADAPTER etc. if needed (though less common)
        # For simplicity, we are mainly focusing on FROM, PARAMETER, TEMPLATE
        # You could add elif conditions here for other directives if necessary

    if not from_line:
        print("Error: Could not find 'FROM' directive in the original Modelfile.", file=sys.stderr)
        sys.exit(1)
    if not template_content:
         print("Warning: Could not find 'TEMPLATE' directive. The model might not behave as expected for chat.", file=sys.stderr)


    # Assemble the new Modelfile
    new_lines.append(from_line)
    new_lines.append(f"PARAMETER num_ctx {target_ctx}") # Add the target num_ctx
    new_lines.extend(parameter_lines) # Add other parameters
    new_lines.extend(template_content) # Add the template block

    print("New Modelfile content generated.")
    return "\n".join(new_lines)

def save_modelfile(filename, content):
    """Saves the content to a file."""
    try:
        with open(filename, "w", encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully saved new Modelfile to: {filename}")
    except IOError as e:
        print(f"Error writing file {filename}: {e}", file=sys.stderr)
        sys.exit(1)

# --- Main Execution ---
if __name__ == "__main__":
    original_mf_content = get_original_modelfile(BASE_MODEL)
    new_mf_content = create_new_modelfile_content(original_mf_content, TARGET_NUM_CTX)

    # Add a header comment to the generated file
    header = f"# Modelfile automatically generated by script\n"
    header += f"# Base Model: {BASE_MODEL}\n"
    header += f"# Customization: Set num_ctx to {TARGET_NUM_CTX}\n\n"
    final_content = header + new_mf_content

    save_modelfile(NEW_MODLEFILE_NAME, final_content)

    print("\n--- Next Steps ---")
    print(f"1. Verify the content of the generated file: {NEW_MODLEFILE_NAME}")
    print(f"2. Create the new Ollama model using the command:")
    print(f"   ollama create {NEW_MODEL_NAME} -f ./{NEW_MODLEFILE_NAME}")
    print(f"3. Run the new model:")
    print(f"   ollama run {NEW_MODEL_NAME}")
    print("\n   While running, you can verify settings with '/show settings' command inside Ollama.")
    print("\n--- Monitoring ---")
    print("   Keep an eye on your VRAM usage:")
    print("   - In WSL: Run 'nvidia-smi' ")
    print("   - On Windows Host: Task Manager -> Performance -> GPU")
    print("   If you experience crashes or extreme slowness, the 32k context might still be too demanding, even for the A6000, or Ollama might not be configured optimally.")