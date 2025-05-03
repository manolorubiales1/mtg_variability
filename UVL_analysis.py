from flamapy.interfaces.python.flamapy_feature_model import FLAMAFeatureModel
fm = FLAMAFeatureModel("./UVL/2ED-Unlimited Edition_variants.uvl")

valido = fm.satisfiable()
print(valido)  # True si el modelo tiene al menos una configuracion válida
