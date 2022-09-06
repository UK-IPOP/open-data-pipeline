TODO:

- [ ] Add comments
- [ ] Add documentation (README and docs site)
  - The latter will be necesarry once we move to dockerfiles and actions
- [ ] Figure out Milwaukee data
- [ ] Add drug-extraction step
- [ ] Add geocoding step (when lat/long not provided)] --> use method to identify when geocoding is needed (i.e. when lat/long is null in datasets that have lat/long or just when there is no lat/long in the dataset but there is address data)
- [ ] Pin versions used of all software
- [ ] Use arcgis package for geocoding
- [ ] Use Socrata package (register API key) for data fetching from datasets published on Socrata
- [ ] Use github package to keep config.yaml updated


pretty sure we can use this query:
https://lio.milwaukeecountywi.gov/arcgis/rest/services/MedicalExaminer/PublicDataAccess/MapServer/1/query?f=json&where=1=1&outFields=*&orderByFields=DeathDate%20desc

going forward to get the 1000 (or less) most recent records by death date and then check for existing from there... but will have to batch pull in first

I think, if my math is right, we can do ~20 minutes / day of actions... (2,000 minutes per month limit for free)