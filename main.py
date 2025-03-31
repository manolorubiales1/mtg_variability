import os
import csv
import json
from typing import Any

from mtgsdk import Card
from mtgsdk import Set

from mtgsdk import Type
from mtgsdk import Supertype
from mtgsdk import Subtype
from mtgsdk import Changelog


MTG_VARIANTS_DIR = 'variants/'
MTG_CARD_COLLECTION_DIR = 'products/'
MTG_STATS_DIR = 'stats/'
MTG_GLOBAL_STATS_DIR = 'global-stats/'
CARD_HEADER = ['Name', 'CMC', 'Colors', 'Color identity', 'Supertypes',
               'Types', 'Subtypes', 'Rarity', 'Set', 'Power', 'Toughness', 'Loyalty', 'Text']

def extract_products():
    """Extract all cards information from the expansion of all time.

    Generates a .csv file for each expansion.
    """
    if not os.path.exists(MTG_CARD_COLLECTION_DIR):
        os.makedirs(MTG_CARD_COLLECTION_DIR)
    if not os.path.exists(MTG_VARIANTS_DIR):
        os.makedirs(MTG_VARIANTS_DIR)
    if not os.path.exists(MTG_STATS_DIR):
        os.makedirs(MTG_STATS_DIR)
    if not os.path.exists(MTG_GLOBAL_STATS_DIR):
        os.makedirs(MTG_GLOBAL_STATS_DIR)

    all_expansions = Set.all() # Lista de todas las expansiones
    total_expansions = len(all_expansions)
    print(f'#Expansions: {total_expansions}')
    
    # Initialize global stats outside the loop
    global_stats = {
        'Total Expansions': total_expansions,
        'Global Card Stats': {
            'Total Cards': 0, 
            'CMC': {}, 
            'Colors': {}, 
            'ColorIdentity': {}, 
            'Supertypes': {}, 
            'Types': {},
            'Subtypes': {}, 
            'Rarity': {}, 
            'Power': {}, 
            'Toughness': {}, 
            'Loyalty': {},
        }
    }
    
    for i, set_exp in enumerate(all_expansions): # Para todas las expansiones

        stats = {
        'Expansion': set_exp.name, 
        'Releasing year': set_exp.release_date, 
        'Number of cards': 0, 
        'CMC': {},
        'Colors': {}, 
        'ColorIdentity' : {}, 
        'Supertypes': {}, 
        'Types': {}, 
        'Subtypes': {}, 
        'Rarity': {},
        'Power': {}, 
        'Toughness': {}, 
        'Loyalty': {},
        }

        name = set_exp.name
        if '/' in name:
            name = name.split('/')[-1]
        name = name.replace(':', '_')
        filename = MTG_CARD_COLLECTION_DIR + set_exp.code + '-' + name + '.csv'
        variants_filename = MTG_VARIANTS_DIR + set_exp.code + '-' + name + '_variants.dat'
        stats_filename = MTG_STATS_DIR + set_exp.code + '-' + name + '_stats.json'
        
        cards_list = extract_cards_from_expansion(set_exp.code) # Saca la lista de cartas de cada expansión (según código de la misma)
        variants = extract_variants_from_cards(cards_list, stats) # Saca las variantes según la lista de no duplicadas

        print(f'({i}/{total_expansions})|-{set_exp.name}: {len(cards_list)}')

        # Write variants for each expansion
        with open(variants_filename, 'w', encoding='utf-8') as file:
            for k, v in variants.items():
                file.write(f'{k}: {v}\n')
        
        # Write products
        with open(filename, 'w', encoding='utf-8', newline='') as file:
            csv_writer = csv.writer(file, delimiter=',')
            csv_writer.writerow(CARD_HEADER)
            for card in cards_list:
                # Una línea por cada carta para cada expansión
                product_features = extract_product_features_from_card(card)
                csv_writer.writerow(product_features)

        # Write stats JSON for this expansion
        with open(stats_filename, 'w', encoding='utf-8') as file:
            json.dump(stats, file, indent=4, ensure_ascii=False)

        # Update global stats
        update_global_stats(global_stats['Global Card Stats'], stats)

    # Write global stats JSON to a single file in the global-stats directory
    with open(os.path.join(MTG_GLOBAL_STATS_DIR, 'global_stats.json'), 'w', encoding='utf-8') as file:
        json.dump(global_stats, file, indent=4, ensure_ascii=False)


def update_global_stats(global_stats, expansion_stats):
    """Update global stats with stats from a single expansion."""
    global_stats['Total Cards'] += expansion_stats['Number of cards']
    
    # Update each attribute's global count
    for attr in ['CMC', 'Colors', 'ColorIdentity', 'Supertypes', 'Types', 
                 'Subtypes', 'Rarity', 'Power', 'Toughness', 'Loyalty']:
        for key, value in expansion_stats[attr].items():
            global_stats[attr][key] = global_stats[attr].get(key, 0) + value


# Extrae todos los posibles valores de cada uno de los atributos de las cartas
def extract_variants_from_cards(cards: list[Card], stats) -> dict[str, list[Any]]:
    result = {}
    result['CMC'] = set()
    result['Colors'] = set()
    result['ColorIdentity'] = set()
    result['Supertypes'] = set()
    result['Types'] = set()
    result['Subtypes'] = set()
    result['Rarity'] = set()
    result['Power'] = set()
    result['Toughness'] = set()
    result['Loyalty'] = set()

    for card in cards:
        if card.cmc:
            result['CMC'].add(card.cmc)
            if 'CMC' not in stats or stats['CMC'] is None:
                stats['CMC'] = {card.cmc: 1}
            else:
                stats['CMC'][card.cmc] = stats['CMC'].get(card.cmc, 0) + 1
        
        # Colors tracking
        if card.colors:
            result['Colors'].update(card.colors)
            for color in card.colors:
                if 'Colors' not in stats or stats['Colors'] is None:
                    stats['Colors'] = {color: 1}
                else:
                    stats['Colors'][color] = stats['Colors'].get(color, 0) + 1
        
        # Color Identity tracking
        if card.color_identity:
            result['ColorIdentity'].update(card.color_identity)
            for color_id in card.color_identity:
                if 'ColorIdentity' not in stats or stats['ColorIdentity'] is None:
                    stats['ColorIdentity'] = {color_id: 1}
                else:
                    stats['ColorIdentity'][color_id] = stats['ColorIdentity'].get(color_id, 0) + 1
        
        # Supertypes tracking
        if card.supertypes:
            result['Supertypes'].update(card.supertypes)
            for supertype in card.supertypes:
                if 'Supertypes' not in stats or stats['Supertypes'] is None:
                    stats['Supertypes'] = {supertype: 1}
                else:
                    stats['Supertypes'][supertype] = stats['Supertypes'].get(supertype, 0) + 1
        
        # Types tracking
        if card.types:
            result['Types'].update(card.types)
            for card_type in card.types:
                stats['Types'][card_type] = stats['Types'].get(card_type, 0) + 1
        
        # Subtypes tracking
        if card.subtypes:
            result['Subtypes'].update(card.subtypes)
            for subtype in card.subtypes:
                if 'Subtypes' not in stats or stats['Subtypes'] is None:
                    stats['Subtypes'] = {subtype: 1}
                else:
                    stats['Subtypes'][subtype] = stats['Subtypes'].get(subtype, 0) + 1
        
        # Rarity tracking
        if card.rarity:
            result['Rarity'].add(card.rarity)
            stats['Rarity'][card.rarity] = stats['Rarity'].get(card.rarity, 0) + 1
        
        # Power tracking
        if card.power:
            result['Power'].add(card.power)
            if 'Power' not in stats or stats['Power'] is None:
                stats['Power'] = {card.power: 1}
            else:
                stats['Power'][card.power] = stats['Power'].get(card.power, 0) + 1
        
        # Toughness tracking
        if card.toughness:
            result['Toughness'].add(card.toughness)
            if 'Toughness' not in stats or stats['Toughness'] is None:
                stats['Toughness'] = {card.toughness: 1}
            else:
                stats['Toughness'][card.toughness] = stats['Toughness'].get(card.toughness, 0) + 1
        
        # Loyalty tracking
        if card.loyalty:
            result['Loyalty'].add(card.loyalty)
            if 'Loyalty' not in stats or stats['Loyalty'] is None:
                stats['Loyalty'] = {card.loyalty: 1}
            else:
                stats['Loyalty'][card.loyalty] = stats['Loyalty'].get(card.loyalty, 0) + 1
        stats['Number of cards']+=1
    return result


def extract_cards_from_expansion(set_exp_code: str) -> list[Card]:
    cards = Card.where(set=set_exp_code).all()
    # Remove duplicate cards
    no_duplicate_cards = set()
    for card in cards:
        # print(f'{card.type} -> {card.supertypes} -> {card.subtypes} -> {card.types}')

        # Si es tipo tierra AND supertipo no None AND supertipo=Basic
        if 'Land' in card.types and card.supertypes is not None and 'Basic' in card.supertypes:
            # No es duplicada
            no_duplicate_cards.add(card)
        # Si no existe ninguna carta con ese nombre en la lista de no duplicadas
        elif not any(c.name == card.name for c in no_duplicate_cards):
            no_duplicate_cards.add(card)
    # print(f'#Cards: {len(no_duplicate_cards)}')
    return no_duplicate_cards


def extract_product_features_from_card(card: Card) -> list[str]:
    result = list()
    result.append(card.name)
    result.append(card.cmc)
    result.append(card.colors)
    result.append(card.color_identity)
    result.append(card.supertypes)
    result.append(card.types)
    result.append(card.subtypes)
    result.append(card.rarity)
    result.append(card.set)
    result.append(card.power)
    result.append(card.toughness)
    result.append(card.loyalty)
    text = card.text.replace(
        '\n', '\\n') if card.text is not None else card.text
    result.append(text)
    return list(map(lambda x: str(x), result))


if __name__ == "__main__":
    extract_products()