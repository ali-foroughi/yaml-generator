#!/usr/bin/python3

# *********************************************************** #
# *** Author: Ali Foroughi                                    #
# *** email: ali.foroughi92@gmail.com                         #
#                                                             #
# ******************** DESCRIPTION ************************** #
#   This script generates YAML file based on values           #
#   defined in a text input file. It takes the values from    #
#   the text file, replaces them in the sample.json file      #
#   and creates a yaml configurtion file.                     #
#    As of now it supports MME and HSS moudles.               #
# *********************************************************** #

import json
import csv
import os
import re
import ips
from ruamel.yaml import YAML

input_dir_mme = "input_files/mme"
output_dir_mme = "output_files/mme"

input_dir_hss = "input_files/hss"
output_dir_hss = "output_files/hss"

#Create output directory
if not os.path.exists(output_dir_mme):
    os.makedirs(output_dir_mme)

if not os.path.exists(output_dir_hss):
    os.makedirs(output_dir_hss)
    
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

def ip_to_remove (wtr):
    for key in wtr:
        match = re.search(r"s10.gtpc.(\d+).addr", key)
        if match:
            number = match.group(1)
            number = int(number)
            print(number)
            return number

# Create MME files
for filename in os.listdir(input_dir_mme):
    input_file = os.path.join(input_dir_mme, filename)
    print (input_file)

    #Open the JSON file containing the sample configuration
    with open("templates/mme.json") as input:
        json_data = json.load(input)

    #Find the tac number to use for deletation
    tac_numbers = check_string_in_file(input_file, "mme.tai.tac")
    #print (tac_numbers)
    tac_numbers = list(map(int, tac_numbers.split(",")))
    #print (tac_numbers)
    tac_numbers_str = str(tac_numbers).replace("'", "").replace("[", "[").replace("]", "]")
    #print (tac_numbers_str)
    #print (tac_numbers)
    
    #Make adjusments based on the input file
    json_data['logger']['file'] = check_string_in_file(input_file, "logger.file")
    json_data['mme']['freeDiameter'] = check_string_in_file(input_file, "mme.freeDiameter")
    json_data['mme']['s1ap'][0]['addr'] = check_string_in_file(input_file, "mme.s1ap")
    json_data['mme']['gtpc'][0]['addr'] = check_string_in_file(input_file, "mme.gtpc")
    json_data['mme']['s10'][0]['addr'] = check_string_in_file(input_file, "mme.s10")
    json_data['mme']['gummei']['mme_gid'] = int(check_string_in_file(input_file, "mme.gummei.mme_gid"))
    json_data['mme']['gummei']['mme_code'] = int(check_string_in_file(input_file, "mme.gummei.mme_code"))
    #json_data['mme']['tai']['tac'] = str(tac_numbers)
    json_data['mme']['tai']['tac'] = tac_numbers
    json_data['mme']['network_name']['full'] = check_string_in_file(input_file, "mme.network_name.full")
    json_data['mme']['mme_name'] = check_string_in_file(input_file, "mme.mme_name")
    json_data['mme']['mgmt_response_path'] = check_string_in_file(input_file, "mme.mgmt_response_path")
    json_data['mme']['mgmt_request_path'] = check_string_in_file(input_file, "mgmt_request_path")
    json_data['sgwc']['gtpc'][0]['addr'] = check_string_in_file(input_file, "sgwc.gtpc")
    json_data['smf']['gtpc'][0]['addr'] = check_string_in_file(input_file, "smf.gtpc")
    json_data['max']['ue'] = int(check_string_in_file(input_file, "max.ue"))

    my_tac = check_string_in_file(input_file, "mme.tai.tac")
    #print (my_tac)
    my_s10_ip = check_string_in_file(input_file, "mme.s10")
    my_tac = list(map(int, my_tac.split(",")))
    #my_tac = list(map(int, my_tac[1:-1].split(',')))
    #print (my_tac)
    
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
    #print (s10_list)
    remove_index = None
    for i, item in enumerate(s10_list):
        for j, tac in enumerate(tac_numbers):
            if item["tac"] == tac and item["addr"] == my_s10_ip:
                #print (item)
                remove_index = i
                #print (remove_index)
                if remove_index is not None:
                    s10_list.pop(remove_index)
                break
    
    yaml_file = os.path.join(output_dir_mme, filename.replace('.txt', '.yaml'))

    #create YAML file based on the modified JSON
    yaml = YAML()
    yaml.indent(mapping=4, sequence=4, offset=2)
    with open(yaml_file, "w") as f:
        yaml.dump(json_data, f)


# Create HSS files
for filename in os.listdir(input_dir_hss):
    input_file = os.path.join(input_dir_hss, filename)
    print (input_file)

    #Open the JSON file containing the sample configuration
    with open("templates/hss.json") as input:
        json_data = json.load(input)

    #Make adjusments based on the input file
    json_data['logger']['file'] = check_string_in_file(input_file, "logger.file")
    json_data['hss']['freeDiameter'] = check_string_in_file(input_file, "hss.freeDiameter")
    json_data['db_uri'] = check_string_in_file(input_file, "db_uri")

    #create YAML file based on the modified JSON
    yaml_file = os.path.join(output_dir_hss, filename.replace('.txt', '.yaml'))
    yaml = YAML()
    yaml.indent(mapping=4, sequence=4, offset=2)
    with open(yaml_file, "w") as f:
        yaml.dump(json_data, f)

print ("************")
print ("YAML files generated and saved to output_files directory.")
print ("************")
