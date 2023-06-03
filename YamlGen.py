#!/usr/bin/python3

# *********************************************************** #
# *** Author: Ali Foroughi                                    #
# *** Role: DevOPS/SRE Core team                              #
# *** email: ali.foroughi92@gmail.com                         #
#                                                             #
# ******************** DESCRIPTION ************************** #
#                                                             #
# This project creates the YAML configuration files for       #
#  Neon 5G based on a csv file input.                         #
#                                                             #
# *********************************************************** #

import json
import sys
import csv
import os
import re
import argparse
import ips
from ruamel.yaml import YAML

## Help
def parse_arguments():
    # Create the parser
    parser = argparse.ArgumentParser(description='Description of your script.')

    # Add command-line argument for modules
    parser.add_argument('-m', nargs='+', help='The names of modules to create configurations for. Separate multiple modules by space, e.g., -m smf amf')

    # Add positional argument for CSV file
    parser.add_argument('csv_file', help='The path to the CSV file')

    # Parse the command-line arguments
    args = parser.parse_args()

    return args

#variables
templates_dir = 'templates'
modules = ["mme", "hss","pcrf","smf","amf","pcf","udr","udm","ausf","nrf","nssf","bsf","scp","upf","sgwc","sgwu"]
log_dir = "/root/zcore/install/var/log/open5gs/"


global_env = {}
with open('global_variables.txt') as file:
    for line in file:
        line = line.strip()
        if line and '=' in line:
            key, value = line.split('=', 1)
            global_env[key] = value

MCC = global_env['MCC']
MNC = global_env['MNC']
MAX_UE = global_env['MAX_UE']
MAX_PEER = global_env['MAX_PEER']
MONGO_IP = global_env['MONGO_CONNECTION_STRING']
MCC = int(MCC)
MNC = int(MNC)
MAX_UE = int(MAX_UE)
MAX_PEER = int(MAX_PEER)


# Get the CSV file name from the command-line argument
csv_file = sys.argv[1]

# Convert the CSV file to lowercase and save it to /tmp
csv_file_lower = os.path.join('/tmp', csv_file)
with open(csv_file, 'r') as file:
    with open(csv_file_lower, 'w') as output_file:
        for line in file:
            output_file.write(line.lower())

### Functions ### 

def create_directories(module_name):
    os.makedirs("input_files/"+module_name)

def input_output_dir (module_name):
    if module_name in modules:
        output_dir = "output_files/"+ module_name
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        return output_dir
    else:
        raise ValueError("Invalid module specified: " + module_name)

def print_logs (module_name):
    print(" \u29D7 generating "+ module_name +" configuration files.")
    
def check_string_in_file(file_path, target_string):
    with open(file_path, 'r') as file:
        for line in file:
            if target_string in line:
                extracted = line.split("=")[1].strip()
                return extracted

def search_json_keys(json_obj, value):
    keys = []
    def search(json_obj, value, parent_key=''):
        if isinstance(json_obj, dict):
            for k, v in json_obj.items():
                search(v, value, parent_key + k + '.')
        elif isinstance(json_obj, list):
            for idx, item in enumerate(json_obj):
                search(item, value, parent_key + str(idx) + '.')
        else:
            if json_obj == value:
                keys.append(parent_key[:-1])
    search(json_obj, value)
    return keys

def process_row(row):
    (
        AMF_NAME, AMF_SBI, AMF_NGAP, AMF_METRICS,
        SMF_NAME, SMF_SBI, SMF_PFCP, SMF_GTPC, SMF_GTPU, SMF_METRICS, SMF_SUBNET,
        NRF_NAME, NRF_SBI, UDM_NAME, UDM_SBI,
        AUSF_NAME, AUSF_SBI, PCF_NAME, PCF_SBI, UDR_NAME, UDR_SBI,
        NSSF_NAME, NSSF_SBI, NSSF_NSI,
        BSF_NAME, BSF_SBI, SCP_NAME, SCP_SBI,
        UPF_NAME, UPF_PFCP, UPF_GTPU, UPF_SUBNET
    ) = row

    with open(csv_file_lower, 'r') as file:
        csv_reader = csv.reader(file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            process_row(row)
        return process_row


#############################   4G modules  #############################

def mme_hss_generate():
    print_logs("MME")

    output_directory = input_output_dir("mme")  # Create the output directory

    with open(csv_file_lower, 'r') as file:
        csv_reader = csv.reader(file, delimiter=',')
        for row in csv_reader:
            VM_name, OM_IP, MME_IP, S11_IP, DB_IP, TAC = row

            MME_NAME = re.search(r'srv[0-9]+-mme-[0-9]+', VM_name).group()
            S1AP_IP = MME_IP
            GTPC_IP = S11_IP
            MME_CODE = int(''.join([x for x in re.findall(r'\d+', MME_NAME)]))
            TAC_VAL = TAC.replace(',', '-')
            tac_numbers = list(map(int, TAC_VAL.split("-")))    # Create a list of all TAC numbers to support multiple TACs. 

            with open("templates/mme.json") as json_template:   # Open the template json file and iterate through it.
                json_data = json.load(json_template)

            json_data['mme']['s1ap'][0]['addr'] =  S1AP_IP
            json_data['mme']['gtpc'][0]['addr'] = GTPC_IP
            json_data['mme']['s10'][0]['addr'] = S1AP_IP
            #json_data['mme']['gummei']['mme_gid'] = MME_CODE
            json_data['mme']['gummei']['mme_code'] = MME_CODE
            json_data['mme']['tai']['tac'] = tac_numbers
            json_data['mme']['mme_name'] = MME_NAME
            
            my_tac = tac_numbers    # TAC value of this MME instance
            my_s10_ip = S1AP_IP     # Find the S10 IP of this instance
            my_tac = tac_numbers    # Handle multiple TACS for one MME
            s10_gtpc = []

            for tac in ips.tac_list:
            # Retrieve the primary and secondary IP addresses
                primary = ips.tac_map[tac]["primary"]
                secondary = ips.tac_map[tac]["secondary"]

            # Add the data to the list
                s10_gtpc.append({"addr": primary, "tac": int(tac)})
                s10_gtpc.append({"addr": secondary, "tac": int(tac)})

            json_data["s10"]["gtpc"] = s10_gtpc

            #Removing MME's own IP and TAC from the s10 list
            s10_list = json_data["s10"]["gtpc"]
            remove_index = None
            for i, item in enumerate(s10_list):
                for j, tac in enumerate(tac_numbers):
                    if item["tac"] == tac and item["addr"] == my_s10_ip:
                        remove_index = i
                        if remove_index is not None:
                            s10_list.pop(remove_index)
                        break
        
            yaml_file = os.path.join(output_directory, MME_NAME+'.yaml')
            yaml = YAML()
            yaml.indent(mapping=4, sequence=4, offset=2)
            with open(yaml_file, "w") as f:
                yaml.dump(json_data, f)
        
     
    ########  create the HSS files ##### 
    print_logs("HSS")

    output_directory = input_output_dir("hss")  # Create the output directory

    with open("templates/hss.json") as json_template:
        json_data = json.load(json_template)

        # Uncomment these and make changes if needed. 
        #json_data['logger']['file'] = check_string_in_file(input_file, "logger.file")
        #son_data['hss']['freeDiameter'] = check_string_in_file(input_file, "hss.freeDiameter")
        #json_data['db_uri'] = check_string_in_file(input_file, "db_uri")
                
        yaml_file = os.path.join(output_directory, MME_NAME+'.yaml')
        yaml = YAML()
        yaml.indent(mapping=4, sequence=4, offset=2)
        with open(yaml_file, "w") as f:
            yaml.dump(json_data, f)


##########################   5G modules   ##########################

def amf_generate ():
    print_logs("AMF")

    output_directory = input_output_dir("amf") # Create the output directory

    with open(csv_file_lower, 'r') as file:
        csv_reader = csv.reader(file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            
            #read all the rows from the CSV file
            AMF_NAME,AMF_SBI,AMF_NGAP,AMF_METRICS,SMF_NAME,SMF_SBI,SMF_PFCP,SMF_GTPC,SMF_GTPU,SMF_METRICS,SMF_SUBNET,NRF_NAME,NRF_SBI,UDM_NAME,UDM_SBI,AUSF_NAME,AUSF_SBI,PCF_NAME,PCF_SBI,UDR_NAME,UDR_SBI,NSSF_NAME,NSSF_SBI,NSSF_NSI,BSF_NAME,BSF_SBI,SCP_NAME,SCP_SBI,UPF_NAME,UPF_PFCP,UPF_GTPU,UPF_SUBNET = row
            
            with open("templates/amf.json") as json_template:
                json_data = json.load(json_template)

            #Edit the json template and insert our own values read from the CSV file   
            json_data['logger']['file']=  log_dir + AMF_NAME + '.log'
            json_data['amf']['sbi'][0]['addr'] =  AMF_SBI
            json_data['amf']['ngap'][0]['addr'] =  AMF_NGAP
            json_data['amf']['metrics'][0]['addr'] =  AMF_METRICS
            json_data['amf']['guami'][0]['plmn_id']['mcc'] =  MCC
            json_data['amf']['guami'][0]['plmn_id']['mnc'] =  MNC
            json_data['amf']['tai'][0]['plmn_id']['mcc'] =  MCC
            json_data['amf']['tai'][0]['plmn_id']['mnc'] =  MNC
            json_data['amf']['plmn_support'][0]['plmn_id']['mcc'] =  MCC
            json_data['amf']['plmn_support'][0]['plmn_id']['mnc'] =  MNC
            json_data['amf']['amf_name'] = AMF_NAME
            json_data['scp']['sbi'][0]['addr'] =  SCP_SBI

            #create YAML file based on the modified JSON
            yaml_file = os.path.join(output_directory, AMF_NAME+'.yaml')
            yaml = YAML()
            yaml.indent(mapping=4, sequence=4, offset=2)
            with open(yaml_file, "w") as f:
                yaml.dump(json_data, f)

def smf_generate ():
    print_logs("SMF")

    output_directory = input_output_dir("smf") # Create the output directory

    with open(csv_file_lower, 'r') as file:
        csv_reader = csv.reader(file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            
            #read all the rows from the CSV file
            AMF_NAME,AMF_SBI,AMF_NGAP,AMF_METRICS,SMF_NAME,SMF_SBI,SMF_PFCP,SMF_GTPC,SMF_GTPU,SMF_METRICS,SMF_SUBNET,NRF_NAME,NRF_SBI,UDM_NAME,UDM_SBI,AUSF_NAME,AUSF_SBI,PCF_NAME,PCF_SBI,UDR_NAME,UDR_SBI,NSSF_NAME,NSSF_SBI,NSSF_NSI,BSF_NAME,BSF_SBI,SCP_NAME,SCP_SBI,UPF_NAME,UPF_PFCP,UPF_GTPU,UPF_SUBNET = row
            
            with open("templates/smf.json") as json_template:
                json_data = json.load(json_template)

            #Edit the json template and insert our own values read from the CSV file
            json_data['logger']['file']=  log_dir + SMF_NAME + '.log'
            json_data['smf']['sbi'][0]['addr'] =  SMF_SBI
            json_data['smf']['pfcp'][0]['addr'] =  SMF_PFCP
            json_data['smf']['gtpc'][0]['addr'] =  SMF_GTPC
            json_data['smf']['gtpu'][0]['addr'] =  SMF_GTPU
            json_data['smf']['metrics'][0]['addr'] =  SMF_METRICS
            json_data['smf']['subnet'][0]['addr'] =  SMF_SUBNET
            json_data['scp']['sbi'][0]['addr'] =  SCP_SBI
            json_data['upf']['pfcp'][0]['addr'] =  UPF_PFCP

            #create YAML file based on the modified JSON
            yaml_file = os.path.join(output_directory, SMF_NAME+'.yaml')
            yaml = YAML()
            yaml.indent(mapping=4, sequence=4, offset=2)
            with open(yaml_file, "w") as f:
                yaml.dump(json_data, f)

def nrf_generate ():
    print_logs("NRF")

    output_directory = input_output_dir("nrf") # Create the output directory

    with open(csv_file_lower, 'r') as file:
        csv_reader = csv.reader(file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            
            #read all the rows from the CSV file
            AMF_NAME,AMF_SBI,AMF_NGAP,AMF_METRICS,SMF_NAME,SMF_SBI,SMF_PFCP,SMF_GTPC,SMF_GTPU,SMF_METRICS,SMF_SUBNET,NRF_NAME,NRF_SBI,UDM_NAME,UDM_SBI,AUSF_NAME,AUSF_SBI,PCF_NAME,PCF_SBI,UDR_NAME,UDR_SBI,NSSF_NAME,NSSF_SBI,NSSF_NSI,BSF_NAME,BSF_SBI,SCP_NAME,SCP_SBI,UPF_NAME,UPF_PFCP,UPF_GTPU,UPF_SUBNET = row
            
            with open("templates/nrf.json") as json_template:
                json_data = json.load(json_template)

            #Edit the json template and insert our own values read from the CSV file
            json_data['logger']['file']=  log_dir + NRF_NAME + '.log' 
            json_data['nrf']['sbi'][0]['addr'] =  NRF_SBI
            json_data['scp']['sbi'][0]['addr'] =  SCP_SBI
            json_data['max']['ue'] =  MAX_UE
            json_data['max']['peer'] =  MAX_PEER

            #create YAML file based on the modified JSON
            yaml_file = os.path.join(output_directory, NRF_NAME+'.yaml')
            yaml = YAML()
            yaml.indent(mapping=4, sequence=4, offset=2)
            with open(yaml_file, "w") as f:
                yaml.dump(json_data, f)

def udm_generate ():
    print_logs("UDM")

    output_directory = input_output_dir("udm") # Create the output directory

    with open(csv_file_lower, 'r') as file:
        csv_reader = csv.reader(file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            
            #read all the rows from the CSV file
            AMF_NAME,AMF_SBI,AMF_NGAP,AMF_METRICS,SMF_NAME,SMF_SBI,SMF_PFCP,SMF_GTPC,SMF_GTPU,SMF_METRICS,SMF_SUBNET,NRF_NAME,NRF_SBI,UDM_NAME,UDM_SBI,AUSF_NAME,AUSF_SBI,PCF_NAME,PCF_SBI,UDR_NAME,UDR_SBI,NSSF_NAME,NSSF_SBI,NSSF_NSI,BSF_NAME,BSF_SBI,SCP_NAME,SCP_SBI,UPF_NAME,UPF_PFCP,UPF_GTPU,UPF_SUBNET = row
            
            with open("templates/udm.json") as json_template:
                json_data = json.load(json_template)

            #Edit the json template and insert our own values read from the CSV file   
            json_data['logger']['file']=  log_dir + UDM_NAME + '.log'
            json_data['udm']['sbi'][0]['addr'] =  UDM_SBI
            json_data['scp']['sbi'][0]['addr'] =  SCP_SBI
            json_data['max']['ue'] =  MAX_UE
            json_data['max']['peer'] =  MAX_PEER

            #create YAML file based on the modified JSON
            yaml_file = os.path.join(output_directory, UDM_NAME+'.yaml')
            yaml = YAML()
            yaml.indent(mapping=4, sequence=4, offset=2)
            with open(yaml_file, "w") as f:
                yaml.dump(json_data, f)


def ausf_generate ():
    print_logs("AUSF")

    output_directory = input_output_dir("ausf") # Create the output directory

    with open(csv_file_lower, 'r') as file:
        csv_reader = csv.reader(file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            
            #read all the rows from the CSV file
            AMF_NAME,AMF_SBI,AMF_NGAP,AMF_METRICS,SMF_NAME,SMF_SBI,SMF_PFCP,SMF_GTPC,SMF_GTPU,SMF_METRICS,SMF_SUBNET,NRF_NAME,NRF_SBI,UDM_NAME,UDM_SBI,AUSF_NAME,AUSF_SBI,PCF_NAME,PCF_SBI,UDR_NAME,UDR_SBI,NSSF_NAME,NSSF_SBI,NSSF_NSI,BSF_NAME,BSF_SBI,SCP_NAME,SCP_SBI,UPF_NAME,UPF_PFCP,UPF_GTPU,UPF_SUBNET = row
            
            with open("templates/ausf.json") as json_template:
                json_data = json.load(json_template)

            #Edit the json template and insert our own values read from the CSV file   
            json_data['logger']['file']=  log_dir + AUSF_NAME + '.log'
            json_data['ausf']['sbi'][0]['addr'] =  AUSF_SBI
            json_data['scp']['sbi'][0]['addr'] =  SCP_SBI
            #json_data['max']['ue'] =  MAX_UE
            #json_data['max']['peer'] =  MAX_PEER

            #create YAML file based on the modified JSON
            yaml_file = os.path.join(output_directory, AUSF_NAME+'.yaml')
            yaml = YAML()
            yaml.indent(mapping=4, sequence=4, offset=2)
            with open(yaml_file, "w") as f:
                yaml.dump(json_data, f)



def pcf_generate ():
    print_logs("PCF")

    output_directory = input_output_dir("pcf") # Create the output directory

    with open(csv_file_lower, 'r') as file:
        csv_reader = csv.reader(file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            
            #read all the rows from the CSV file
            AMF_NAME,AMF_SBI,AMF_NGAP,AMF_METRICS,SMF_NAME,SMF_SBI,SMF_PFCP,SMF_GTPC,SMF_GTPU,SMF_METRICS,SMF_SUBNET,NRF_NAME,NRF_SBI,UDM_NAME,UDM_SBI,AUSF_NAME,AUSF_SBI,PCF_NAME,PCF_SBI,UDR_NAME,UDR_SBI,NSSF_NAME,NSSF_SBI,NSSF_NSI,BSF_NAME,BSF_SBI,SCP_NAME,SCP_SBI,UPF_NAME,UPF_PFCP,UPF_GTPU,UPF_SUBNET = row
            
            with open("templates/pcf.json") as json_template:
                json_data = json.load(json_template)

            #Edit the json template and insert our own values read from the CSV file   
            json_data['logger']['file']=  log_dir + PCF_NAME + '.log'
            json_data['pcf']['sbi'][0]['addr'] =  PCF_SBI
            json_data['scp']['sbi'][0]['addr'] =  SCP_SBI
            json_data['max']['ue'] =  MAX_UE
            json_data['max']['peer'] =  MAX_PEER
            json_data['db_uri'] =  MONGO_IP

            #create YAML file based on the modified JSON
            yaml_file = os.path.join(output_directory, PCF_NAME+'.yaml')
            yaml = YAML()
            yaml.indent(mapping=4, sequence=4, offset=2)
            with open(yaml_file, "w") as f:
                yaml.dump(json_data, f)


def udr_generate ():
    print_logs("UDR")

    output_directory = input_output_dir("udr") # Create the output directory

    with open(csv_file_lower, 'r') as file:
        csv_reader = csv.reader(file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            
            #read all the rows from the CSV file
            AMF_NAME,AMF_SBI,AMF_NGAP,AMF_METRICS,SMF_NAME,SMF_SBI,SMF_PFCP,SMF_GTPC,SMF_GTPU,SMF_METRICS,SMF_SUBNET,NRF_NAME,NRF_SBI,UDM_NAME,UDM_SBI,AUSF_NAME,AUSF_SBI,PCF_NAME,PCF_SBI,UDR_NAME,UDR_SBI,NSSF_NAME,NSSF_SBI,NSSF_NSI,BSF_NAME,BSF_SBI,SCP_NAME,SCP_SBI,UPF_NAME,UPF_PFCP,UPF_GTPU,UPF_SUBNET = row
            
            with open("templates/udr.json") as json_template:
                json_data = json.load(json_template)

            #Edit the json template and insert our own values read from the CSV file   
            json_data['logger']['file']=  log_dir + UDR_NAME + '.log'
            json_data['udr']['sbi'][0]['addr'] =  UDR_SBI
            json_data['scp']['sbi'][0]['addr'] =  SCP_SBI
            json_data['max']['ue'] =  MAX_UE
            json_data['max']['peer'] =  MAX_PEER
            json_data['db_uri'] =  MONGO_IP

            #create YAML file based on the modified JSON
            yaml_file = os.path.join(output_directory, UDR_NAME+'.yaml')
            yaml = YAML()
            yaml.indent(mapping=4, sequence=4, offset=2)
            with open(yaml_file, "w") as f:
                yaml.dump(json_data, f)

def nssf_generate ():
    print_logs("NSSF")

    output_directory = input_output_dir("nssf") # Create the output directory

    with open(csv_file_lower, 'r') as file:
        csv_reader = csv.reader(file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            
            #read all the rows from the CSV file
            AMF_NAME,AMF_SBI,AMF_NGAP,AMF_METRICS,SMF_NAME,SMF_SBI,SMF_PFCP,SMF_GTPC,SMF_GTPU,SMF_METRICS,SMF_SUBNET,NRF_NAME,NRF_SBI,UDM_NAME,UDM_SBI,AUSF_NAME,AUSF_SBI,PCF_NAME,PCF_SBI,UDR_NAME,UDR_SBI,NSSF_NAME,NSSF_SBI,NSSF_NSI,BSF_NAME,BSF_SBI,SCP_NAME,SCP_SBI,UPF_NAME,UPF_PFCP,UPF_GTPU,UPF_SUBNET = row
            
            with open("templates/nssf.json") as json_template:
                json_data = json.load(json_template)

            #Edit the json template and insert our own values read from the CSV file   
            json_data['logger']['file']=  log_dir + NSSF_NAME + '.log'
            json_data['nssf']['sbi'][0]['addr'] =  NSSF_SBI
            json_data['nssf']['nsi'][0]['addr'] =  NSSF_NSI
            json_data['scp']['sbi'][0]['addr'] =  SCP_SBI
            json_data['max']['ue'] =  MAX_UE
            json_data['max']['peer'] =  MAX_PEER

            #create YAML file based on the modified JSON
            yaml_file = os.path.join(output_directory, NSSF_NAME+'.yaml')
            yaml = YAML()
            yaml.indent(mapping=4, sequence=4, offset=2)
            with open(yaml_file, "w") as f:
                yaml.dump(json_data, f)

def bsf_generate ():
    print_logs("BSF")

    output_directory = input_output_dir("bsf") # Create the output directory

    with open(csv_file_lower, 'r') as file:
        csv_reader = csv.reader(file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            
            #read all the rows from the CSV file
            AMF_NAME,AMF_SBI,AMF_NGAP,AMF_METRICS,SMF_NAME,SMF_SBI,SMF_PFCP,SMF_GTPC,SMF_GTPU,SMF_METRICS,SMF_SUBNET,NRF_NAME,NRF_SBI,UDM_NAME,UDM_SBI,AUSF_NAME,AUSF_SBI,PCF_NAME,PCF_SBI,UDR_NAME,UDR_SBI,NSSF_NAME,NSSF_SBI,NSSF_NSI,BSF_NAME,BSF_SBI,SCP_NAME,SCP_SBI,UPF_NAME,UPF_PFCP,UPF_GTPU,UPF_SUBNET = row
            
            with open("templates/bsf.json") as json_template:
                json_data = json.load(json_template)

            #Edit the json template and insert our own values read from the CSV file   
            json_data['logger']['file']=  log_dir + BSF_NAME + '.log'
            json_data['bsf']['sbi'][0]['addr'] =  BSF_SBI
            json_data['scp']['sbi'][0]['addr'] =  SCP_SBI
            #json_data['max']['ue'] =  MAX_UE
            #json_data['max']['peer'] =  MAX_PEER
            json_data['db_uri'] =  MONGO_IP

            #create YAML file based on the modified JSON
            yaml_file = os.path.join(output_directory, BSF_NAME+'.yaml')
            yaml = YAML()
            yaml.indent(mapping=4, sequence=4, offset=2)
            with open(yaml_file, "w") as f:
                yaml.dump(json_data, f)


def scp_generate ():
    print_logs("SCP")

    output_directory = input_output_dir("scp") # Create the output directory

    with open(csv_file_lower, 'r') as file:
        csv_reader = csv.reader(file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            
            #read all the rows from the CSV file
            AMF_NAME,AMF_SBI,AMF_NGAP,AMF_METRICS,SMF_NAME,SMF_SBI,SMF_PFCP,SMF_GTPC,SMF_GTPU,SMF_METRICS,SMF_SUBNET,NRF_NAME,NRF_SBI,UDM_NAME,UDM_SBI,AUSF_NAME,AUSF_SBI,PCF_NAME,PCF_SBI,UDR_NAME,UDR_SBI,NSSF_NAME,NSSF_SBI,NSSF_NSI,BSF_NAME,BSF_SBI,SCP_NAME,SCP_SBI,UPF_NAME,UPF_PFCP,UPF_GTPU,UPF_SUBNET = row
            
            with open("templates/scp.json") as json_template:
                json_data = json.load(json_template)

            #Edit the json template and insert our own values read from the CSV file   
            json_data['logger']['file']=  log_dir + SCP_NAME + '.log'
            json_data['scp']['sbi'][0]['addr'] =  SCP_SBI
            json_data['nrf']['sbi'][0]['addr'] =  NRF_SBI
            #json_data['max']['ue'] =  MAX_UE
            #json_data['max']['peer'] =  MAX_PEER
            json_data['db_uri'] =  MONGO_IP

            #create YAML file based on the modified JSON
            yaml_file = os.path.join(output_directory, SCP_NAME+'.yaml')
            yaml = YAML()
            yaml.indent(mapping=4, sequence=4, offset=2)
            with open(yaml_file, "w") as f:
                yaml.dump(json_data, f)

def upf_generate ():
    print_logs("UPF")

    output_directory = input_output_dir("upf") # Create the output directory

    with open(csv_file_lower, 'r') as file:
        csv_reader = csv.reader(file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            
            #read all the rows from the CSV file
            AMF_NAME,AMF_SBI,AMF_NGAP,AMF_METRICS,SMF_NAME,SMF_SBI,SMF_PFCP,SMF_GTPC,SMF_GTPU,SMF_METRICS,SMF_SUBNET,NRF_NAME,NRF_SBI,UDM_NAME,UDM_SBI,AUSF_NAME,AUSF_SBI,PCF_NAME,PCF_SBI,UDR_NAME,UDR_SBI,NSSF_NAME,NSSF_SBI,NSSF_NSI,BSF_NAME,BSF_SBI,SCP_NAME,SCP_SBI,UPF_NAME,UPF_PFCP,UPF_GTPU,UPF_SUBNET = row
            
            with open("templates/upf.json") as json_template:
                json_data = json.load(json_template)

            #Edit the json template and insert our own values read from the CSV file   
            json_data['logger']['file']=  log_dir + UPF_NAME + '.log'
            json_data['upf']['pfcp'][0]['addr'] =  UPF_PFCP
            json_data['upf']['gtpu'][0]['addr'] =  UPF_GTPU
            json_data['upf']['subnet'][0]['addr'] =  UPF_SUBNET
            json_data['smf']['pfcp']['addr'] =  SMF_PFCP
            #json_data['max']['ue'] =  MAX_UE
            #json_data['max']['peer'] =  MAX_PEER

            #create YAML file based on the modified JSON
            yaml_file = os.path.join(output_directory, UPF_NAME+'.yaml')
            yaml = YAML()
            yaml.indent(mapping=4, sequence=4, offset=2)
            with open(yaml_file, "w") as f:
                yaml.dump(json_data, f)


def main():
    # Parse the command-line arguments
    args = parse_arguments()

    # Access the values of the command-line arguments
    modules = args.m

    if modules:
        module_functions = {
            "smf": smf_generate,
            "amf": amf_generate,
            "nrf": nrf_generate,
            "udm": udm_generate,
            "ausf": ausf_generate,
            "pcf": pcf_generate,
            "udr": udr_generate,
            "nssf": nssf_generate,
            "bsf": bsf_generate,
            "scp": scp_generate,
            "upf": upf_generate
        }

        # Check each module name and call the corresponding function
        for module in modules:
            if module in module_functions:
                module_functions[module]()
            else:
                print(f"Unknown module: {module}")
    else:
        # Run other function or logic if modules are not specified
        print("No modules specified.")

if __name__ == '__main__':
    main()



amf_generate()
smf_generate()
nrf_generate()
udm_generate()
ausf_generate()
pcf_generate()
udr_generate()
nssf_generate()
bsf_generate()
scp_generate()
upf_generate()

print ("DONE \u2713")
print ("YAML files generated and saved to output_files directory.")
