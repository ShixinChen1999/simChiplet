
import sys
import random

def extract_traffic_distribution_lines(file_path,net_path,block_path):
    
    name=[]
    with open(block_path,"r") as blk_f:
        for line in blk_f:
            elements = line.split()
            name.append(elements[4])
    
    chiplet_num=len(name)
    frequency=[]
    temp_frequency=[]
    # Open the file for reading
    with open(file_path, 'r') as file:
        for line in file:
            # Check if the line contains "traffic_distribution"
            if 'ctrl_traffic_distribution' in line:
                # Split the line by whitespace
                elements = line.split()
                if len(elements) >= 3:
                    connection=[]
                    chiplet1=int(elements[0].split(".")[-2][1:])
                    chiplet2=int(elements[0].split(".")[-1][1:])
                    inter_frequency = int(elements[1])
                    if chiplet2>chiplet1 and chiplet1<chiplet_num and chiplet2<chiplet_num:
                        temp_frequency.append([chiplet1,chiplet2,inter_frequency])

                else:
                    print(f"Line does not have enough elements: {line.strip()}")



    
    

    
    net = open(net_path, 'w')
    net_num=chiplet_num*(chiplet_num-1)/2

    sorted_frequency = sorted(temp_frequency, key=lambda x: (x[0],x[1]))

    with open(file_path, 'r') as file:
        for line in file:
            # Check if the line contains "traffic_distribution"
            if 'data_traffic_distribution' in line:
                # Split the line by whitespace
                elements = line.split()
                if len(elements) >= 3:
                    connection=[]
                    chiplet1=int(elements[0].split(".")[-2][1:])
                    chiplet2=int(elements[0].split(".")[-1][1:])
                    inter_frequency = int(elements[1])
                    for pair in sorted_frequency:
                        if [chiplet1,chiplet2]==(pair[0:2]):
                            pair[2]=pair[2]+inter_frequency

                else:
                    print(f"Line does not have enough elements: {line.strip()}")


   



    # fre_file = open(net_path+"freq","w")
    net.write("NumNets : %d\n"% net_num)
    for frequency in sorted_frequency:
        if frequency[0]<chiplet_num and (frequency[1]>frequency[0]):
            #fre_file.write("Chiplet%d and Chiplet%d frequency=%d\n"%(frequency[0],frequency[1],frequency[2]))
            net.write("NetDegree : 2 %d 1\n" %frequency[2])
            net.write("%s\n"%name[frequency[0]])
            net.write("%s\n"%name[frequency[1]])
    #fre_file.close


    # sorted_frequency=sorted_frequency[:int(net_num)]

    # random.shuffle(sorted_frequency)
    
    

    # for i in range(chiplet_num):
    #     for j in range(i+1,chiplet_num):
    #         net.write("NetDegree : 2 %d 1\n" %sorted_frequency[0][2])
    #         net.write("Chiplet%d\n"%i)
    #         net.write("Chiplet%d\n"%j)
    #         sorted_frequency=sorted_frequency[1:]

    net.close()


# Example usage
file_path =  sys.argv[1] # Replace with the actual path to your file
net_path = sys.argv[2]
block_path = sys.argv[3]


extract_traffic_distribution_lines(file_path,net_path,block_path)
