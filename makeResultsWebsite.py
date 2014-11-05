#!/usr/bin/python
import json
import os
import shutil
import sys
import hotnet2
from hotnet2 import hnap, hnio, viz
from hotnet2.constants import VIZ_INDEX, VIZ_SUBNETWORKS

def get_parser():
    description = 'Creates a website showing the subnetworks output by HotNet2.'
    parser = hnap.HotNetArgParser(description=description, fromfile_prefix_chars='@')
    parser.add_argument('-r', '--results_files', nargs='+', required=True,
                        help='Paths to results.json files output by HotNet2')
    parser.add_argument('-ef', '--edge_file', required=True,
                        help='Path to TSV file listing edges of the interaction network, where\
                              each row contains the indices of two genes that are connected in the\
                              network.')
    parser.add_argument('-dsf', '--display_score_file',
                        help='Path to a tab seperated file contain a gene name in the first\
                              column and the display score for that gene in the second column\
                              of each line.')
    parser.add_argument('-nn', '--network_name', default='Network',
                        help='Display name for the interaction network.')
    parser.add_argument('-o', '--output_directory', required=True,
                        help='Output directory in which the website should be generated.')
    return parser

def run(args):
    subnetworks_file = '%s/viz_files/%s' % (hotnet2.__file__.rsplit('/', 1)[0], VIZ_SUBNETWORKS)

    # create output directory if doesn't exist; warn if it exists and is not empty
    outdir = args.output_directory
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    if len(os.listdir(outdir)) > 0:
        print("WARNING: Output directory is not empty. Any conflicting files will be overwritten. "
              "(Ctrl-c to cancel).")

    ks = set()
    output = dict(deltas=[], subnetworks=dict(), stats=dict())
    for results_file in args.results_files:
        results = json.load(open(results_file))
        ccs = results['components']
        gene2heat = json.load(open(results['parameters']['heat_file']))['heat']
        d_score = hnio.load_display_score_tsv(args.display_score_file) if args.display_score_file else None
        edges = hnio.load_ppi_edges(args.edge_file)
        gene2index = dict((gene, index) for index, gene \
                          in hnio.load_index(results['parameters']['infmat_index_file']).iteritems())
        delta = results['parameters']['delta']

        output['deltas'].append(delta)

        output["subnetworks"][delta] = []
        for cc in ccs:
            output['subnetworks'][delta].append(viz.get_component_json(cc, gene2heat, edges, gene2index,
                                                                args.network_name, d_score))

        output['stats'][delta] = results['statistics']
        for k in sorted(map(int, results['statistics'].keys())):
            ks.add(k)
            continue
            stats = results['statistics'][str(k)]
            output['stats'][delta].append( dict(k=k, expected=stats['expected'], observed=stats['observed'], pval=stats['pval']))

    output['ks'] = range(min(ks), max(ks)+1)
    with open('%s/subnetworks.json' % outdir, 'w') as out:
        json.dump(output, out, indent=4)

    shutil.copy(subnetworks_file, '%s/%s' % (outdir, VIZ_INDEX))

if __name__ == "__main__":
    run(get_parser().parse_args(sys.argv[1:]))
