#!/bin/bash

# Loop 20 times
for i in {1..20}; do
  # Base state
  curl -X GET "http://localhost:5000/api/set_all?signal=GGGGGGGGGGGGGGGG"
  
  # First modification
  curl -X GET "http://localhost:5000/api/set_all?signal=CGGGGGGGGGGGGGGG"
  
  # Second modification
  curl -X GET "http://localhost:5000/api/set_all?signal=GGCGGGGGGGGGGGGG"
  
  # Rest for 2 seconds
  sleep 2
done
