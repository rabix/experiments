
def sbg_schema2json_schema(sbg):

    def wrap_in_array(schema):
        return {"type": "array", "items": schema}

    MAPPINGS = {"name": "title",
                "description": "description",
                "default": "default"
               }

    TYPES = {"integer": "integer",
             "float": "number",
             "string": "string",
             "boolean": "boolean",
             "struct": "object",
             "file": {"$ref": "http://rabix.org/file.json"}
            }

    TYPE_MAPPINGS = {"integer": {
                        "min": "minimum",
                        "max": "maximum"
                     },
                     "float": {"min": "minimum",
                                "max": "maximum"
                               },
                     "string": {"pattern": "pattern"}
                   }

    def convert_elem(elem):
        js_param = {}
        sbg_type = elem["type"]
        if sbg_type in TYPES:
            js_param["type"] = TYPES[sbg_type]
        elif sbg_type == "enum":
            js_param["enum"] = elem["values"]
        else:
            raise RuntimeError("Unknown type: " + sbg_type)

        for sbg_k, js_k in MAPPINGS.items():
            if sbg_k in elem:
                js_param[js_k] = elem[sbg_k]

        if sbg_type in TYPE_MAPPINGS:
            for sbg_k, js_k in TYPE_MAPPINGS[sbg_type].items():
                if sbg_k in elem:
                    js_param[js_k] = elem[sbg_k]

        if elem["list"]:
            js_param = wrap_in_array(js_param)

        return js_param


    json = {"$schema": "http://json-schema.org/schema#",
            "inputs": {
                "type": "object",
                "properties": {},
                "required": []
            }
           }

    js_inputs = json["inputs"]["properties"]

    for inp in sbg["inputs"]:
        inp2 = dict(inp)
        inp2["type"] = "file"

        if inp["required"]:
            json["inputs"]["required"].append(inp["id"])

        js_inputs[inp["id"]] = convert_elem(inp2)



    for param in sbg["params"]:
        if inp["required"]:
            json["inputs"]["required"].append(param["id"])

        js_inputs[param["id"]] = convert_elem(param)

    return json


def sbg_job2cliche_job(doc):
    pass



def cliche_job2sbg_job(doc):
    sbg_job = {"$$type": "job",
               "wrapper_id": doc["app"],
               "args": {
                "$inputs": {},
                "$params": {}
               }
              }
    sbg_resources = {"$$type": "resources"}
    allocated_resources = doc["allocatedResources"]

    sbg_resources["high_io"] = allocated_resources["network"]
    sbg_resources["cpu"] = allocated_resources["cpu"]
    sbg_resources["mem_mb"] = allocated_resources["mem"]

    sbg_job["resources"] = sbg_resources

    for k, v in doc["inputs"].items():
        if isinstance(v, dict) and "path" in v:
            sbg_job["args"]["$inputs"][k] = v["path"]
        else:
            sbg_job["args"]["$params"][k] = v

    return sbg_job


if __name__ == "__main__":
    from os.path import join, dirname
    import json
    import yaml
    import jsonschema
    bwa = json.load(open("/home/luka/devel/rabix/rabix/tests/apps/BwaMem.json"))
    bwa_schm = sbg_schema2json_schema(bwa["schema"])
    print(json.dumps(bwa_schm, indent=2))
    jsonschema.Draft4Validator.check_schema(bwa_schm)

    job_path = join(dirname(__file__), "../examples/bwa-mem.yml")
    job = yaml.load(open(job_path))
    print(json.dumps(cliche_job2sbg_job(job["job"]), indent=2))

