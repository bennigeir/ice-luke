local base = import "lib/base.libsonnet";
local model = import "lib/transformers_model_luke.jsonnet";


base + {
    "dataset_reader": base["dataset_reader"] + {"use_entity_feature": true},
    "model": model
}