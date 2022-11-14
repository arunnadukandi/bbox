#See LICENSE.iitm for license details
'''

Author   : Santhosh Pavan
Email id : santhosha@mindgrovetech.in
Details  : This file consists cocotb testbench for bbox dut

--------------------------------------------------------------------------------------------------
'''
'''
TODO:
Task Description: Add list of instructions in Testfactory block. So that testbench generates tests for listed instructions. One instruction is implemented as an example. 
		  For multiple instructions, provided as comment (see after TestFactory(TB)). Please the use the same format.
                  Note - Comments are provided for TestFactory.
		  Note - The value of instr (ANDN) is a temp value, it needed to be changed according to spec.

Note - Here testbench assumes below verilog port names are generated by bluespec compiler. Please implement the bluespec design with below port names.

 DUT Ports:
 Name                         I/O  size 
 bbox_out                       O    65/33
 CLK                            I     1 
 RST_N                          I     1 
 instr                          I    32
 rs1                            I    64/32
 rs2                            I    64/32
   (instr, rs1, rs2) -> bbox_out
'''


import string
import random
import cocotb
import logging as _log
from cocotb.decorators import coroutine
from cocotb.triggers import Timer, RisingEdge, FallingEdge
from cocotb.binary import BinaryValue
from cocotb.clock import Clock
from cocotb.regression import TestFactory

from bbox_ref_model import bbox_rm


specs = {'addn'  : 0b01000000000000000111000000110011,
         'orn'   : 0b01000000000000000110000000110011,
         'xnor'  : 0b01000000000000000100000000110011,
        'cpop'   : 0b01100000001000000001000000010011,
        'cpopw'  : 0b01100000001000000001000000011011,
        'clz'    : 0b01100000000000000001000000010011,
        'clzw'   : 0b01100000000000000001000000011011,
        'ctz'    : 0b01100000000100000001000000010011,
        'ctzw'   : 0b01100000000100000001000000011011,
        'max'    : 0b00001010000000000110000000110011,
        'maxu'   : 0b00001010000000000111000000110011,
        'min'    : 0b00001010000000000100000000110011,
        'minu'   : 0b00001010000000000101000000110011
    
}


#generates clock and reset
async def initial_setup(dut):
	cocotb.start_soon(Clock(dut.CLK, 1, units='ns').start())
        
	dut.RST_N.value = 0
	await RisingEdge(dut.CLK)
	dut.RST_N.value = 1


#drives input data to dut
async def input_driver(dut, instr, rs1, rs2, single_opd):
    await RisingEdge(dut.CLK)
    dut.instr.value = instr
    dut.rs1.value = rs1
    dut._log.info("---------------- DUT Input Info -----------------------")
    if single_opd == 1:
        await RisingEdge(dut.CLK)
        dut._log.info("instr = %s  rs1 = %s ",hex(dut.instr.value), hex(dut.rs1.value))

    else :
        dut.rs2.value = rs2
        await RisingEdge(dut.CLK)
        dut._log.info("instr = %s  rs1 = %s rs2 = %s",hex(dut.instr.value), hex(dut.rs1.value), hex(dut.rs2.value))
    dut._log.info("-------------------------------------------------------")

#monitors dut output
async def output_monitor(dut):
    while True:
        await RisingEdge(dut.CLK)
        if(dut.bbox_out.value[0]): 
            break

    dut_result = dut.bbox_out.value
    return dut_result

#compares output of dut and rm
async def scoreboard(dut, dut_result, rm_result):
    dut._log.info("------------ Compare DUT o/p & Ref Model o/p ----------")
    dut._log.info("Expected output  = %s", rm_result)
    dut._log.info("DUT output       = %s", dut_result)
    assert rm_result == str(dut_result),"Failed"
    dut._log.info("-------------------------------------------------------")

#Testbench
async def TB(dut, XLEN, instr, instr_name, single_opd, num_of_tests):
    await initial_setup(dut)
    dut._log.info("*******************************************************")
    dut._log.info("------------- Test %r of RV%d starts --------------" %(instr_name,XLEN))
    dut._log.info("*******************************************************")
    for i in range (num_of_tests):
        rs1 = random.randint(0,(2**XLEN)-1) 
        rs2 = random.randint(0,(2**XLEN)-1)
        # rs1 = 10
        # rs2 = 5
        rm_result = bbox_rm(instr, rs1, rs2, XLEN)
    
        await input_driver(dut, instr, rs1, rs2, single_opd)
        dut_result = await output_monitor(dut)
    
        await scoreboard(dut, dut_result, rm_result)	
    dut._log.info("*******************************************************")
    dut._log.info("------------- Test %r of RV%d ends ----------------" %(instr_name,XLEN))
    dut._log.info("*******************************************************")


# generates sets of tests based on the different permutations of the possible arguments to the test function
tf = TestFactory(TB)

base = 'RV64'
#To run tests for RV32, change base = 'RV32'

#generates tests for instructions of RV32
if base == 'RV32':

    # tf.add_option('XLEN', [32])
    # tf.add_option(('instr','instr_name','single_opd'), [(1, 'addn', 0)])
    #if instruction has single operand, provide single_opd = 1 (please see below line).
    ##To run multiple instr - tf.add_option(((('instr','instr_name','single_opd'), [(1, 'addn', 0),(2,'clz',1),(...)])
    tf.add_option('XLEN', [32])
    tf.add_option('num_of_tests',[1])
    i = 0
    if(0):
        for keys in specs:
            
            encoding = str(specs.get(keys))      # storing the value of keys in string form
            int_encoding = specs.get(keys)       # storing the value of keys 
            # chcking if encoding belongs to zbb - logic with negate
            print(encoding[2:9])
            if(encoding[2:9] == '0100000'):   
                
                if(encoding[17:20] == '111'):   # slicing to get the 12-14 bits as per encoding 
                    tf.add_option(('instr','instr_name','single_opd'), [(int(int_encoding),'addn_32',0)]) # pass andn fvalues
                    tf.generate_tests(postfix=i) # Text string to append to end of test_function name when naming generated test cases
                            
                elif(encoding[17:20] == '110'):
                    tf.add_option(('instr','instr_name','single_opd'), [(int(int_encoding),'orn',0)])   # pass orn values
                    tf.generate_tests(postfix=i)
            
                elif(encoding[17:20] == '100'):
                    tf.add_option(('instr','instr_name','single_opd'), [(3,'xnor',0)])   # pass xnor values
                    tf.generate_tests(postfix=i)
            
            # Checking encoding for zbb - count population and counting leading/laggin zeros

            elif(encoding[:7] == '0110000'):
                if(encoding[25:32] == '0010011' and encoding[7:12] == '00010'):   # checking for CPOP OP code
                    tf.add_option(('instr','instr_name','single_opd'), [(4, 'cpop', 1)])   
                    tf.generate_tests(postfix=i)
                
                # elif(encoding[25:32] == '0011011'):  # Checking for CPOPW OP code
                #     tf.add_option(('instr','instr_name','single_opd'), [(5, 'cpopw', 1)])   
                #     tf.generate_tests(postfix=i)

                elif(encoding[7:12] == '00000'):
                    tf.add_option(('instr','instr_name','single_opd'), [(6, 'clz', 1)])   
                    tf.generate_tests(postfix=i)

            
              
            i+=1

#generates tests for instructions of RV64
elif base == 'RV64':
    tf.add_option('XLEN', [64])
    tf.add_option('num_of_tests',[1])
    i = 0
    if(1):
        for keys in specs:
            
            #encoding = bin(specs.get(keys))      # storing the value of keys in string form
            encoding = format(specs.get(keys),'032b')  # converting the int value to bin keeping the leading zeros
            
            int_encoding = specs.get(keys)       # storing the value of keys
            
            # chcking if encoding belongs to zbb - logic with negate
            
            if(encoding[:7] == '0100000'):   
                
                if(encoding[17:20] == '111'):   # slicing to get the 12-14 bits as per encoding 
                    tf.add_option(('instr','instr_name','single_opd'), [(int(int_encoding),'addn',0)]) # pass andn fvalues
                    tf.generate_tests(postfix=i) # Text string to append to end of test_function name when naming generated test cases
                            
                elif(encoding[17:20] == '110'):
                    tf.add_option(('instr','instr_name','single_opd'), [(int(int_encoding),'orn',0)])   # pass orn values
                    tf.generate_tests(postfix=i)
            
                elif(encoding[17:20] == '100'):
                    tf.add_option(('instr','instr_name','single_opd'), [(int(int_encoding),'xnor',0)])   # pass xnor values
                    tf.generate_tests(postfix=i)
            
            # Checking encoding for zbb - count population
            
            elif(encoding[:7] == '0110000'):
                # print(encoding[:7])
                if(encoding[25:32] == '0010011' and encoding[7:12] == '00010'):   # checking for CPOP OP code
                    tf.add_option(('instr','instr_name','single_opd'), [(int(int_encoding), 'cpop', 1)])   
                    tf.generate_tests(postfix=i)
                
                elif(encoding[7:12] == '00010' and encoding[25:32] == '0011011'):  # Checking for CPOPW OP code
                    tf.add_option(('instr','instr_name','single_opd'), [(int(int_encoding), 'cpopw', 1)])   
                    tf.generate_tests(postfix=i)

                elif(encoding[7:12] == '00000' and encoding[25:32] == '0010011'): # clz OP code
                    tf.add_option(('instr','instr_name','single_opd'), [(int(int_encoding), 'clz', 1)])   
                    tf.generate_tests(postfix=i)

                elif(encoding[7:12] == '00000' and encoding[25:32] == '0011011'): # clzw OP code
                    tf.add_option(('instr','instr_name','single_opd'), [(int(int_encoding), 'clzw', 1)])   
                    tf.generate_tests(postfix=i)
                
                elif(encoding[7:12] == '00001' and encoding[17:20] == '001' and encoding[25:32] == '0010011'):  # ctz OP code
                    tf.add_option(('instr','instr_name','single_opd'), [(int(int_encoding), 'ctz', 1)])   
                    tf.generate_tests(postfix=i)

                # ctzw OP code
                elif(encoding[7:12] == '00001' and encoding[17:20] == '001' and encoding[25:32] == '0011011'):
                    tf.add_option(('instr','instr_name','single_opd'), [(int(int_encoding), 'ctzw', 1)])   
                    tf.generate_tests(postfix=i)    

            # Checking encoding for zbb - max/min for Signed and Unsigned integers

            # checking for signed max/maxU/min and minU OP code
            elif(encoding[:7] == '0000101'):
                # max of signed numbers
                if(encoding[17:20] == '110' and encoding[25:32] == '0110011'):  
                    tf.add_option(('instr','instr_name','single_opd'), [(int(int_encoding), 'max', 0)])   
                    tf.generate_tests(postfix=i)

                # max of unsigned numbers
                elif(encoding[17:20] == '111' and encoding[25:32] == '0110011'):  
                    tf.add_option(('instr','instr_name','single_opd'), [(int(int_encoding), 'maxU', 0)])   
                    tf.generate_tests(postfix=i)
                
                # min of signed numbers
                if(encoding[17:20] == '100' and encoding[25:32] == '0110011'):  
                    tf.add_option(('instr','instr_name','single_opd'), [(int(int_encoding), 'min', 0)])   
                    tf.generate_tests(postfix=i)

                # min of unsigned numbers
                elif(encoding[17:20] == '101' and encoding[25:32] == '0110011'):  
                    tf.add_option(('instr','instr_name','single_opd'), [(int(int_encoding), 'minU', 0)])   
                    tf.generate_tests(postfix=i)

            i+=1







    #tf.add_option(('instr','instr_name','single_opd'),[(1,'andn',0),(2, 'orn', 0),(3, 'xnor', 0)])
    #if instruction has single operand, provide single_opd = 1 (please see below line).
    ##To run multiple instr - tf.add_option(((('instr','instr_name','single_opd'), [(1, 'addn', 0),(2,'clz',1),(...)])

#for each instruction below line generates 10 test vectors, can change to different no.


