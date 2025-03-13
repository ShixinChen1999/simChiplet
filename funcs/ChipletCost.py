# Import python libraries
import time
import math
import copy
import queue
import argparse
import random as rnd
import json



def read_file(filename):
    file = open(filename, "r")
    file_content = json.loads(file.read())
    file.close()
    return file_content

def write_file(filename, content):
    file = open(filename, "w")
    file.write(json.dumps(content, indent=4))
    file.close()

def compute_area_summary(cost_config):
    total_chiplet_area = 0
	# Smallest and largest coordinates occupied by a chiplet
    (minx, miny, maxx, maxy) = (float("inf"),float("inf"),-float("inf"),-float("inf"))
	# Iterate through chiplets
    for chiplet in cost_config["chiplets"]:
		#chiplet = chiplet_desc[chiplet_desc["name"]]
        (x,y) = (cost_config["chiplets"][chiplet]["position"]["x"],cost_config["chiplets"][chiplet]["position"]["y"])	            # Position
        (w,h) = (cost_config["chiplets"][chiplet]["dimensions"]["x"],cost_config["chiplets"][chiplet]["dimensions"]["y"])			# Dimensions
		# Add this chiplet's are to total area
        total_chiplet_area += (w * h)
		# Update min and max coordinates
        minx = min(minx, x)
        miny = min(miny, y)
        maxx = max(maxx, x + w)
        maxy = max(maxy, y + h)
	# Compute total interposer area
    chip_width = (maxx - minx)
    chip_height = (maxy - miny)
    total_interposer_area =  chip_width * chip_height
    area_summary = {
		"chip_width" : chip_width,	
		"chip_height" : chip_height,	
		"total_chiplet_area" : total_chiplet_area,
		"total_interposer_area" : total_interposer_area
	}
    return area_summary



def compute_manufacturing_cost(cost_config,area_summary):
	# First, compute the manufacturing cost per chiplet
    results_per_chiplet = {}
    for chiplet in cost_config["chiplets"]:
        results_per_chiplet[chiplet] = {}
        # chiplet = chiplets[chiplet_name]
        chiplet_name=chiplet
        chiplet=cost_config["chiplets"][chiplet]
        tech = cost_config[chiplet["technology"]]
        wr = tech["wafer_radius"]										# Wafer radius
        dd = tech["defect_density"]										# Defect density
        wc = tech["wafer_cost"]											# Wafer cost
        ca = chiplet["dimensions"]["x"] * chiplet["dimensions"]["y"]	# Chiplet area
        # Dies per wafer
        dies_per_wafer = int(math.floor(((math.pi * wr**2) / ca) - ((math.pi * 2 * wr) / math.sqrt(2 * ca))))
        results_per_chiplet[chiplet_name]["dies_per_wafer"] = format(dies_per_wafer,'.2f')
        # Manufacturing yield
        manufacturing_yield = 1.0 / (1.0 + dd * ca)
        results_per_chiplet[chiplet_name]["manufacturing_yield"] = format(manufacturing_yield,'.2f')
        # Known good dies
        known_good_dies = dies_per_wafer * manufacturing_yield
        results_per_chiplet[chiplet_name]["known_good_dies"] = format(known_good_dies,'.2f')
        # Cost
        cost = wc / known_good_dies
        results_per_chiplet[chiplet_name]["cost"] = cost
	# Next, compute the manufacturing cost of the interposer if an interposer is used
    results_interposer = {"cost" : 0}
    if cost_config["has_interposer"]:
        ip_tech =cost_config["interposer_technology"]
        ip_tech=cost_config[ip_tech]
        wr = ip_tech["wafer_radius"]									# Wafer radius
        dd = ip_tech["defect_density"]								# Defect density
        wc = ip_tech["wafer_cost"]									# Wafer cost
        ia = area_summary["total_interposer_area"]						# Interposer area
        # Dies per wafer
        dies_per_wafer = int(math.floor(((math.pi * wr**2) / ia) - ((math.pi * 2 * wr) / math.sqrt(2 * ia))))
        results_interposer["dies_per_wafer"] = format(dies_per_wafer,'.2f')
        # Manufacturing yield
        manufacturing_yield = 1.0 / (1.0 + dd * ia)
        results_interposer["manufacturing_yield"] = format(manufacturing_yield,'.2f')
        # Known good dies
        known_good_dies = dies_per_wafer * manufacturing_yield
        results_interposer["known_good_dies"] = format(known_good_dies,'.2f')
        # Cost
        cost = wc / known_good_dies
        results_interposer["cost"] = cost
	# Compute the overall cost per working chip
    py = cost_config["packaging_yield"]									# Packaging yield

    chip_total_cost=0
    for chiplet_name in cost_config["chiplets"]:
        chip_total_cost+=results_per_chiplet[chiplet_name]["cost"]
    total_cost = (chip_total_cost + results_interposer["cost"]) / py
    return {"total_cost" : format(total_cost,'.3f'), "chip_total_cost" : format(chip_total_cost,'.3f'),"interposer" : results_interposer, "chiplets" : results_per_chiplet}

def generate_cost_config(floorplan, dimension_file,cost_config):
    chiplets=[]
    with open(floorplan,"r") as flp:
        store_value = False
        for line in flp:
            if "Block" in line :
                store_value = True
                continue
            if store_value and "Chiplet" in line:
                name, x, y, rotation = line.split()
                chiplets.append([name, x, y, rotation])
            else:
                store_value = False
    
    dimension=[]
    with open(dimension_file, "r") as file:
        for line in file:
            _,_,width,height,name = line.split()
            dimension.append([name,width,height])
    
    for dim in dimension:
        for chip in chiplets:
            if chip[0]==dim[0]:
                dim.append(chip[1])
                dim.append(chip[2])
                dim.append(chip[3])
    
    new_cost_config= read_file(cost_config)

    if "chiplets" in new_cost_config:
        del new_cost_config["chiplets"]

    new_cost_config["chiplets"]={}
    for dim in dimension:
        #new_chiplet={dim[0]:{"dimensions":{"x":dim[1],"y":dim[2]},"technology" : "tech_1","rotation" : dim[5],"position": {"x" : dim[3], "y" : dim[4]}}}
        if int(dim[5])==1:
            new_cost_config["chiplets"][dim[0]]={"dimensions":{"x":float(dim[2])/100.0,"y":float(dim[1])/100.0},"technology" : "tech_1","rotation" : dim[5],"position": {"x" : float(dim[3])/100.0, "y" : float(dim[4])/100.0}}
        new_cost_config["chiplets"][dim[0]]={"dimensions":{"x":float(dim[1])/100.0,"y":float(dim[2])/100.0},"technology" : "tech_1","rotation" : dim[5],"position": {"x" : float(dim[3])/100.0, "y" : float(dim[4])/100.0}}
    # print(new_cost_config)

    return new_cost_config


def generate_cost_config_2(floorplan,cost_config): # for input format
    
    new_cost_config= read_file(cost_config)

    if "chiplets" in new_cost_config:
        del new_cost_config["chiplets"]

    new_cost_config["chiplets"]={}

    chiplets=[]
    with open(floorplan,"r") as flp:
        for line in flp:
            name,h,w,x,y = line.split()
            chiplets.append([name,h,w,x,y,0]) # defualt: not retota
            new_cost_config["chiplets"][name]={"dimensions":{"x":float(h)*1000.0,"y":float(w)*1000.0},"technology" : "tech_1","rotation" : 0,"position": {"x" : float(x)*1000.0, "y" : float(y)*1000.0}}

    return new_cost_config   

            

def cost_evaluate(flp_path,cost_template,cost_path):
    cost_config=generate_cost_config_2(flp_path,cost_template)

    write_file(cost_path,cost_config)

    area_summary=compute_area_summary(cost_config)
    cost=compute_manufacturing_cost(cost_config,area_summary)
    write_file(cost_path.split(".json")[0]+"_result.json",{**area_summary,**cost})

if __name__ == "__main__":
    parser = argparse.ArgumentParser()	
    parser.add_argument("-f", "--floorplan",required = True, help = "Path to cost config")
    parser.add_argument("-d","--dimension",required=True, help="Path to input Chiplet")
    parser.add_argument("-c", "--cost_config", required = True, help = "Path to cost config") 
    args = parser.parse_args()


    cost_config=generate_cost_config(args.floorplan, args.dimension,args.cost_config)

    write_file(args.cost_config.split(".")[0]+"_input.json",cost_config)

    area_summary=compute_area_summary(cost_config)
    cost=compute_manufacturing_cost(cost_config,area_summary)

    write_file(args.cost_config.split(".")[0]+"_result.json",{**area_summary,**cost})


