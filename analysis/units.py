"""Unit texts keyed the way each prediction file keys its rows.

Used by the model-running scripts; needs texts/ from rebuild_texts.py.
"""
import common as C


def panel1():
    """(lang, length, unit_id) -> text."""
    return {(r['lang'], r['length'], r['unit_id']): r['text'] for r in C.texts('panel1_units')}


def panel2():
    """(panel, regime, corpus, lang, length, unit_id) -> text, for Panel 2 and
    the Panel 1 L20 cells, as the panel-2 prediction files key them."""
    out = {('panel2', r['regime'], r['corpus'], r['lang'], r['length'], r['unit_id']): r['text']
           for r in C.texts('panel2_units')}
    out.update({('panel1_ext', r['regime'], r['corpus'], r['lang'], r['length'], r['unit_id']): r['text']
                for r in C.texts('panel1_l20_units')})
    return out


def openlid_v3_inputs():
    """The 39,646 OpenLID-v3 units in the order of data/openlid_v3_predictions.csv."""
    p1 = panel1()
    p2 = {(k[1], k[3], k[4], k[5]): t for k, t in panel2().items()}
    nested = {(r['source'], r['length'], r['unit_id']): r['text'] for r in C.texts('nested_units')}
    reader = {r['uid']: r['text'] for r in C.texts('reader_sample')}
    out = []
    for r in C.read_csv('openlid_v3_predictions.csv'):
        if r['set'] == 'human':
            t = reader[r['unit_id']]
        elif r['set'] == 'nested':
            t = nested[(r['source'], r['length'], r['unit_id'])]
        elif r['regime'] == 'P1' and r['length'] != 'L20':
            t = p1[(r['lang'], r['length'], r['unit_id'])]
        else:
            t = p2[(r['regime'], r['lang'], r['length'], r['unit_id'])]
        out.append((r, t))
    return out
