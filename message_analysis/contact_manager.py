from collections import defaultdict
from .xml_processor import process_xml_files
from datetime import datetime

def get_contacts(xml_dir):
    """Extract unique contacts from XML files sorted by most recent message"""
    contacts = {}
    for msg in process_xml_files(xml_dir):
        phone = msg.get('address')
        name = msg.get('contact_name') or phone
        date_str = msg.get('date')
        try:
            date = datetime.fromtimestamp(int(date_str)/1000)
        except (ValueError, TypeError):
            date = datetime.min
            
        # Track most recent message date per contact
        if (name, phone) not in contacts or date > contacts[(name, phone)]:
            contacts[(name, phone)] = date
    
    # Sort by most recent message date (descending)
    return sorted(contacts.items(), key=lambda x: x[1], reverse=True)
