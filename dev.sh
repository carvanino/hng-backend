#!/bin/bash

concurrently \
  --kill-others-on-fail \
  --names "STAGE-0,STAGE-1,STAGE-2,STAGE-3,GATEWAY" \
  -c "cyan,magenta,yellow,blue,green" \
  "npm run start:stage-0" \
  "npm run start:stage-1" \
  "npm run start:stage-2" \
  "npm run start:stage-3" \
  "npm start"
