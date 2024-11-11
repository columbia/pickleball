import torch
from gliner import GLiNER

#model = GLiNER.from_pretrained("EmergentMethods/gliner_medium_news-v2.1")
#model = GLiNER.from_pretrained("/data/no-malicious/gliner/GliNER/DeepMount00-GLiNER_ITA_BASE",
model = GLiNER.from_pretrained("test", local_files_only=True)

text = """
The Chihuahua State Public Security Secretariat (SSPE) arrested 35-year-old Salomón C. T. in Ciudad Juárez, found in possession of a stolen vehicle, a white GMC Yukon, which was reported stolen in the city's streets. The arrest was made by intelligence and police analysis personnel during an investigation in the border city. The arrest is related to a previous detention on February 6, which involved armed men in a private vehicle. The detainee and the vehicle were turned over to the Chihuahua State Attorney General's Office for further investigation into the case.
"""

labels = ["person", "location", "date", "event", "facility", "vehicle", "number", "organization"]

entities = model.predict_entities(text, labels)

for entity in entities:
    print(entity["text"], "=>", entity["label"])
