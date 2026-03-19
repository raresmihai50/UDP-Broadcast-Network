#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Utilizare: ./startnodes.sh <config_file> <first_node_index> <last_node_index>"
    exit 1
fi

CONFIG_FILE=$1
START_IDX=$2
END_IDX=$3

echo "Pornesc nodurile de la $START_IDX la $END_IDX..."

for (( i=$START_IDX; i<=$END_IDX; i++ ))
do
    python bcastnode.py "$CONFIG_FILE" "$i" &
    echo "Nodul $i pornit in background (PID $!)."
done

echo "Toate nodurile au fost pornite! Asteapta sa-si faca treaba (aprox. 15-20 secunde)."