
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


    json = {"inputs": {
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



def clice_job2sbg_job(doc):
  pass


if __name__ == "__main__":
    import json
    bwa = json.load(open("/home/luka/devel/rabix/rabix/tests/apps/BwaMem.json"))
    print(json.dumps(sbg_schema2json_schema(bwa["schema"]), indent=4))
