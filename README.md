TODO:

- [ ] Add comments
- [ ] Add documentation (README and docs site)
  - The latter will be necesarry once we move to dockerfiles and actions
- [ ] Figure out Milwaukee data
- [ ] Add drug-extraction step
- [ ] Add geocoding step (when lat/long not provided)]
- [ ] Pin versions used of all software


pretty sure we can use this query:
https://lio.milwaukeecountywi.gov/arcgis/rest/services/MedicalExaminer/PublicDataAccess/MapServer/1/query?f=json&where=1=1&outFields=*&orderByFields=DeathDate%20desc

going forward to get the 1000 (or less) most recent records by death date and then check for existing from there... but will have to batch pull in firstmkd