import pandas
from copy import deepcopy
from indra.databases import hgnc_client, uniprot_client
from indra.statements import Agent, Phosphorylation, ModCondition, Evidence

def read_phosphosite(fname):
    df = pandas.read_csv(fname, index_col=None)
    statements = []
    antibody_map = {}
    for _, row in df.iterrows():
        sub_upid = row['SUB_ID']
        if not pandas.isnull(sub_upid):
            sub_hgnc_symbol = uniprot_client.get_gene_name(sub_upid)
            sub_hgnc = hgnc_client.get_hgnc_id(sub_hgnc_symbol)
        else:
            sub_hgnc_symbol = row['SUB_GENE']
            sub_hgnc_id = hgnc_client.get_hgnc_id(sub_hgnc_symbol)
            sub_upid = hgnc_client.get_uniprot_id(sub_hgnc_id)
        sub = Agent(sub_hgnc_symbol,
                    db_refs={'UP': sub_upid,'HGNC': sub_hgnc})
        residue = row['Actual_site'][0]
        if len(row['Actual_site']) > 1:
            position = row['Actual_site'][1:]
        else:
            position = None

        sub_readout = deepcopy(sub)
        mc = ModCondition('phosphorylation', residue, position)
        sub_readout.mods = [mc]
        ps = row['phosphosite']
        if ps in antibody_map:
            found = False
            for p in antibody_map[ps]:
                if p.name == sub.name and p.mods[0].residue == residue and \
                    p.mods[0].position == position:
                    found = True
                    break
            if not found:
                antibody_map[ps].append(sub_readout)
        else:
            antibody_map[ps] = [sub_readout]

        kin_upid = row['KIN_ID']
        if not pandas.isnull(kin_upid):
            if not uniprot_client.is_human(kin_upid):
                print '%s non human' % kin_upid
                continue
            kin_hgnc_symbol = uniprot_client.get_gene_name(kin_upid)
            kin_hgnc = hgnc_client.get_hgnc_id(kin_hgnc_symbol)
        else:
            kin_hgnc_symbol = row['KINASE_GENE_SYMBOL']
            kin_hgnc_id = hgnc_client.get_hgnc_id(kin_hgnc_symbol)
            kin_upid = hgnc_client.get_uniprot_id(kin_hgnc_id)
        kin = Agent(kin_hgnc_symbol,
                    db_refs={'UP': kin_upid,'HGNC': kin_hgnc})

        ev = Evidence(source_api='phosphosite')
        st = Phosphorylation(kin, sub, residue, position, evidence = [ev])
        statements.append(st)
    return statements, antibody_map
