from pathlib import Path
import questionary
from .contact_manager import get_contacts
from .xml_processor import process_xml_files
from .ollama_client import analyze_conversation

def main():
    """Main application entry point"""
    # Get all contacts from XML files (sorted by most recent message)
    contacts = get_contacts('textMessageBackups')
    
    # Let user select a contact
    contact = questionary.select(
        "Select a contact to analyze (sorted by most recent message first):",
        choices=[f"{name} ({phone}) - Last: {date.strftime('%Y-%m-%d')}" 
                for (name, phone), date in contacts],
    ).ask()

    # Extract selected contact info
    selected_name, selected_phone = next(
        (n, p) for (n, p), _ in contacts 
        if f"{n} ({p}) - Last:" in contact
    )
    
    # Create output directory
    output_dir = Path("outputs/raw_messages")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract and save messages
    messages_file = output_dir / f"{selected_name.replace(' ', '_')}.txt"
    with open(messages_file, 'w') as f:
        for msg in process_xml_files('textMessageBackups'):
            if msg.get('address') == selected_phone:
                f.write(f"{msg.get('date')}: {msg.get('body')}\n")
    
    # Generate style guide
    style_guide = analyze_conversation(selected_name, messages_file)
    if style_guide:
        guide_dir = Path("outputs/style_guides")
        guide_dir.mkdir(parents=True, exist_ok=True)
        guide_file = guide_dir / f"conversationStyle_{selected_name.replace(' ', '_')}.md"
        with open(guide_file, 'w') as f:
            f.write(style_guide)
        print(f"Created style guide at: {guide_file}")
