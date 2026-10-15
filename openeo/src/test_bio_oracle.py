import pyo_oracle as pyo

pyo.list_local_data()

# 1. List available layers (filter by search term, variable, scenario, depth, ...)
# layers = pyo.list_layers()
# print(layers)
# layers.to_csv("data/output/bio_oracle/test.csv")

# query a specific layer
info = pyo.info_layer("tas_baseline_2000_2020_depthsurf")
print(info)

# 3. Build constraints from friendly bounds (no hand-written dicts)
constraints = pyo.build_constraints(
    "thetao_baseline_2000_2019_depthsurf",
    time=("2000-01-01T00:00:00Z", "2010-01-01T00:00:00Z"),
    latitude=(0, 10),
    longitude=(0, 10),
)

df = pyo.load_layer(
    "thetao_baseline_2000_2019_depthsurf",
    constraints=constraints,
    variables=["thetao_mean"],
)

print(df)
