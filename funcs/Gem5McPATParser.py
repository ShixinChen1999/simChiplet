"""
[usage]:
python3 Gem5ToMcPAT-Parser.py -c ../m5out/config.json -s ../m5out/stats.txt -t template.xml

# Tested
python 3.6.9
python 3.8.5

"""
import argparse
import sys
import json
import re
from xml.etree import ElementTree as ET
from xml.dom import minidom
import copy
import types
import logging
import numbers


def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def create_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Gem5 to McPAT parser")

    parser.add_argument(
        '--config', '-c', type=str, required=True,
        metavar='PATH',
        help="Input config.json from Gem5 output.")
    parser.add_argument(
        '--stats', '-s', type=str, required=True,
        metavar='PATH',
        help="Input stats.txt from Gem5 output.")
    parser.add_argument(
        '--template', '-t', type=str, required=True,
        metavar='PATH',
        help="Template XML file")
    parser.add_argument(
        '--temp', '-tt', type=argparse.FileType('w'), default="temp-template.xml",
        metavar='PATH',
        help="Template file for McPAT input in XML format (default: temp-template.xml)")    
    parser.add_argument(
        '--output', '-o', type=argparse.FileType('w'), default="mcpat-in.xml",
        metavar='PATH',
        help="Output file for McPAT input in XML format (default: mcpat-in.xml)")

    return parser


class PIParser(ET.TreeBuilder):
    def __init__(self, *args, **kwargs):
        # call init of superclass and pass args and kwargs
        super(PIParser, self).__init__(*args, **kwargs)

        self.CommentHandler = self.comment
        self.ProcessingInstructionHandler = self.pi
        self.start("document", {})

    def close(self):
        self.end("document")
        return ET.TreeBuilder.close(self)

    def comment(self, data):
        self.start(ET.Comment, {})
        self.data(data)
        self.end(ET.Comment)

    def pi(self, target, data):
        self.start(ET.PI, {})
        self.data(target + " " + data)
        self.end(ET.PI)


def parse(source):
    parser = ET.XMLParser(target=PIParser())
    return ET.parse(source, parser=parser)


def readStatsFile(statsFile):
    global stats
    stats = {}
    F = open(statsFile)
    ignores = re.compile(r'^---|^$')# find blank line or line start with "---"
    statLine = re.compile(
        r'([a-zA-Z0-9_\.:-]+)\s+([-+]?[0-9]+\.[0-9]+|[-+]?[0-9]+|nan|inf)?') # find line with kinds and values
    count = 0
    for line in F:
        # ignore empty lines and lines starting with "---"
        if not ignores.match(line):
            count += 1
            if statLine.match(line) is not None:
                statKind = statLine.match(line).group(1) 
                statValue = statLine.match(line).group(2)
                #print(count,statKind,statValue)
                if statValue == 'nan':
                    #logging.warning("%s is nan. Setting it to 0" % statKind)
                    statValue = '0'
                stats[statKind] = statValue
    F.close()


def readConfigFile(configFile):
    global config
    F = open(configFile)
    config = json.load(F)
    #print (config)
    #print (config["system"]["membus"])
    # print(config["system"]["cpu"][0]["numThreads"])# number is a list array 
    # print(config["system"]["cpu"][1]["numThreads"])
    # print(config["system"]["cpu"][1]["pwr_gating_latency"])
    
    F.close()


def readMcpatFile(templateFile):
    global templateMcpat
    templateMcpat = parse(templateFile)
    # ET.dump(templateMcpat)


def prepareTemplate(tempFile,design_config_path):
    design_config =  json.load(open(design_config_path))
    numCores =  int(design_config["processor"]["num_cpus"]) #len(config["system"]["cpu"])
    numL2 = int(design_config["processor"]["num_l2cache"])#len(config["system"]["ruby"])
    #numCores = 2
    # print("cores=",numCores)
    #privateL2 = 'l2cache' in config["system"]["cpu"][0].keys() # We can use this to check if the key exist
    privateL2 = 'l2_cntrl0' in config["system"]["ruby"]
    sharedL2 = 'l2' in config["system"].keys()

    # if 'l1_cntrl' in str(config["system"]["ruby"].keys()):
    #     print(config["system"]["ruby"]['l1_cntrl0'])
    #     exit()
    #print(numCores,privateL2,sharedL2)

    if privateL2:
        numL2 = numL2
    elif sharedL2:
        numL2 = 1
    else:
        numL2 = 0
    elemCounter = 0
    root = templateMcpat.getroot()
    for child in root[0][0]:
        elemCounter += 1  # to add elements in correct sequence

        if child.attrib.get("name") == "number_of_cores":
            child.attrib['value'] = str(numCores)
        if child.attrib.get("name") == "number_of_L2s":
            child.attrib['value'] = str(numL2)
        if child.attrib.get("name") == "Private_L2":
            if sharedL2:
                Private_L2 = str(0)
            else:
                Private_L2 = str(1)
            child.attrib['value'] = Private_L2
        temp = child.attrib.get('value')
        
        # numCores = len(config["system"]["cpu"])
        # temp = confStr
        # if ("l1_cntrl" in confStr):
        #     confStr = "(" + temp.replace("l1_cntrl.", "l1_cntrl0.") + ")"
        #     for i in range(1, numCores):
        #         confStr = confStr+ \
        #                 " + (" + temp.replace("l1_cntrl.", "l1_cntrl"+str(i)+".") + ")" 
        #     print(confStr)
        #     exit()

        # if isinstance(temp, str) and temp.split('.')[0] == "stats":
        #     print(temp)
        #     continue
        # if isinstance(temp, str) and ("cntrl" in temp):
        #     print(temp)
        #     exit()
        # to consider all the cpus in total cycle calculation # e.g. stats.system.cpu.numCycles
        
        if isinstance(temp, str) and ("cpu." in temp ) and temp.split('.')[0] == "stats":
            value = "(" + temp.replace("cpu.", "cpu0.") + ")" # stats.system.cpu.numCycles
            for i in range(1, numCores):
                value = value + \
                    " + (" + temp.replace("cpu.", "cpu"+str(i)+".") + ")"
            #print(value)
            child.attrib['value'] = value # eg. (stats.system.cpu0.numCycles) + (stats.system.cpu1.numCycles) + (stats.system.cpu2.numCycles)...

        # if isinstance(temp, str) and ("l1_cntrl." in temp ) and temp.split('.')[0] == "stats":
        #     print(temp)
        #     value = "(" + temp.replace("l1_ctrls.", "l1_ctrls0.") + ")" # stats.system.cpu.numCycles
        #     for i in range(1, numCores):
        #         value = value + \
        #             " + (" + temp.replace("l1_ctrls.", "l1_ctrls"+str(i)+".") + ")"
        #     #print(value)
        #     child.attrib['value'] = value 

        # if isinstance(temp, str) and ("mem_ctrls." in temp ) and temp.split('.')[0] == "stats":
        #     value = "(" + temp.replace("mem_ctrls.", "mem_ctrls0.") + ")" # stats.system.cpu.numCycles
        #     for i in range(1, numCores):
        #         value = value + \
        #             " + (" + temp.replace("mem_ctrls.", "mem_cntrls"+str(i)+".") + ")"
        #     #print(value)
        #     child.attrib['value'] = value 

       
        # remove a core template element and replace it with number of cores template elements
        if child.attrib.get("name") == "core":
            coreElem = copy.deepcopy(child)
            coreElemCopy = copy.deepcopy(coreElem)
            for coreCounter in range(numCores):
                coreElem.attrib["name"] = "core" + str(coreCounter)
                coreElem.attrib["id"] = "system.core" + str(coreCounter)
                for coreChild in coreElem:
                    childId = coreChild.attrib.get("id")
                    childValue = coreChild.attrib.get("value")
                    childName = coreChild.attrib.get("name")
                    
                    
                    
                        #exit()

                    if isinstance(childName, str) and childName == "x86":
                        if config["system"]["cpu"][coreCounter]["isa"][0]["type"] == "X86ISA": #RiscvISA
                            childValue = "1"
                        else:
                            childValue = "0"
                    if isinstance(childId, str) and "core" in childId: #system.core0.predictor
                        #print(childId,childValue,childName)
                        childId = childId.replace(
                            "core", "core" + str(coreCounter)) #system.core0.predictor

                    if isinstance(childName, str) and (childName== "icache" or childName== "dcache" ): # propress icache
                        for level2Child in coreChild:
                            level2ChildValue =  level2Child.attrib.get("value")    
                            
                            if "l1_cntrl" in str(level2ChildValue):
                                level2ChildValue = level2ChildValue.replace("l1_cntrl.", "l1_cntrl"+ str (coreCounter)+ ".")
                                level2Child.attrib["value"] = level2ChildValue
                            elif "mem_ctrls" in str(level2ChildValue):
                                level2ChildValue = level2ChildValue.replace("mem_ctrls.", "mem_ctrls"+ str (coreCounter)+ ".")
                                level2Child.attrib["value"] = level2ChildValue
                                #print(level2ChildValue)
                            # print(level2ChildValue)
                            # print(coreCounter)
                        #exit()
                        # print(childId,childValue,childName)
                        # exit()
                    if isinstance(childValue, str) and "cpu." in childValue and "stats" in childValue.split('.')[0]:
                        #print(childId,childValue,childName)
                        childValue = childValue.replace(
                            "cpu.", "cpu" + str(coreCounter) + ".")
                    

                    if isinstance(childValue, str) and "cpu." in childValue and "config" in childValue.split('.')[0]:
                        #print(childId,childValue,childName)
                        childValue = childValue.replace(
                            "cpu.", "cpu." + str(coreCounter) + ".")

                   

                  
                    if len(list(coreChild)) != 0: #8
                        #print(len(list(coreChild)))
                        for level2Child in coreChild:
                            level2ChildValue = level2Child.attrib.get("value")
                            if isinstance(level2ChildValue, str) and "cpu." in level2ChildValue and "stats" in level2ChildValue.split('.')[0]:
                                level2ChildValue = level2ChildValue.replace(
                                    "cpu.", "cpu" + str(coreCounter) + ".")
                            if isinstance(level2ChildValue, str) and "cpu." in level2ChildValue and "config" in level2ChildValue.split('.')[0]:
                                level2ChildValue = level2ChildValue.replace(
                                    "cpu.", "cpu." + str(coreCounter) + ".")
                            level2Child.attrib["value"] = level2ChildValue
                    if isinstance(childId, str):
                        coreChild.attrib["id"] = childId
                    if isinstance(childValue, str):
                        coreChild.attrib["value"] = childValue
                root[0][0].insert(elemCounter, coreElem)
                coreElem = copy.deepcopy(coreElemCopy)
                elemCounter += 1
            root[0][0].remove(child)
        

        # # remove a L2 template element and replace it with number of L2 template elements
        # if child.attrib.get("name") == "mc":
        #     #print(child.attrib.get("name"))
        #     coreElem = copy.deepcopy(child)
        #     coreElemCopy = copy.deepcopy(coreElem)
        #     for coreCounter in range(numCores):
        #         #coreElem.attrib["name"] = "core" + str(coreCounter)
        #         #coreElem.attrib["id"] = "system.core" + str(coreCounter)
        #         for coreChild in coreElem:
        #             childId = coreChild.attrib.get("id")
        #             childValue = coreChild.attrib.get("value")
        #             childName = coreChild.attrib.get("name")
                
                    
                    
        #             if isinstance(childValue, str) and "mem_ctrls" in childValue and "stats" in childValue:
        #                 #print(childValue) 
        #                 # print("mc:",childValue)
        #                 childValue = childValue.replace(
        #                     "mem_ctrls.", "mem_ctrls" + str(coreCounter) + ".")
        #                 coreChild.attrib["value"] = childValue
        #                 # print(childValue)
        #                 # exit()
                        
                    
        #         #exit()
        #         root[0][0].insert(elemCounter, coreElem)
        #         coreElem = copy.deepcopy(coreElemCopy)
        #         elemCounter += 1
        #     root[0][0].remove(child)
        # elemCounter -= 1

        if child.attrib.get("name") == "L2":
            if privateL2:
                l2Elem = copy.deepcopy(child)
                l2ElemCopy = copy.deepcopy(l2Elem)
                for l2Counter in range(numL2):
                        

                    l2Elem.attrib["name"] = "L2" + str(l2Counter)
                    l2Elem.attrib["id"] = "system.L2" + str(l2Counter)
                    for l2Child in l2Elem:
                        l2ChildValue = l2Child.attrib.get("value")
                        if isinstance(l2ChildValue, str) and "l2_cntrl" in str(l2ChildValue):
                            l2ChildValue = l2ChildValue.replace("l2_cntrl.", "l2_cntrl"+ str (l2Counter)+ ".")
                            l2Child.attrib["value"] = l2ChildValue

                        # if isinstance(childValue, str) and "cpu." in childValue and "stats" in childValue.split('.')[0]:
                        #     childValue = childValue.replace(
                        #         "cpu.", "cpu" + str(l2Counter) + ".")
                        # if isinstance(childValue, str) and "cpu." in childValue and "config" in childValue.split('.')[0]:
                        #     childValue = childValue.replace(
                        #         "cpu.", "cpu." + str(l2Counter) + ".")
                        # if isinstance(childValue, str):
                        #     l2Child.attrib["value"] = childValue
                    root[0][0].insert(elemCounter, l2Elem)
                    l2Elem = copy.deepcopy(l2ElemCopy)
                    elemCounter += 1
                root[0][0].remove(child)
            else:
                child.attrib["name"] = "L20"
                child.attrib["id"] = "system.L20"
                for l2Child in child:
                    childValue = l2Child.attrib.get("value")
                    if isinstance(childValue, str) and "cpu.l2cache." in childValue:
                        childValue = childValue.replace("cpu.l2cache.", "l2.")

        elemCounter -= 1
        
    prettify(root)
    templateMcpat.write(tempFile)
    # exit()


def getConfValue(confStr):
   
    # For special case
    # if("itb" in confStr):
    #     confStr=confStr.replace("itb", "mmu.itb",1)
    
    spltConf = re.split('\.', confStr)


    currConf = config # all configs
    
        
    #print('spltConf=',spltConf)
    currHierarchy = ""
    

    for x in spltConf:
        
        # if ("l1_cntrl" in confStr):# debugging
        #     # temp = confStr
        #     # print(confStr)
        #     # if isinstance(temp, str) :
        #     #     value = "(" + temp.replace("l1_cntrl.", "l1_cntrl0.") + ")" # stats.system.cpu.numCycles
        #     #     for i in range(1, numCores):
        #     #         value = value + \
        #     #             " + (" + temp.replace("cpu.", "cpu"+str(i)+".") + ")"
        #     #     #print(value)
        #     #     child.attrib['value'] = value # eg. (stats.system.cpu0.numCycles) + (stats.system.cpu1.numCycles) + (stats.system.cpu2.numCycles)...

        #     currHierarchy += x
        #     if  str.isdigit(x):
        #         if not isinstance(currConf,dict):# avoid cpu.0
        #             #print("1",currHierarchy)
        #             currConf = currConf[int(x)] 
        #             break
        #         else:
        #             #print("2",currHierarchy, "last_x=",last_x)
        #             currConf = currConf[last_x][int(x)]
                    
                    
                   
    
        #     elif x in currConf and (not currConf==None):
        #         if not isinstance(currConf[x], dict) :#number or list 
        #             #currConf = currConf[int(x)]
        #             #print('3',currHierarchy)
        #             if isinstance(currConf[x],numbers.Number) :
        #                 #print('4',currHierarchy)
        #                 # print(currConf[int(x)]['itb'])
        #                 currConf = currConf[x]
        #                 break
        #             elif isinstance(currConf[x],list):# system.cpu is a list type
        #                 #print('5',currHierarchy)
                    
        #                 #print("%s meet list type" % currHierarchy, x) 
        #                 last_x = x
        #                 #currConf = currConf[int(x)]

        #             else:
        #                 #print('7',currHierarchy)
        #                 #print(currHierarchy)
        #                 print("%s does not exist in config" % currHierarchy)
        #                 #currConf = currConf[x]
        #                 # print(currConf)
        #                 # exit()
        #             #exit()
        #             # if currConf[x]:
        #             #else:
        #             # else:
        #             #     print("%s may meet system.cpu" % currHierarchy)
        #             # #print("item currConf=",currConf[x][0])
        #             #     #this is mostly for system.cpu* as system.cpu is an array
        #             #     #This could be made better
                        
        #             #     print(currConf['numThreads'])
        #             #     exit()
        #             #     if 'cpu_id' not in currConf[0]:
        #             #         print("%s does not exist in config" % currHierarchy)
        #             #     else:
        #             #         currConf = currConf[x]
        # #         else:
        # #                 print("***WARNING: %s does not exist in config.***" % currHierarchy)
        # #                 print("\t Please use the right config param in your McPAT template file")
        #         else:# remaining is dict
        #             #print('6',currHierarchy)
        #             currConf = currConf[x]
        #     else:
        #         #print('8',currHierarchy)
        #         #print(currConf['mmu']['itb']['size'])
        #         print("%s does not exist in config" % currHierarchy)
        #     currHierarchy += "."
        # else:
        currHierarchy += x
        if  str.isdigit(x):
            if not isinstance(currConf,dict):# avoid cpu.0
                currConf = currConf[int(x)] 
                break
            else:
                #print("cpu_id=",currConf[last_x][int(x)]['cpu_id'])
                currConf = currConf[last_x][int(x)]
                #print(currConf)
            #print("digit currConf=",currConf)
            #exit()
            
        elif x in currConf and (not currConf==None):
            #print("is dict=",isinstance(currConf, dict))
            #if isinstance(currConf, types.ListType):
            if not isinstance(currConf[x], dict) :#number or list 
                #currConf = currConf[int(x)]
                
                if isinstance(currConf[x],numbers.Number) :
                    currConf = currConf[x]
                    break
                elif isinstance(currConf[x],list):# system.cpu is a list type
                    
                
                    #print("%s meet list type" % currHierarchy) 
                    last_x = x
                else:
                    currConf=currConf
                    #print("%s does not exist in config" % currHierarchy)
                    #currConf = currConf[x]
                    # print(currConf)
                    # exit()
                #exit()
                # if currConf[x]:
                #else:
                # else:
                #     print("%s may meet system.cpu" % currHierarchy)
                # #print("item currConf=",currConf[x][0])
                #     #this is mostly for system.cpu* as system.cpu is an array
                #     #This could be made better
                    
                #     print(currConf['numThreads'])
                #     exit()
                #     if 'cpu_id' not in currConf[0]:
                #         print("%s does not exist in config" % currHierarchy)
                #     else:
                #         currConf = currConf[x]
    #         else:
    #                 print("***WARNING: %s does not exist in config.***" % currHierarchy)
    #                 print("\t Please use the right config param in your McPAT template file")
            else:# remaining is dict
                currConf = currConf[x]
        else:
            currConf=currConf
            #print("%s does not exist in config" % currHierarchy)
        currHierarchy += "."
    
    #print("item currConf",currConf)
    #exit()
    #logging.info(confStr, currConf)

    if isinstance(currConf, numbers.Number):
        return currConf
    else:
        return None

def dumpMcpatOut(outFile):
    """
    outfile: file reference to "mcpat-in.xml"
    """

    rootElem = templateMcpat.getroot()
    
    configMatch = re.compile(r'config\.([][a-zA-Z0-9_:\.]+)')
    # replace params with values from the GEM5 config file
   

    for param in rootElem.iter('param'):
        #print("-------------------")
       
        name = param.attrib['name']
        value = param.attrib['value']
        
        #print(name,value)
        
        # # if there is a config in this attrib
        if 'config' in value:
            
            
            allConfs = configMatch.findall(value)
            

            for conf in allConfs:
                confValue = getConfValue(conf)
                #print("conf=",conf,"confValue=",confValue)
                if isinstance(confValue,numbers.Number):
                    
                    value = re.sub("config." + conf, str(confValue), value)
                    # print(allConfs,'=',confValue,"=",value,"=", eval(str(value)))
                    # exit()
                # else:
                #     print("cannot find an item [%s] in the json" % conf)
                    #exit()

                
                if "," in value and not ("config" in value): # multi items in the script
                    #print(value)
                    exprs = re.split(',', value)
                    
                    #print("0=",exprs[0])
                    # print(eval(exprs[0][1:]))
                    
                    for i in range(len(exprs)):
                        #print("i=",i, exprs[i])
                        try:
                            exprs[i] = str(eval(exprs[i]))
                        except Exception as e:
                            #logging.error("Possibly " + conf + " does not exist in config" +
                                        # "\n\t set correct key string in template value")
                            raise

                    param.attrib['value'] = ','.join(exprs)
                elif "," in value and ("config" in value):
                    param.attrib['value'] = value #str(eval(str(value)))
                    #print(allConfs,'=>',confValue,"=>",value,"=", value)
                else:
                    
                    param.attrib['value'] = str(eval(str(value)))
            #print(allConfs,'=>',confValue,"=>",value,"=", eval(str(value)))
    #exit()
    # replace stats with values from the GEM5 stats file
    statRe = re.compile(r'stats\.([a-zA-Z0-9_:\.]+)')
    for stat in rootElem.iter('stat'):
        name = stat.attrib['name']
        value = stat.attrib['value']
        
        #if 'stats' in value  and not "fpRegfileWrites" in value and not "workload" in value:
        if 'stats' in value:
            allStats = statRe.findall(value)
            
            expr = value
            for i in range(len(allStats)):
                # print(allStats[i])
                if allStats[i] in stats:#and ("numIdleCycles" not in allStats[i]):
                    expr = re.sub('stats.%s' %
                                  allStats[i], stats[allStats[i]], expr)
                #handle special
                # elif "idleCycles" in allStats[i]:
                #     try:
                #         cpu_stat = allStats[i].replace(".idleCycles",".exec_context.thread_0.numIdleCycles")
                #         expr = re.sub('stats.%s' %
                #                       allStats[i], stats[cpu_stat], expr)
                #         # print(expr)
                        
                #     except KeyError:
                #         logging.warning(allStats[i] +
                #                         " does not exist in stats" +
                #                         "\n\t Maybe invalid stat in McPAT template file")
                    
                elif ".cpu0." in allStats[i]:
                    try:
                        cpu_stat = allStats[i].replace(".cpu0.", ".cpu.")
                        expr = re.sub('stats.%s' %
                                      allStats[i], stats[cpu_stat], expr)
                    except KeyError:
                        
                        # logging.warning(allStats[i] +
                        #                 " does not exist in stats" +
                        #                 "\n\t Maybe invalid stat in McPAT template file, set to 0")
                        expr = '0'
                        #exit()
                

                else:
                    # expr = re.sub('stats.%s' % allStats[i], str(1), expr)
                    # logging.warning(allStats[i] +
                    #                 " does not exist in stats" +
                    #                 "\n\t Maybe invalid stat in McPAT template file,  set to 0")
                    expr = '0'
                    #exit()
            if 'config' not in expr and 'stats' not in expr:# overall cycles
                stat.attrib['value'] = str(eval(expr))

    # Write out the xml file
    templateMcpat.write(outFile)


# def main():
#     global args
#     parser = create_parser()
#     args = parser.parse_args()
#     readStatsFile(args.stats)
#     readConfigFile(args.config)
#     readMcpatFile(args.template)

#     prepareTemplate(args.temp)

#     dumpMcpatOut(args.output)

def gem5tomcpat(config, stats,design_config,template, temp ,output ):

    readStatsFile(stats)
    readConfigFile(config)
    readMcpatFile(template)

    prepareTemplate(temp,design_config)

    dumpMcpatOut(output)

if __name__ == '__main__':
    main()
