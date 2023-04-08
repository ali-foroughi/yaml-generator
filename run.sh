#!/bin/bash

csv_file="$1"

rm -rf input_files/* 2> /dev/null
mkdir -p input_files/mme/ 2> /dev/null
mkdir -p input_files/hss/ 2> /dev/null

tr '[:upper:]' '[:lower:]' < $csv_file > /tmp/$csv_file

while IFS="," read -r VM_name OM_IP MME_IP S11_IP DB_IP TAC
do

  MME_NAME=$(echo $VM_name | grep -oE "srv[0-9]+-mme-[0-9]+")
  S1AP_IP=$(echo $MME_IP)
  GTPC_IP=$(echo $S11_IP)
  MME_CODE=$(echo $MME_NAME | grep -oE "[0-9]+" | tr -d '\n' | awk '{print $1}')
  TAC_VAL=$(echo $TAC | tr - ,)

  cp templates/mme_input_sample.txt input_files/mme/$MME_NAME.txt

  sed -i 's/S1AP_IP/'$S1AP_IP'/g' input_files/mme/$MME_NAME.txt
  sed -i 's/GTPC_IP/'$GTPC_IP'/g' input_files/mme/$MME_NAME.txt
  sed -i 's/S10_IP/'$S1AP_IP'/g' input_files/mme/$MME_NAME.txt
  sed -i 's/MME_CODE/'$MME_CODE'/g' input_files/mme/$MME_NAME.txt
  sed -i 's/TAC_VAL/'$TAC_VAL'/g' input_files/mme/$MME_NAME.txt
  sed -i 's/MME_NAME/'$MME_NAME'/g' input_files/mme/$MME_NAME.txt

  cp templates/hss_input_sample.txt input_files/hss/$MME_NAME.txt
  
done < /tmp/$csv_file

rm -rf output_files/ 2> /dev/null
./yaml_gen.py
rm -rf input_files/ 2> /dev/null
rm /tmp/$csv_file
rm -rf __pycache__ 2> /dev/null