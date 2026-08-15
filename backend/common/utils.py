def set_attrs(obj,data:dict):
    if data:
        for k,v in data.items():
            setattr(obj,k,v)