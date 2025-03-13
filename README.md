# ChipletSim: A Simulation Framework for Chiplet-based Architecture

____

## Building Toolchains

### Construct the Environment
Create new conda enviroment to make the installation successfully.

    conda create -n simChiplet python=3.8
    conda activate simChiplet
    conda install scons

**Note**: using `pip` to install `scons` may cause complilation bug :report no python installation



### Install GEM5 that support RISCV and X86      
Install Gem5 in the root path of the repo

    git clone https://gem5.googlesource.com/public/gem5
    git tag
    git checkout v22.1.0.0
    #X86 ISA is more stable
    scons build/X86/gem5.opt PROTOCOL=MESI_Two_Level -j`nproc`
    scons build/RISCV/gem5.opt PROTOCOL=MESI_Two_Level -j`nproc`
    


### Install RISCV compilation toolchain (Only for RISCV support)
    git --recursive clone  https://github.com/riscv/riscv-gnu-toolchain #may take a long time
    cd riscv-gnu-toolchain
    mkdir build
    cd build
    ../configure --prefix=/path/to/install # change the path to install
    make linux -j`nproc` && make install # wait to install submodule and compilation


### Complie the workloads:

## For matrix multiplication test
    cd workload

change the RISCV-Toolchain path in Makefile 
    # in Makefile Need specify in your environment
    RISCV_GCC_COMPILER=RISCV-Toolchain/bin/riscv64-unknown-linux-gnu-gcc 
make:

    mkdir matmul
    make x86 -j4
## For NPB benchmark
    cd workload/NPB-OMP
    make [APP] CLASS=[OPTIONS]

[APP] = cg, ep,ft,is,mg [OPTIONS]= S,A,B,C 


_____
## Run the Simulation

### Specify the simulation:
change the archietcture parameetr in arch.json
    
make sure your path in the sim-config.json is correct

    python sim.py -c sim-config.json

The evalaution results of simulation will stored in report.csv file
    path,sim_ticks,sim_insts,a_lat,max_lat,area,peak_power,total_chiplet_area,total_interposer_area,total_cost,chip_total_cost,max_thermal,avg_thermal
stats.txt,1159261000,3877396,118450.4,118468,350.918,254.456,348.319233,442.703835,10.740,6.221,45.700000000000045,45.504780273437525


    
