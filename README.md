# AllTalentz Bootcamp 10.0 AquaEstimator 
## Drying Equipment & Line-Item Estimator

This application uses water-damage moisture readings
to create a drying equipment plan (air movers, LGR dehumidifiers, estimated drying
days) and a cost line-item breakdown.




## How it works

1. A user enters details in an editable table: room name, material, square
   footage, moisture reading %, and class of loss.
2. The app applies a rules table (material porosity + class) to size air
   movers and dehumidifiers per room and estimate drying days.
3. It generates a cost line-item table (equipment rental, antimicrobial
   treatment, labor) and a total.


## To Run locally

```
pip install -r requirements.txt
streamlit run app.py
```

local URL for Streamlit:`http://localhost:8501`


## Future plans

- I intend to replace the hardcoded `PRICING` dict and rule tables with lookups against
  a live pricing database (e.g. Azure SQL), so rates and equipment ratios
  stay current without a code change.
- Use the actual IICRC S500 standards for water mitigation and remediation and any company-specific standards.
- Add authentication and tie output from this tool into an existing job/estimate record instead of a standalone tool.
