import os
from xml_processor import XMLProcessor

def main():
    os.makedirs('out', exist_ok=True)
    
    processor = XMLProcessor('input/test_input.xml')
    processor.parse_classes()
    
    with open('out/config.xml', 'w') as f:
        f.write(processor.generate_config_xml())
    
    with open('out/meta.json', 'w') as f:
        f.write(processor.generate_meta_json())
        
if __name__ == '__main__':
    main()
