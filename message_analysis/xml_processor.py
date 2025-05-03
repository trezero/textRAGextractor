import xml.etree.ElementTree as ET
from pathlib import Path

def process_xml_files(xml_dir):
    """Process all XML files in directory and yield messages"""
    for xml_file in Path(xml_dir).glob('*.xml'):
        try:
            tree = ET.parse(xml_file)
            yield from tree.findall('.//sms')
        except ET.ParseError:
            continue
