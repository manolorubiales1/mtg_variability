from flamapy.core.discover import DiscoverMetamodels
# from flamapy.core.models.ast import AST

# Ruta al directorio UVL
uvl_dir = 'C://Users//Usuario//Desktop//TFG-Project//UVL'

# Leer modelo UVL
dm = DiscoverMetamodels()
fm = dm.use_transformation_t2m("UVL/2ED-Unlimited Edition_variants.uvl", 'fm')


print(fm.get_mandatory_features())


