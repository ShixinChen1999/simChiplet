import argparse
import sys
import os
import json
import re
import random
from xml.etree import ElementTree as ET
from xml.dom import minidom
import copy
import types
import logging
import numbers
import csv
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np

from matplotlib.ticker import FormatStrFormatter
from matplotlib.colors import LinearSegmentedColormap

from funcs.Gem5McPATParser import gem5tomcpat
from funcs.McpatHotspotParser import mcpat_to_hotspot
from funcs.ChipletCost import cost_evaluate
from funcs.SpecBench import spec_runner

def run_gem5(simulation_configs):

    config_path = simulation_configs["design_spec"]["path"]
    outdir = simulation_configs["report"]["path"]

    global config
    config = json.load(open(config_path))
    config_origin = config

    # processor design
    cpu_type=config["processor"]["cpu_type"]
    num_cpus=config["processor"]["num_cpus"] 
    l1d_size=config["processor"]["l1d_size"]
    l1i_size=config["processor"]["l1i_size"]
    l1d_assoc=config["processor"]["l1d_assoc"]
    num_l2cache=config["processor"]["num_l2cache"]
    l2_size=config["processor"]["l2_size"]
    l2_assoc=config["processor"]["l2_assoc"]
    num_dirs=config["processor"]["num_dirs"]
    cacheline_size=config["processor"]["cacheline_size"]
    # memory design
    mem_size=config["memory"]["mem-size"]
    mem_type=config["memory"]["mem-type"]
    mem_channels=config["memory"]["mem-channels"]
    mem_ranks=config["memory"]["mem-ranks"]
    # connection design
    topo=config["topology"]["topo"]
    mesh_row=config["topology"]["mesh_rows"]
    number_of_virtual_network=config["topology"]["number_of_virtual_networks"]
    control_msg_size=config["topology"]["control_msg_size"]
    ni_flit_size=config["topology"]["ni_flit_size"]
    vcs_per_vnet=config["topology"]["vcs_per_vnet"]
    buffers_per_data_vc=config["topology"]["buffers_per_data_vc"]
    buffers_per_ctrl_vc=config["topology"]["buffers_per_ctrl_vc"]
    chiplet_sim=config["topology"]["chiplet_sim"]


   
    #simulator design
    ISA = simulation_configs["simulator"]["ISA"]
    simulator=os.path.join(simulation_configs["simulator"]["gem5-root"],str(ISA)+"/gem5.opt")
    se_path = simulation_configs["simulator"]["se-path"]
    max_ticks=simulation_configs["simulator"]["max-ticks"]
    max_time=simulation_configs["simulator"]["maxtime"]
    link_latency=simulation_configs["simulator"]["link-latency"]

   
    #workload specifictaion
    bench=simulation_configs["simulator"]["app"]
    benchmark_config=simulation_configs["benchmark"][bench] # is the path of workload / spec2006
    candidate =  benchmark_config["candidate"]
    report_dir = os.path.join(simulation_configs["report"]["path"],candidate+"/log.dse")
    workload=os.path.join(benchmark_config["root_path"],candidate)
    options=benchmark_config["options"]
    
   
    # report path
   
    print(f"Simulation: {simulator}, Workload: {workload}")
    print("--"*10+"Running GEM5"+"--"*10)
   
    

    l1d_size =str(config["processor"]["l1d_size"])
    l1i_size =str(config["processor"]["l1i_size"])
    l1d_assoc=str(config["processor"]["l1d_assoc"])
    num_l2cache=str(config["processor"]["num_l2cache"])
    l2_size=str(config["processor"]["l2_size"])
    l2_assoc=str(config["processor"]["l2_assoc"])
    num_dirs=str(config["processor"]["num_dirs"])
    cacheline_size=str(config["processor"]["cacheline_size"])

    mem_size=config["memory"]["mem-size"]
    mem_type=config["memory"]["mem-type"]
    mem_channels=config["memory"]["mem-channels"]
    mem_ranks=config["memory"]["mem-ranks"]
    topo=config["topology"]["topo"]
    mesh_row=config["topology"]["mesh_rows"]
    number_of_virtual_network=config["topology"]["number_of_virtual_networks"]
    control_msg_size=config["topology"]["control_msg_size"]
    ni_flit_size=config["topology"]["ni_flit_size"]
    vcs_per_vnet=config["topology"]["vcs_per_vnet"]
    buffers_per_data_vc=config["topology"]["buffers_per_data_vc"]
    buffers_per_ctrl_vc=config["topology"]["buffers_per_ctrl_vc"]
    
    
    


    cmd_line=str(simulator)+" -d "+str(outdir)+" "+str(se_path)+" --cpu-type "+str(cpu_type) \
        +" --num-cpu="+str(num_cpus) \
        +" --l1d_size="+str(l1d_size) \
        +" --l1i_size="+str(l1i_size) \
        +" --l1d_assoc="+str(l1d_assoc) \
        +" --num-l2cache="+str(num_l2cache) \
        +" --l2_size="+str(l2_size) \
        +" --l2_assoc="+str(l2_assoc) \
        +" --cacheline_size="+str(cacheline_size) \
        +" --num-dirs="+str(num_dirs) \
        +" --ruby --mem-size="+str(mem_size) \
        +" --mem-type="+str(mem_type) \
        +" --mem-channels="+str(mem_channels) \
        +" --mem-ranks="+str(mem_ranks) \
        +" --topology="+str(topo) \
        +" --vcs-per-vnet="+str(vcs_per_vnet) \
        +" --mesh-rows="+str(mesh_row) \
        +" --maxtime="+str(max_time) \
        +" -c "+str(workload) \
        +" -o \""+str(options)+"\"" \
        +" --link-latency="+str(link_latency) \
        +" > "+str(outdir)+"/gem5.log 2>&1"
    # print(f"GEM5 simulation command line: {cmd_line}")
    print(cmd_line)
    
    os.system(cmd_line)
    


def report_csv(report_file):

   


    re_processor = 'Processor: \n'
    # re_core = 'Core:\n'
    # re_l2 = 'L2\n'
    re_area = r'\s*Area\s*=\s*([0-9.]*)\s*\w*\^\w*\n'
    re_to_leak = r'\s*Peak\s*Power\s*=\s*([0-9.]*)\s*\w*\n'
    re_pe_leak = r'\s*Total\s*Leakage\s*=\s*([0-9.]*)\s*\w*\n'
    re_peak = r'\s*Peak\s*Dynamic\s*=\s*([0-9.]*)\s*\w*\n'
    re_subth = r'\s*Subthreshold\s*Leakage\s*=\s*([0-9.]*)\s*\w*\n'
    re_subth2 = r'\s*Subthreshold\s*Leakage\s*with\s*power\s*gating\s*=\s*([0-9.]*)\s*\w*\n'
    re_gate = r'\s*Gate\s*Leakage\s*=\s*([0-9.]*)\s*\w*\n'
    re_run = r'\s*Runtime\s*Dynamic\s*=\s*([0-9.e-]*)\s*\w*\n'

    processor = re.compile(re_processor+re_area+re_to_leak+re_pe_leak+re_peak+re_subth+re_subth2+re_gate+re_run)
    
    succ_case=[]
    print("--"*10+"Generating Report"+"--"*10)
   

    out_path=os.path.join(report_file)
    stats_path=os.path.join(out_path,"stats.txt")
    log_path=os.path.join(out_path,"gem5.log")
    power_path=os.path.join(out_path,"mcpat/mcpat-out.txt")
    flp_path=os.path.join(out_path,"hotspot/floorplan.flp")
    blk_path=os.path.join(out_path,"hotspot/hardblock.txt")
    cost_path=os.path.join(out_path,"hotspot/cost_result.json")
    thermal_path=os.path.join(out_path,"hotspot/thermal_layer0.txt")

    
    
    if os.path.exists(stats_path) and os.stat(stats_path).st_size>0:
        valid_data=True
        case_result=[stats_path.split("/")[-1]]
        latency=[]
        traces_list=[]
        chip_cost=[]
        thermal=[]
        
        with open(log_path,'r') as log_file:
            for line in log_file:
                if re.search(r'Cycles taken:',line):
                    latency.append(int(line.split()[2]))
                    
        if os.path.exists(power_path):
            with open(power_path,'r') as power_file:
                all_lines = power_file.read()
                power_file.close()
                traces_list = processor.findall(all_lines)
        

        if os.path.exists(cost_path):
            file = open(cost_path, "r")
            cost = json.loads(file.read())
            file.close()
            chip_cost=[cost["total_chiplet_area"],cost["total_interposer_area"],cost["total_cost"],cost["chip_total_cost"]]

        if os.path.exists(thermal_path):
            with open(thermal_path, 'r') as file:
                for line in file:
                    max_thermal,avg_thermal = line.split()
                    thermal.append([max_thermal,avg_thermal])

        with open(stats_path, 'r') as file:
            for line in file:
                
                if re.search(r'simTicks', line):
                    simTicks=int(line.split()[1])
                    case_result.append(simTicks)
                if re.search(r'simInsts', line):
                    simInsts=int(line.split()[1])
                    case_result.append(simInsts)
                # if re.search(r'average_flit_latency', line):
                #     average_flit_latency=float(line.split()[1])  
                #     case_result.append(average_flit_latency) 
                # else:
                #     print("No average_flit_latency")
                # if re.search(r'average_packet_latency', line):
                #     average_packet_latency=float(line.split()[1]) 
                #     case_result.append(average_packet_latency)
                # else:
                #     print("No average_flit_latency")
                # if re.search(r'average_hops', line):
                #     average_hops=float(line.split()[1]) 
                #     case_result.append(average_hops)
            if len(latency)!=0:
                case_result.append(sum(latency)/len(latency))
                case_result.append(max(latency))
            else:
                #valid_data=False
                print("No latency")
                case_result.append(0)
                case_result.append(0)
            
            if len(traces_list)!=0:
                case_result.append(traces_list[0][0])
                case_result.append(traces_list[0][1])
            else:
                valid_data=False
                print("No power")
                case_result.append(0)
                case_result.append(0)
            
            if len(chip_cost)!=0:
                case_result.append(chip_cost[0])
                case_result.append(chip_cost[1])
                case_result.append(chip_cost[2])
                case_result.append(chip_cost[3])
            else:
                valid_data=False
                print("No cost")
                case_result.append(0)
                case_result.append(0)
                case_result.append(0)
                case_result.append(0)

            if len(thermal)!=0:
                case_result.append(thermal[0][0])
                case_result.append(thermal[0][1])
            else:
                valid_data=False
                print("No thermal")
                case_result.append(0)
                case_result.append(0)

            if valid_data==True: # all data is stored
                # print(case_result)
                succ_case.append(case_result)
            print(case_result)
            case_result=[]

    #succ_case.sort(key=lambda ele: ele[0])
    csv_file=out_path+"/report.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["path","sim_ticks","sim_insts","a_lat","max_lat","area","peak_power","total_chiplet_area","total_interposer_area","total_cost","chip_total_cost","max_thermal","avg_thermal"]) 
        writer.writerows(succ_case)
    print("------------------REPORT--------------------")
    print(["path","sim_ticks","sim_insts","a_lat","max_lat","area","peak_power","total_chiplet_area","total_interposer_area","total_cost","chip_total_cost","max_thermal","avg_thermal"])
    print(succ_case)

def run_mcpat(configs,report_file):
    

    mcpat_template = configs["mcpat"]["template"] #"template/template_my.xml"
  
    mcpat_root=configs["mcpat"]["path"]

    print("--"*10+"McPAT Modeling"+"--"*10)    
   
    out_path = report_file
        
       
    design_config_path=configs["design_spec"]["path"]
    mcpat_path=os.path.join(out_path,"mcpat")
    stats_path=os.path.join(out_path,"stats.txt")
    config_path=os.path.join(out_path,"config.json")
    hotspot_path=os.path.join(out_path,"hotspot")
    temp_path=os.path.join(mcpat_path,"temp-template.xml")
    macpt_in_path=os.path.join(mcpat_path,"mcpath-in.xml")
    mcpat_out_path=os.path.join(mcpat_path,"mcpat-out.txt")

    if not os.path.exists(mcpat_path):
        os.makedirs(mcpat_path)
    if not os.path.exists(hotspot_path):
        os.makedirs(hotspot_path)

    if os.path.exists(stats_path):
        if os.stat(stats_path).st_size>0: 

            print(f"McPAT Simulation ......")
            
            gem5tomcpat(config_path,stats_path,design_config_path,mcpat_template,temp_path,macpt_in_path)
            cmd_line=mcpat_root+" -infile "+macpt_in_path+" -print_level 5 > "+ mcpat_out_path
            #print(f"Mcpat cmd: {cmd_line}")
            os.system(cmd_line)


   

def split_gird_staedy(grid_steady_file,num_layers,num_rows,num_cols):
    #grid_steady_file = sys.argv[1]
    grid_steady_prefix = grid_steady_file.split('.grid.steady')[0]
    # num_layers = int(sys.argv[2])
    # num_rows = int(sys.argv[3])
    # num_cols = int(sys.argv[4])
    #print(grid_steady_prefix)
    with open(grid_steady_file, "r") as ifp:
      for i in range(num_layers):
        line = ifp.readline()[:-1]
        layer_num = line.split()[1][:-1]

        split_file = f"{grid_steady_prefix}_layer{layer_num}.grid.steady"
        with open(split_file, "w") as ofp:
          for i in range(num_rows * num_cols):
            line = ifp.readline().split()
            ofp.write(f"{line[0]}    {round(float(line[1]), 2)}\n")

def grid_thermal_map(flp_filename,temperatures_filename,rows,cols,output_filename):
  # 添加字体路径
    import matplotlib.font_manager as fm
    font_path = '/data/sxchen/workspace/Arch/gem5/ChipletSim/third-party/Times New Roman.ttf'  # 替换为实际路径
    fm.fontManager.addfont(font_path)

    # 设置字体
    plt.rcParams['font.family'] = 'Times New Roman'

    fig, axs = plt.subplots(1)
    total_width = -np.inf
    total_length = -np.inf
    with open(flp_filename, "r") as fp:
        for line in fp:

            # Ignore blank lines and comments
            if line == "\n" or line[0] == '#':
                continue

            parts = line.split()
            name = parts[0]
            width = float(parts[1])
            length = float(parts[2])
            x = float(parts[3])
            y = float(parts[4])

            rectangle = plt.Rectangle((x, y), width, length, fc="none", ec="black")
            axs.add_patch(rectangle)
            plt.text(x+width/2, y+length/2, name, fontsize=8,  ha='center', va='center', )

            total_width = max(total_width, x + width)
            total_length = max(total_length, y + length)

        temps = []
        with open(temperatures_filename, "r") as fp:
            for line in fp:
                temps.append(float(line.strip().split()[1])-273.15)

        temps = np.reshape(temps, (rows, cols))
            # 创建绿色到红色的颜色映射
        colors = ["green", "yellow", "red"]  # 从绿色到红色
        cmap = LinearSegmentedColormap.from_list("custom_cmap", colors, N=256)

        # 绘制热图
        im = axs.imshow(temps, cmap=cmap, extent=(0, total_width, 0, total_length), vmin=89.5, vmax=93)

        

        #im = axs.imshow(temps, cmap='hot_r', extent=(0, total_width, 0, total_length))


        # if min_temp is None and max_temp is None:
        #   im.set_clim(np.min(temps), np.max(temps))
        # else:
        #   im.set_clim(min_temp, max_temp)

        cbar = fig.colorbar(im, ax=axs)

        axs.set_title(f"Maximum Temperature = {round(np.max(temps),2)} °C")

        axs.set_xticks([n for n in np.linspace(0, total_width, 5)])
        axs.set_xticklabels([round(n*(10**3),2) for n in np.linspace(0, total_width, 5)])
        axs.set_xlabel("Horizontal Position (mm)")

        #axs.xaxis.set_major_formatter(FormatStrFormatter('%.2f'))

        axs.set_yticks([n for n in np.linspace(0, total_length, 5)])
        axs.set_yticklabels([round(n*(10**3),2) for n in np.linspace(0, total_length, 5)])
        axs.set_ylabel("Vertical Position (mm)")
        #axs.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))

        plt.axis('scaled')
        plt.savefig(output_filename)

    return [np.max(temps),np.average(temps)]

def run_hotspot(configs,report_dir):

     # regular expressions for power and area
    re_processor = 'Processor: \n'
    # re_core = 'Core:\n'
    # re_l2 = 'L2\n'
    re_area = r'\s*Area\s*=\s*([0-9.]*)\s*\w*\^\w*\n'
    re_to_leak = r'\s*Peak\s*Power\s*=\s*([0-9.]*)\s*\w*\n'
    re_pe_leak = r'\s*Total\s*Leakage\s*=\s*([0-9.]*)\s*\w*\n'
    re_peak = r'\s*Peak\s*Dynamic\s*=\s*([0-9.]*)\s*\w*\n'
    re_subth = r'\s*Subthreshold\s*Leakage\s*=\s*([0-9.]*)\s*\w*\n'
    re_subth2 = r'\s*Subthreshold\s*Leakage\s*with\s*power\s*gating\s*=\s*([0-9.]*)\s*\w*\n'
    re_gate = r'\s*Gate\s*Leakage\s*=\s*([0-9.]*)\s*\w*\n'
    re_run = r'\s*Runtime\s*Dynamic\s*=\s*([0-9.e-]*)\s*\w*\n'

    processor = re.compile(re_processor+re_area+re_to_leak+re_pe_leak+re_peak+re_subth+re_subth2+re_gate+re_run)

   
    
    hotspot_root=configs["hotspot"]["path"]
    floorplan_root = configs["floorplan"]["path"]

    print("--"*10+"McPAT to HotSpot Coverting"+"--"*10)
   
       
        
    out_path=os.path.join(report_dir)
    stats_path=os.path.join(out_path,"stats.txt")
    power_path=os.path.join(out_path,"mcpat/mcpat-out.txt")
    flp_path=os.path.join(out_path,"hotspot/floorplan.flp")
    blk_path=os.path.join(out_path,"hotspot/hardblock.txt")
    cost_path=os.path.join(out_path,"hotspot/cost_result.json")
    thermal_path=os.path.join(out_path,"hotspot/thermal_layer0.txt")

    if os.path.exists(power_path):
        with open(power_path,'r') as power_file:
            all_lines = power_file.read()
            power_file.close()
            traces_list = processor.findall(all_lines)
        
        ptrace_path=os.path.join(out_path,"mcpat/mcpat-out.ptrace")
            
                
                    # mcpat_to_hotspot(power_path,ptrace_path)
                    #mcpat_to_hotspot(power_path,ptrace_path,flp_path,blk_path)
    print("--"*10+"HotSpot Runing"+"--"*10)

   

    out_path=os.path.join(report_dir)
    hotspot_path=os.path.join(out_path, "hotspot")
    flp_path=hotspot_path+"/floorplan.flp"
    if os.path.exists(flp_path) and os.stat(flp_path).st_size>0:
        materials_path=configs["hotspot"]["materials"]
        example_config_path=configs["hotspot"]["template"]
        mcpat_out_path=hotspot_path+"/mcpat-out.ptrace"
        gcc_steady_path=hotspot_path+"/gcc.steady"
        gcc_grid_steady_path=hotspot_path+"/gcc.grid.steady"
        ttrace_path=hotspot_path+"/gcc.ttrace "
        gcc_grid_ttrace_path=hotspot_path+"/gcc.grid.ttrace"
        hotspot_log=hotspot_path+"/hotspot.log"
        chiplet_desc_path = hotspot_path+"/chiplet.desc"
        average_power_path = hotspot_path+"/chiplet.p"
        
        # if len(traces_list)!=0: # running hotspot floorplan
        #     side_width = mcpat_to_hotspot(power_path,ptrace_path,chiplet_desc_path,average_power_path)
        #     floorplan_cmd=floorplan_root + " -c "+example_config_path+" -f "+chiplet_desc_path + \
        #         " -p "+ average_power_path+ " -o "+flp_path+" -s_sink "+str(side_width*10) +" -s_spreader "+ str(side_width*10) +" >> "+hotspot_log + " 2>&1"
        #     print(floorplan_cmd)
        #     os.system(floorplan_cmd)

       

        cmd_1_line=hotspot_root +" -c "+example_config_path+" -f "+flp_path+" -p "+mcpat_out_path + \
            " -materials_file "+materials_path+" -model_type grid -steady_file "+gcc_steady_path+" -grid_steady_file " +\
                gcc_grid_steady_path+ " > "+hotspot_log + " 2>&1"
        print(cmd_1_line)
        
        cmd_2_line=hotspot_root+"  -c "+example_config_path+" -init_file "+gcc_steady_path+" -f "+flp_path+ \
            " -p "+mcpat_out_path+" -materials_file "+materials_path+" -model_type grid -o "+ttrace_path+ \
                " -grid_transient_file "+gcc_grid_ttrace_path+" >> "+hotspot_log + " 2>&1"
        #print(cmd_2_line)

        os.system(cmd_1_line)
        os.system(cmd_2_line)

        num_layers=configs["hotspot"]["num_layers"]
        num_rows=configs["hotspot"]["num_rows"]
        num_cols=configs["hotspot"]["num_cols"]

        thermal_report=[]
        split_gird_staedy(gcc_grid_steady_path,num_layers,num_rows,num_cols)
        for i in range(num_layers):
            temperatures_filename=hotspot_path+"/gcc_layer"+str(i)+".grid.steady"
            output_filename=hotspot_path+"/result_layer"+str(i)+".pdf"
            thermal_path=hotspot_path+"/thermal_layer"+str(i)+".txt"
            thermal_report=grid_thermal_map(flp_path,temperatures_filename,num_rows, num_cols, output_filename)
            f = open(thermal_path, "w")
            f.write(str(thermal_report[0])+" "+str(thermal_report[1]))
            f.close()
    return  

def run_cost(configs,report_dir):
    cost_template = configs["cost"]["template"] #"template/cost.json"
 
    mcpat_root=configs["mcpat"]["path"]


 


    print("--"*10+"Cost Evaluating"+"--"*10)


    out_path=os.path.join(report_dir)
    hotspot_path=os.path.join(out_path, "hotspot")
    flp_path=hotspot_path+"/floorplan.flp"
    cost_path=hotspot_path+"/cost.json"
    if os.path.exists(flp_path) and os.stat(flp_path).st_size>0:
        cost_evaluate(flp_path,cost_template, cost_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Netlist compare Tool')
    parser.add_argument('-c', '--config',   required=True, default=None)

    args = parser.parse_args()

    config_file = args.config
    with open(config_file, 'r') as model_f:
        configs = json.load(model_f)

    report_dir =  configs["report"]["path"]
    # run_gem5(configs)
    # run_mcpat(configs,report_dir)
    # run_hotspot(configs,report_dir)
    run_cost(configs,report_dir)
    report_csv(report_dir)
