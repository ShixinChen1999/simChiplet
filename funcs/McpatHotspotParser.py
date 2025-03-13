import re
import sys
import random
import math
# from Floorplan import init_floorplan

class Block:
	def __init__(self, name, index, c_type, area, power):
		self.name = name
		self.index = index
		self.type = c_type
		self.area = area
		self.power = power
		self.width = None
		self.height = None
		self.left = None
		self.bottom = None
		self.min_ratio = 1
		self.max_ratio = 2 
		self.rotate = 1
        

	def center(self):
		return (self.left + self.width / 2, self.bottom + self.height / 2)



def init_floorplan(blocks,max_width):
    # Sort blocks by area (width * height) in descending order
    blocks.sort(key=lambda block: block.width * block.height, reverse=True)
    
    # Initialize coordinates
    x, y = 0, 0
    max_height_in_row = 0
    
    # Place each block
    for block in blocks:
        # Check if the block fits in the current row
        if x + block.width > max_width:
            # Start a new row
            x = 0
            y += max_height_in_row
            max_height_in_row = 0
        
        # Set the position for the block
        block.left = x
        block.bottom = y
        
        # Update the position for the next block
        x += block.width
        max_height_in_row = max(max_height_in_row, block.height)

    # Return the updated list of blocks with their positions
    return blocks

def distance_between_centers(block1, block2):
    center1 = block1.center()
    center2 = block2.center()
    return math.sqrt((center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2)

def calculate_distances(blocks):
    distances = {}
    for i in range(len(blocks)):
        for j in range(i + 1, len(blocks)):
            distance = distance_between_centers(blocks[i], blocks[j])
            distances[(blocks[i].name, blocks[j].name)] = distance
    return distances

#regular expressions
ncores = re.compile(r'Total Cores: (\d+) cores')
nl2s = re.compile(r'Total L2s: (\d+)')

re_core = r'Core:\n'
re_l2 = r'L2\n'
re_area = r'\s*Area\s*=\s*([0-9.]*)\s*\w*\^\w*\n'
re_peak = r'\s*Peak\s*Dynamic\s*=\s*([0-9.]*)\s*\w*\n'
re_subth = r'\s*Subthreshold\s*Leakage\s*=\s*([0-9.]*)\s*\w*\n'
re_subth2 = r'\s*Subthreshold\s*Leakage\s*with\s*power\s*gating\s*=\s*([0-9.]*)\s*\w*\n'
re_gate = r'\s*Gate\s*Leakage\s*=\s*([0-9.]*)\s*\w*\n'
# re_run = '\s*Runtime\s*Dynamic\s*=\s*([0-9.]*)\s*\w*\n'
re_run = r'\s*Runtime\s*Dynamic\s*=\s*([0-9.e-]*)\s*\w*\n'


core = re.compile(re_core+re_area+re_peak+re_subth+re_subth2+re_gate+re_run)
l2 = re.compile(re_l2+re_area+re_peak+re_subth+re_subth2+re_gate+re_run)


#READ ALL LINES OF FILE
def get_lines_of_file(fin):
	all_lines = fin.read()
	fin.close()
	return all_lines

#GET NUMBER OF ELEMENTS BASED ON DE "elem" re object.
#elem = regular expression object for number of elements (core, l2, etc...)
#all_lines = the file
def get_number_of_elems(elem, all_lines):
	m = elem.search(all_lines)
	if m:
		return int(m.group(1))
	else:
		return 1

#GET LIST OF POWER TRACES. THE LIST CONTAINS LISTS OF POWER TRACES FOR ALL ELEMENTS OF THE SAME TYPE (ex: core0, core1, ..., coren)
#elem = regular expression object for attributes of element "elem"
def get_power_traces(elem, all_lines):
	p_traces = []
	traces_list = elem.findall(all_lines)
	# print("number=",len(traces_list))
	number_of_elems=len(traces_list)
	for n in range(0,number_of_elems):
		p_traces.append([])
	
	#print(traces_list)
	for i in range(0,len(traces_list)):
		p_traces[i%number_of_elems].append(traces_list[i][5])# Dynamic Power is 5th
	return p_traces

def get_area_traces(elem, number_of_elems, all_lines):
	area_traces = []
	for n in range(0,number_of_elems):
		area_traces.append([])
	traces_list = elem.findall(all_lines)
	#print(traces_list)
	for i in range(0,len(traces_list)):
		area_traces[i%number_of_elems].append(traces_list[i][0])# Area is the  first element
	return area_traces


#WRITE HEADER TO PTRACE FILE (ONLY CORES AND L2S FOR NOW)
def write_header_ptrace(fout,number_of_cores,number_of_l2s):
	#WRITE CORES HEADERS
	for i in range(0,number_of_cores):
		fout.write('Core_'+str(i)+'\t')
	#WRITE L2s HEADERS
	for i in range(0,number_of_l2s):
		fout.write('L2_'+str(i)+'\t')
	#WRITE NEW LINE
	fout.write('\n')

#WRITE POWER TRACES TO PTRACE FILE (ONLY CORES AND L2S FOR NOW)
def write_traces_ptrace(fout,number_of_traces,p_traces_cores,p_traces_l2s):
	for i in range(0,number_of_traces):
		#write cores traces
		for j in range(0,len(p_traces_cores)):
			fout.write(p_traces_cores[j][i] + '\t')
		#write l2s traces
		for j in range(0,len(p_traces_l2s)):
			fout.write(p_traces_l2s[j][i] + '\t')	
		fout.write('\n')

#n_increase = number of times that the traces will be increased
def artificial_sim_increase(p_traces,number_of_traces,n_increase):
	for i in range(0,n_increase):
		for j in range(0,len(p_traces)):
			last_trace = p_traces[j][-1]
			# print("last_trace=",last_trace)
			#increase traces
			for k in range(0,number_of_traces):
				p_traces[j].append(str(float(p_traces[j][k])+float(last_trace)))




def initial_flp(flp_path,area_traces_cores,area_traces_l2s,blk_path):

	flp_file = open(flp_path,'w')
	blk_file = open(blk_path,'w')
	area_file = open(blk_path.replace("hardblock.txt", "chiplet.area"),'w')

	#change area from mm^2 to m^2
	RelaxRatio=1.2
	
	blocks=[]
	allArea=0
	for i in range(0,len(area_traces_cores[0])):# core first
		for j in range(0, len(area_traces_cores)):
			allArea += float(area_traces_cores[j][i])
	
	for i in range(0,len(area_traces_l2s[0])):# core first
		for j in range(0, len(area_traces_l2s)):
			allArea += float(area_traces_l2s[j][i])


	allArea = allArea*RelaxRatio
	
	

	for i in range(0,len(area_traces_cores[0])):# core first
		for j in range(0, len(area_traces_cores)):
			# 
			name = 'Core_' + str(j)+'\t'
			# print("area_traces_cores[j][i]=",area_traces_cores[j][i])
			# print("ratio=",ratio)
			ratio = random.uniform(0.9, 1.1) #height/width  
			height = ratio * math.sqrt(float(area_traces_cores[j][i]))
			width = float(area_traces_cores[j][i])/height
			blocks.append(Block(name,height,width))
			#left = random.uniform(0, 1)*math.sqrt(allArea)
			#bottom = random.uniform(0, 1)*math.sqrt(allArea)
			# flp_out.write(name +'\t'+str(width*0.001)+'\t'+str(height*0.001)+'\t'+str(left*0.001)+'\t'+str(bottom*0.001)+'\n' )


	for i in range(0,len(area_traces_l2s[0])):# core first
		for j in range(0, len(area_traces_l2s)):
			
			name = 'L2_' + str(j)+'\t'
			ratio = random.uniform(0.9, 1.1) #height/width  
			height = ratio * math.sqrt(float(area_traces_l2s[j][i]))
			width = float(area_traces_l2s[j][i])/height
			blocks.append(Block(name,height,width))
			#left = random.uniform(0, 1)*math.sqrt(allArea)
			#bottom = random.uniform(0, 1)*math.sqrt(allArea)
			# flp_out.write(name +'\t'+str(width*0.001)+'\t'+str(height*0.001)+'\t'+str(left*0.001)+'\t'+str(bottom*0.001)+'\n')
 
	
	max_width=math.sqrt(allArea)

	blocks=init_floorplan(blocks, max_width)# floorplan method

	for i in range(0,len(blocks)):
		flp_file.write(blocks[i].name +'\t'+str(round(blocks[i].width*0.001,6))+'\t'+str(round(blocks[i].height*0.001,6))+'\t'+str(round(blocks[i].left*0.001,6))+'\t'+str(round(blocks[i].bottom*0.001,6))+'\n')
	
	for i in range(0,len(blocks)):	
		blk_file.write("n"+str(i)+" hardrectilinear "+str(int(blocks[i].width*1000)) +" "+str(int(blocks[i].height*1000)) +" "+ str(blocks[i].name)+"\n") 
	
	for i in range(0,len(blocks)):	
		area_file.write(blocks[i].name +'\t'+str(round(blocks[i].area*0.000001, 6))+'\n') 
	

	flp_file.close()
	blk_file.close()

	distances = calculate_distances(blocks)
	
	latency_f = open(blk_path+"-distance",'w')
	latency_f.write("Distance:\n")

	for block_pair, distance in distances.items():
		latency_f.write(f"{block_pair[0]} to {block_pair[1]}: {distance}\n")

		# for j in range(0,len(area_traces_cores)):
		# 	flp_out.write(area_traces_cores[j][i] + '\t')
		# #write l2s traces
		# for j in range(0,len(area_traces_l2s)):
		# 	flp_out.write(area_traces_l2s[j][i] + '\t')	
		# flp_out.write('\n')
	latency_f.close()

	
def generate_desc(chiplet_desc_path, average_power_path, blocks):
	core_num=0
	l2_num = 0
	for block in blocks:
		if block.type=='core':
			core_num+=1
		if block.type=='l2':
			l2_num+=1
	

	match_ratio = core_num/l2_num

	with open(chiplet_desc_path, 'w') as file: 
		for block in blocks:
			#[block.name,block.power, block.min_ratio, block.max_ratio]
			new_line = ' '.join(list(map(str,[block.name,block.area, block.min_ratio, block.max_ratio, block.rotate])))
			file.write(new_line+"\n")

		for i in range(len(blocks)):
			for j in range(i+1, len(blocks)):
				# if blocks[i].type== 'core' and blocks[j].type=='core':
				# 	new_line = ' '.join([blocks[i].name, blocks[j].name, '1'])
				# 	file.write(new_line+"\n")
				if blocks[i].type== 'core' and blocks[j].type == 'l2':
					if abs(blocks[i].index-match_ratio*blocks[j].index) <= 1:
						new_line = ' '.join([blocks[i].name, blocks[j].name, '2'])
						file.write(new_line+"\n")
			

	with open(average_power_path, 'w') as file:
		for block in blocks:
			new_line = ' '.join(list(map(str,[block.name, block.power])))
			file.write(new_line+"\n")
	return
		
def mcpat_to_hotspot(power_path,ptrace_path,chiplet_desc_path,average_power_path):

	power_file=open(power_path,'r')
	all_lines=get_lines_of_file(power_file)
		
	number_of_cores = len(core.findall(all_lines))
	number_of_l2s = len(l2.findall(all_lines))

	# print(number_of_cores,number_of_l2s)
	# exit()
	p_traces_cores = get_power_traces(core,all_lines)
	p_traces_l2s = get_power_traces(l2,all_lines)
	
	area_traces_cores = get_area_traces(core,number_of_cores,all_lines)
	area_traces_l2s = get_area_traces(l2,number_of_l2s,all_lines)

	# print(len(p_traces_cores))
	# print(len((p_traces_l2s)))
	# print(p_traces_cores)
	# print(p_traces_l2s)
	# artificial_sim_increase(p_traces_cores,len(p_traces_cores[0]),1)
	# artificial_sim_increase(p_traces_l2s,len(p_traces_l2s[0]),1)

	ptrace_file=open(ptrace_path,'w')

	#GET NUMBER OF TRACES
	number_of_traces = len(p_traces_cores[0])

	#WRITE HEADER TO PTRACE FILE
	write_header_ptrace(ptrace_file,number_of_cores,number_of_l2s)

	#WRITE POWER TRACES
	write_traces_ptrace(ptrace_file,number_of_traces,p_traces_cores,p_traces_l2s)

	ptrace_file.close()

	#init floorplan
	
	# print(area_traces_cores)
	# print(area_traces_l2s)
	blocks = []
	
	for i in range(0,len(area_traces_cores[0])):# core first
		for j in range(0, len(area_traces_cores)):
			name = 'Core_' + str(j)+'\t'
			blocks.append(Block(name,j,'core', float(area_traces_cores[j][i])/(10 ** 6),float(p_traces_cores[j][i])))
	

	for i in range(0,len(area_traces_l2s[0])):# core first
		for j in range(0, len(area_traces_l2s)):
			name = 'L2_' + str(j)+'\t'
			blocks.append(Block(name, j, 'l2',float(area_traces_l2s[j][i])/(10 ** 6),float(p_traces_l2s[j][i])))
	
	ratio = 1.2
	allArea = 0
	for block in blocks:
		print(block.area)
		allArea += block.area
	print(allArea)
	side_width =  ratio * math.sqrt(allArea)
	
	generate_desc(chiplet_desc_path, average_power_path, blocks)
	return side_width

	# initial_flp(flp_path,area_traces_cores,arae_traces_l2s,blk_path)
	



