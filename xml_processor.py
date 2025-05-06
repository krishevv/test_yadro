import xml.etree.ElementTree as ET
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class Attribute:
    name: str
    type: str

@dataclass
class ClassInfo:
    name: str
    is_root: bool
    documentation: str
    attributes: List[Attribute]
    children: List['ClassInfo']
    min_multiplicity: Optional[str] = None
    max_multiplicity: Optional[str] = None

class XMLParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> Dict[str, Any]:
        pass

class XMIParser(XMLParser):
    def parse(self, file_path: str) -> Dict[str, Any]:
        tree = ET.parse(file_path)
        root = tree.getroot()
        return {
            'classes': self._parse_classes(root),
            'aggregations': self._parse_aggregations(root)
        }
    
    def _parse_classes(self, root: ET.Element) -> Dict[str, ClassInfo]:
        classes = {}
        for class_elem in root.findall('.//Class'):
            class_name = class_elem.get('name')
            classes[class_name] = ClassInfo(
                name=class_name,
                is_root=class_elem.get('isRoot') == 'true',
                documentation=class_elem.get('documentation', ''),
                attributes=[
                    Attribute(name=attr.get('name'), type=attr.get('type'))
                    for attr in class_elem.findall('.//Attribute')
                ],
                children=[]
            )
        return classes
    
    def _parse_aggregations(self, root: ET.Element) -> List[Dict[str, str]]:
        return [
            {
                'source': agg.get('source'),
                'target': agg.get('target'),
                'sourceMultiplicity': agg.get('sourceMultiplicity'),
                'targetMultiplicity': agg.get('targetMultiplicity')
            }
            for agg in root.findall('.//Aggregation')
        ]

class ModelProcessor:
    def __init__(self, parser: XMLParser):
        self.parser = parser
        self.classes: Dict[str, ClassInfo] = {}
        self.aggregations: List[Dict[str, str]] = []
    
    def process(self, file_path: str) -> None:
        data = self.parser.parse(file_path)
        self.classes = data['classes']
        self.aggregations = data['aggregations']
        self._process_aggregations()
    
    def _process_aggregations(self) -> None:
        for agg in self.aggregations:
            target_class = self.classes.get(agg['target'])
            if target_class:
                source_class = self.classes.get(agg['source'])
                if source_class:
                    multiplicity = agg['sourceMultiplicity'].split('..')
                    source_class.min_multiplicity = multiplicity[0]
                    source_class.max_multiplicity = multiplicity[-1] if len(multiplicity) > 1 else multiplicity[0]
                    target_class.children.append(source_class)

class ConfigGenerator:
    def __init__(self, model: ModelProcessor):
        self.model = model
    
    def generate(self) -> str:
        root_class = next((c for c in self.model.classes.values() if c.is_root), None)
        if root_class:
            return self._build_xml(root_class)
        return ""
    
    def _build_xml(self, class_info: ClassInfo, indent: int = 0) -> str:
        result = []
        indent_str = '    ' * indent
        
        result.append(f"{indent_str}<{class_info.name}>")
        
        for attr in class_info.attributes:
            result.append(f"{indent_str}    <{attr.name}>{attr.type}</{attr.name}>")
        
        for child in class_info.children:
            result.append(self._build_xml(child, indent + 1))
        
        result.append(f"{indent_str}</{class_info.name}>")
        return '\n'.join(result)

class MetaGenerator:
    def __init__(self, model: ModelProcessor):
        self.model = model
    
    def generate(self) -> str:
        meta_data = []
        for class_info in self.model.classes.values():
            class_meta = {
                'class': class_info.name,
                'documentation': class_info.documentation,
                'isRoot': class_info.is_root
            }
            
            if class_info.max_multiplicity is not None:
                class_meta['max'] = class_info.max_multiplicity
            
            if class_info.min_multiplicity is not None:
                class_meta['min'] = class_info.min_multiplicity
            
            class_meta['parameters'] = []
            
            for attr in class_info.attributes:
                class_meta['parameters'].append({
                    'name': attr.name,
                    'type': attr.type
                })
            
            for child in class_info.children:
                class_meta['parameters'].append({
                    'name': child.name,
                    'type': 'class'
                })
            
            meta_data.append(class_meta)
        
        return json.dumps(meta_data, indent=4)

class XMLProcessor:
    def __init__(self, input_file: str):
        self.input_file = input_file
        self.parser = XMIParser()
        self.model = ModelProcessor(self.parser)
        self.config_generator = ConfigGenerator(self.model)
        self.meta_generator = MetaGenerator(self.model)
    
    def parse_classes(self) -> None:
        self.model.process(self.input_file)
    
    def generate_config_xml(self) -> str:
        return self.config_generator.generate()
    
    def generate_meta_json(self) -> str:
        return self.meta_generator.generate()

