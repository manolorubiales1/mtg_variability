import os
import re

# Carpetas de entrada y salida
variant_dir = r"C:\Users\Usuario\Desktop\TFG-Project\variants"
output_dir = r"C:\Users\Usuario\Desktop\TFG-Project\UVL"
constraint_file = r"C:\Users\Usuario\Desktop\TFG-Project\mtg_fm_restrictions_v7.txt"  # Nuevo archivo

# Leer restricciones externas
def parse_constraints(path):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Parsear variantes desde .dat
def parse_variants(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    categories = {}
    for line in lines:
        if ":" in line:
            key, values = line.split(":", 1)
            value_set = eval(values.strip())
            categories[key.strip()] = sorted(str(v).replace("'", "").strip() for v in value_set)
    return categories

# Sanitizar nombres de características
def sanitize_feature_name(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name.replace("*", "star").replace(".", "_").replace(" ", "_"))

# Generar codificación binaria
def generate_binary_block(name, max_value):
    num_bits = max_value.bit_length()
    block = f"{name}\n    mandatory\n"
    for i in range(num_bits):
        block += f"        {name}_bit{i}\n"
    return block, [f"{name}_bit{i}" for i in range(num_bits)]

# Indentar bloques correctamente
def indent_block(block, level=1):
    indent = "    " * level
    return "".join(indent + line if line.strip() else line for line in block.splitlines(True))

# Traducir restricciones externas con binarización
def generate_binary_constraints(constraints):
    def encode_value_to_bits(var, value, bits=3):
        binary = f"{value:0{bits}b}"
        return "(" + " & ".join(
            f"{var}_bit{i}" if bit == "1" else f"!{var}_bit{i}"
            for i, bit in enumerate(reversed(binary))
        ) + ")"

    updated_constraints = []
    for line in constraints:
        modified = line

        # Sustituir CMC_0 a CMC_7 por codificación binaria
        for n in range(8):
            token = f"CMC_{n}"
            if token in modified:
                modified = modified.replace(token, encode_value_to_bits("CMC", n, bits=3))

        # Reemplazar Power y Toughness por expresión booleana OR de sus bits
        for attr in ["Power", "Toughness"]:
            pattern = re.compile(rf'\b{attr}\b')
            if pattern.search(modified):
                bits_expr = " | ".join(f"{attr}_bit{i}" for i in range(4))
                modified = pattern.sub(f"({bits_expr})", modified)

        updated_constraints.append(modified)

    return updated_constraints

# Generar UVL correcto
def generate_uvl(categories, constraints, root_name):
    binary_attrs = {'CMC': 7, 'Power': 8, 'Toughness': 8}
    single_valued = {'CMC', 'Rarity', 'Power', 'Toughness', 'Loyalty'}
    mandatory = {'CMC', 'Types', 'Rarity'}

    uvl = "features\n"
    uvl += f"    MTG_{sanitize_feature_name(root_name)}\n"

    # Añadir automáticamente CMC_0 si hay tierras
    if 'Types' in categories and 'Land' in categories['Types']:
        if 'CMC' not in categories:
            categories['CMC'] = []
        if '0' not in categories['CMC']:
            categories['CMC'].append('0')

    # Bloques obligatorios
    mand_blocks = ""
    for cat in mandatory:
        if cat in binary_attrs:
            block, _ = generate_binary_block(cat, binary_attrs[cat])
            mand_blocks += indent_block(block, level=3)
        elif cat in categories and categories[cat]:
            group_type = "alternative" if cat in single_valued else "or"
            block = f"{cat}\n    {group_type}\n"
            for v in categories[cat]:
                block += f"        {sanitize_feature_name(cat)}_{sanitize_feature_name(v)}\n"
            mand_blocks += indent_block(block, level=3)
    if mand_blocks:
        uvl += "        mandatory\n" + mand_blocks

    # Bloques opcionales
    optional_cats = [cat for cat in categories if cat not in mandatory and categories[cat]]
    if optional_cats:
        uvl += "        optional\n"
        for cat in optional_cats:
            group_type = "alternative" if cat in single_valued else "or"
            block = f"{cat}\n    {group_type}\n"
            for v in categories[cat]:
                block += f"        {sanitize_feature_name(cat)}_{sanitize_feature_name(v)}\n"
            uvl += indent_block(block, level=3)

    # Agregar restricciones comunes
    if constraints:
        uvl += "\nconstraints\n"
        for c in constraints:
            uvl += f"    {c}\n"

    return uvl

# Función principal
def main():
    files = [f for f in os.listdir(variant_dir) if f.endswith(".dat")]
    constraints = parse_constraints(constraint_file)
    constraints = generate_binary_constraints(constraints)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    total = len(files)
    for idx, filename in enumerate(files, start=1):
        full_path = os.path.join(variant_dir, filename)
        base_name = os.path.splitext(filename)[0]
        output_path = os.path.join(output_dir, f"{base_name}.uvl")

        try:
            categories = parse_variants(full_path)
            uvl_text = generate_uvl(categories, constraints, base_name)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(uvl_text)

            print(f"({idx}/{total}) UVL generado correctamente: {base_name}.uvl")
        except Exception as e:
            print(f"({idx}/{total}) Error en {filename}: {e}")

if __name__ == "__main__":
    main()
