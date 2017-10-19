from Bio import AlignIO
from indra.util import read_unicode_csv, write_unicode_csv
from indra.databases import uniprot_client, hgnc_client
import subprocess
import re

peptide_file = 'sources/retrospective_ova_phospho_sort_common_gene_10057.txt'

# Problem: statements from reading and many databases give results in terms
# of HGNC identifiers, which are mapped to canonical Uniprot IDs.
# However, protein data is mapped to RefSeq identifiers, which often refer
# to isoforms that don't match the canonical Uniprot sequence. Sometimes
# they also can't mapped to any of the isoforms of the canonical entry in Uniprot
# due to differences in sequence.
#
# Solution: Get RefSeq IDs for all peptides and group by gene symbol. Then
# Get a Uniprot ID corresponding to each RefSeq ID (ideally an isoform of the
# reviewed entry, though it doesn't really matter which one since the point is
# just to get the sequence for running an alignment.
# Get the Uniprot ID associated with the gene symbol.
#
# Get sequences for all Uniprot IDs associated with a given gene symbol.
# Run sequences through sequence alignment.
#
# Then, for a given peptide, look up phosphorylated site; get upid for refseq
# id. If matches canonical up_id from HGNC, go straight to sequence
# Otherwise, map to sequence
# alignment; get corresponding site on reference sequence; get priors associated
# with that site on canonical protein.


def load_refseq_seqs():
    seq_file = 'sources/GRCh38_latest_protein.faa'
    seq_data = {}
    with open(seq_file, 'rt') as f:
        cur_seq_lines = []
        for line in f:
            if line.startswith('>'):
                if cur_seq_lines:
                    fasta_header = cur_seq_lines[0].strip()
                    sequence = ''.join([l.strip() for l in cur_seq_lines[1:]])
                    seq_data[rs_id] = (fasta_header, sequence)
                    cur_seq_lines = []
                # Now, update the Refseq ID
                rs_id = line[1:line.index(' ')]
            cur_seq_lines.append(line)
    return seq_data


def load_refseq_up_map():
    map_file = 'sources/uniprot-refseq-prot.tab'
    id_map = {}
    for row in read_unicode_csv(map_file, delimiter='\t', skiprows=1):
        up_id = row[0]
        rs_id = row[1]
        if rs_id not in id_map:
            id_map[rs_id] = [up_id]
        else:
            id_map[rs_id].append(up_id)
    return id_map


def get_genes_to_refseq_ids(problems):
    # First, collect refseq IDs for each gene
    gene_dict = {}
    for row in read_unicode_csv(peptide_file, delimiter='\t', skiprows=1):
        site_id = row[0]
        gene_sym, rem = site_id.split('.', maxsplit=1)
        refseq_id, site_info = rem.split(':')
        if gene_sym not in gene_dict:
            hgnc_id = hgnc_client.get_hgnc_id(gene_sym)
            if not hgnc_id:
                problems.add((refseq_id, 'invalid gene symbol'))
                continue
            up_id_main = hgnc_client.get_uniprot_id(hgnc_id)
            if not up_id_main or ', ' in up_id_main:
                problems.add((refseq_id, 'could not get Uniprot ID from HGNC'))
                continue
            gene_dict[gene_sym] = set([refseq_id])
        else:
            gene_dict[gene_sym].add(refseq_id)
    return gene_dict


def run_msa(gene_dict, rs_data, problems):
    # Next, get sequences and run alignments
    counter = 0
    matches = set()
    aln_data = {}
    for gene_sym, rs_ids in gene_dict.items():
        counter += 1
        if counter >= 20:
            break
        print("%s: %d of %d genes" % (gene_sym, counter, len(gene_dict)))
        fasta_lines = []
        # Get the main Uniprot sequence from the gene symbol
        hgnc_id = hgnc_client.get_hgnc_id(gene_sym)
        up_id_main = hgnc_client.get_uniprot_id(hgnc_id)
        up_sequence = uniprot_client.get_sequence(up_id_main)
        fasta_lines.append('>%s\n' % gene_sym)
        fasta_lines.append('%s\n' % up_sequence)

        # Now, iterate over the refseq ids and get the sequences
        seq_ids = []
        # The filenames to use if we do an alignment
        in_file = 'aln/in/%s.fasta' % gene_sym
        out_file = 'aln/out/%s.fasta' % gene_sym
        # Iterate over the Refseq IDs
        for rs_id in rs_ids:
            seq_info = rs_data.get(rs_id)
            if not seq_info:
                problems.add((rs_id, 'no sequence in Refseq'))
                continue
            seq_ids.append(rs_id)
            fasta_header, sequence = seq_info
            fasta_lines.append('>%s\n%s\n' % (rs_id, sequence))
            if sequence == up_sequence:
                aln_data[rs_id] = (gene_sym, True, None)
            else:
                aln_data[rs_id] = (gene_sym, False, out_file)
        if len(seq_ids) == 0:
            continue

        if len(seq_ids) == 1 and sequence == up_sequence:
            print("\tAll sequences match, no alignment needed.")
            continue
        else:
            # Write the fasta file
            with open(in_file, 'wt') as f:
                for line in fasta_lines:
                    f.write(line)
            # Run the sequence alignment
            print("\tRunning sequence alignment.")
            subprocess.call(['./clustal-omega-1.2.3-macosx', '-i', in_file,
                             '-o', out_file, '--force'])
    return aln_data


def _get_index_map(aln):
    ix_map = {}
    for aln_ix, aln_row in enumerate(aln):
        seq = aln_row.seq
        from_ix_map = []
        to_ix_map = []
        seq_ctr = 0
        for aa_ix, aa in enumerate(seq):
            if aa != '-':
                from_ix_map.append(aa_ix)
                to_ix_map.append(seq_ctr)
                seq_ctr += 1
            else:
                to_ix_map.append(None)
        ix_map[aln_row.id] = {'ix': aln_ix, 'from': from_ix_map,
                              'to': to_ix_map}
    return ix_map


def get_mapped_sites(aln_data, rs_data, num_res=7):
    # For each peptide, get info, then get flanking sequence and site on refseq
    results = []
    for row in read_unicode_csv(peptide_file, delimiter='\t', skiprows=1):
        site_id = row[0]
        gene_sym, rem = site_id.split('.', maxsplit=1)
        rs_id, site_info = rem.split(':')
        # Split out multiple site info
        rem = site_info
        site_list = []
        while rem:
            m = re.match('([sty][0-9]+)(.*)', rem)
            assert m.groups()[0]
            site_list.append(m.groups()[0])
            rem = m.groups()[1]
        # Get the main Uniprot sequence from the gene symbol
        #hgnc_id = hgnc_client.get_hgnc_id(gene_sym)
        #up_id_main = hgnc_client.get_uniprot_id(hgnc_id)
        #up_sequence = uniprot_client.get_sequence(up_id_main)
        flanks = []
        site_ixs = []
        mapped_sites = []
        for site in site_list:
            res = site[0].upper()
            pos = int(site[1:])
            try:
                seq_info = rs_data[rs_id]
            except KeyError:
                flanks.append('')
                site_ixs.append('')
                continue
            fasta_header, sequence = seq_info
            start_ix = pos - num_res - 1
            end_ix = pos + num_res
            site_ix = num_res
            if start_ix < 0:
                site_ix = num_res + start_ix
                start_ix = 0
            if end_ix > len(sequence):
                end_ix = len(sequence)
            flanks.append(sequence[start_ix:end_ix])
            site_ixs.append(str(site_ix))
            # Now get the alignment info
            aln_entry = aln_data.get(rs_id)
            # If no alignment info, don't try to get mapped sites
            if gene_sym == 'ABLIM1':
                import ipdb; ipdb.set_trace()
            if not aln_entry:
                mapped_sites.append('')
            else:
                (_, matched_seq, aln_file) = aln_entry
                # Sequence was a match, no need to map site, copy over site info
                if matched_seq:
                    mapped_sites.append(site)
                else:
                    # Read the alignment file
                    aln = AlignIO.read(aln_file, 'fasta')
                    ix_map = _get_index_map(aln)
                    aln_col_ix = ix_map[rs_id]['from'][pos-1]
                    rs_row_ix = ix_map[rs_id]['ix']
                    gene_row_ix = ix_map[gene_sym]['ix']
                    assert aln[rs_row_ix][aln_col_ix] == res
                    assert aln[gene_row_ix][aln_col_ix] == '-' or \
                           aln[gene_row_ix][aln_col_ix] == res
                    gene_pos = ix_map[gene_sym]['to'][aln_col_ix]
                    # This site is not present in the gene sequence
                    if gene_pos is None:
                        mapped_sites.append('')
                    else:
                        mapped_sites.append('%s%s' % (res, gene_pos+1))
        result = (site_id, rs_id, gene_sym,
                  ','.join([s.upper() for s in site_list]),
                  ','.join(flanks),
                  ','.join(site_ixs),
                  ','.join(mapped_sites))
        results.append(result)
    return results


if __name__ == '__main__':
    problems = set([])
    rs_data = load_refseq_seqs()
    gene_dict = get_genes_to_refseq_ids(problems)
    aln_data = run_msa(gene_dict, rs_data, problems)
    site_data = get_mapped_sites(aln_data, rs_data)

    #write_unicode_csv('seq_match_ids.txt', matches)
    #write_unicode_csv('problems.txt', problems)
    """


    id_map = load_refseq_up_map()

        site_id = row[0]
        print('%d: %s' % (row_ix, site_id))
        gene_sym, rem = site_id.split('.', maxsplit=1)
        refseq_id, site_info = rem.split(':')
        res = site_info[0].upper()
        pos = site_info[1:]
        try:
            pos = int(pos)
        except ValueError:
            print("\tSkipping double phosphosite %s" % site_id)
            continue

            if not sequence[pos-1] == res:
                print("\tInvalid site: %s" % site_id)
                continue

        # Check whether the sequences are identical!
        if sequence == up_sequence:
            print("\tSequences are identical, no need for sequence alignment!")
            continue

    # Now pick a gene and collect the UP IDs for getting sequences
    for gene in gene_dict.keys():
        up_main = gene_dict[gene]['main']
        refseq_up_ids = gene_dict[gene]['refseq']
        seq_id_list = []
        for refseq_up_id in refseq_up_ids:
            if refseq_up_id + '-1' == up_main:
                continue
            seq_id_list.append(refseq_up_id)
        if seq_id_list:
            seq_id_list.append(up_main)


    # Now collect, all uniprot IDs for each gene symbol, including the canonical
    # one


    write_unicode_csv('all_peptides_refseq.txt', ids)
    """

