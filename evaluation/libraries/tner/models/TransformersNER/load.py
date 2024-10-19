from tner import TransformersNER

model = TransformersNER("tner/roberta-large-ontonotes5")
print(model.predict(["Jacob Collier is a Grammy awarded English artist from London"]))
