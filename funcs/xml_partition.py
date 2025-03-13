import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
import os
import copy

# 配置部分
def get_config():
    config = {
        'file_path': 'mcpath-in.xml',  # 输入XML文件路径
        'chiplet_count': 5,                    # 划分文件的数量
        'core_allocation': [1, 3, 2, 6, 4],       # 每个文件分配的核心数量
        'cache_allocation': [1, 1, 1, 3, 2],      # 每个文件分配的cache数量
        'node_techs': ['22nm', '45nm', '32nm', '65nm','90nm'],  # 每个文件对应的工艺节点参数
    }
    return config

# 替换或添加参数的函数
def replace_or_add_param(system, param_name, new_value):
    param = system.find(f"param[@name='{param_name}']")
    if param is not None:
        param.set("value", new_value)
    else:
        ET.SubElement(system, "param", name=param_name, value=new_value)

# XML划分的主要函数
def split_xml_with_config(config):
    file_path = config['file_path']
    n = config['chiplet_count']
    core_allocation = config['core_allocation']
    cache_allocation = config['cache_allocation']
    node_techs = config['node_techs']

    print(f"Starting split for file: {file_path}")
    print(f"Number of chiplets: {n}")
    print(f"Core allocation: {core_allocation}")
    print(f"Cache allocation: {cache_allocation}")
    print(f"Technology nodes: {node_techs}")

    # 读取并解析 XML 文件
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return
    except Exception as e:
        print(f"Error parsing XML file: {e}")
        return

    system = root.find(".//component[@id='system']")
    
    if system is None:
        print("Error: 'system' component not found in XML.")
        return

    # 自动从 XML 文件中提取 cores 和 caches
    cores = [core for core in system.findall("component") if core.attrib['id'].startswith('system.core')]
    l2s = [l2 for l2 in system.findall("component") if l2.attrib['id'].startswith('system.L2')]

    total_cores = len(cores)
    total_caches = len(l2s)

    print(f"Total cores found: {total_cores}")
    print(f"Total caches found: {total_caches}")

    if total_cores == 0 or total_caches == 0:
        print(f"Error: Cores or caches not found in XML file.")
        return

    # 创建指定数量的新的根节点，每个包含一个系统组件
    new_trees = [ET.ElementTree(ET.Element("component", id="root", name="root")) for _ in range(n)]
    new_systems = [ET.SubElement(new_trees[i].getroot(), "component", id="system", name="system") for i in range(n)]

    core_index = 0
    cache_index = 0

    for i, (num_cores, num_caches) in enumerate(zip(core_allocation, cache_allocation)):
        # 更新核心和 L2 参数
        ET.SubElement(new_systems[i], "param", name="number_of_cores", value=str(num_cores))
        ET.SubElement(new_systems[i], "param", name="number_of_L2s", value=str(num_caches))

        # 替换或添加工艺节点参数
        if node_techs and i < len(node_techs):
            replace_or_add_param(new_systems[i], "core_tech_node", node_techs[i])

        # 分配 cores 和 l2s 到新的系统组件中
        for j in range(num_cores):
            new_systems[i].append(copy_element(cores[core_index]))
            core_index += 1
        for k in range(num_caches):
            new_systems[i].append(copy_element(l2s[cache_index]))
            cache_index += 1

        # 将其余的原始系统参数和组件添加到每个新系统组件中
        for param in system.findall("param"):
            if param.attrib['name'] not in ["number_of_cores", "number_of_L2s", "core_tech_node"]:
                new_systems[i].append(copy_element(param))
        for component in system.findall("component"):
            if component.attrib['id'] not in [core.attrib['id'] for core in cores] + [l2.attrib['id'] for l2 in l2s]:
                new_systems[i].append(copy_element(component))

    # 保存新的 XML 文件
    base_name = os.path.splitext(file_path)[0]
    for i, new_tree in enumerate(new_trees):
        new_file_path = f"{base_name}_part{i+1}.xml"
        # 美化输出
        xml_str = ET.tostring(new_tree.getroot(), 'utf-8')
        pretty_xml_as_str = parseString(xml_str).toprettyxml(indent="  ")
        with open(new_file_path, 'w') as f:
            f.write(pretty_xml_as_str)
        print(f"Saved: {new_file_path}")

def copy_element(elem):
    """递归复制一个元素及其所有子元素和文本"""
    new_elem = ET.Element(elem.tag, elem.attrib)
    for child in elem:
        child_copy = copy_element(child)
        new_elem.append(child_copy)
    return new_elem

# 主函数入口
if __name__ == "__main__":
    config = get_config()  # 获取用户设置的配置
    split_xml_with_config(config)  # 按照配置执行文件划分
