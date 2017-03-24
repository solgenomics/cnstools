import os
from ._utils import MultiTracker, make_dir, call_command
import file_handlers as fhs

def identify(out_folder,
             chrom_data,
             annotations,
             reference,
             coding_features,
             min_len,
             min_seg_score,
             max_conservation_gap,
             min_site_score,
             **kwargs):
    tracker = MultiTracker("Identifying CNS",len(chrom_data),estimate=False,style="fraction")
    tracker.auto_display(1)

    cmd_env = os.environ.copy()
    if bedtools_path!="":
            cmd_env["PATH"] = bedtools_path+":" + cmd_env["PATH"]

    make_dir(out_folder)

    reference_coding_bed, genome_gene_beds = create_genome_beds(out_folder, annotations, reference, coding_features, tracker)

    for chrom_name in chrom_data:
        chr_tracker = MultiTracker("Identifying CNS on "+chrom_name,1,estimate=False,style="noProg")
        chrom_out = os.path.join(out_folder,chrom_name+"_cns")
        make_dir(chrom_out)
        chrom_cns_identify(reference,
                           chrom_data,
                           chrom_name,
                           chrom_out,
                           reference_coding_bed,
                           min_len,
                           min_seg_score,
                           max_conservation_gap,
                           min_site_score,
                           chr_tracker)

def chrom_cns_identify(reference,
                       chrom_data,
                       chrom_name,
                       chrom_out,
                       reference_coding_bed,
                       min_len,
                       min_seg_score,
                       max_conservation_gap,
                       min_site_score,
                       tracker):

    chrom = chrom_data[chrom_name]
    

    #Format the MAF file to have a species identifier on the reference sequence
    chrom_seq_maf = os.path.join(chrom_out,"chrom_seqs_formatted.maf")
    orig_maf = fhs.maf.Handler(chrom['chrom_seq_maf'])
    chrom_seq_maf_handler = orig_maf.modify(_maf_format(reference),chrom_seq_maf,
                                            parent=tracker,tracker_name="Format aligned MAF file")

    #maf_to_bed
    info = "Convert aligned sequences to .bed:"
    header_print(info)
    ref_seq_bed = os.path.join(chrom_out,"ref_seq.bed")
    chrom_seq_maf_handler.to_bed(ref_seq_bed,genome_name=reference,index_tag="original_index",
                                 parent=tracker,tracker_name="Convert aligned to BED")

    #$bedtools subtract
    noncoding_bed_path = os.path.join(chrom_out,"aligned_noncoding_bed.bed")
    cmd = "bedtools subtract -a %s -b %s > %s" % (ref_seq_bed,reference_coding_bed,noncoding_bed_path)
    call_command([cmd],shell=True,env=cmd_env,parent=chr_tracker,tracker_name="Subtract coding from aligned")

    #wiggle_to_bed
    info = "Converting especially conserved regions in wiggle file to bed"
    header_print(info)
    best_conserved_bed = os.path.join(chrom_out,"best_conserved.bed")
    bcw = fhs.wig.Handler(chrom['chrom_conservation_wig'])
    bcw.to_bed(best_conserved_bed,
               genome=reference,
               min_seg_length=min_cns_length,
               min_seg_score=min_seg_score,
               max_conservation_gap=max_conservation_gap,
               min_site_score=min_site_score,
               parent=tracker,
               tracker_name="Convert conserved to BED")

    #filter_bed_with_wiggle
    cns_bed = os.path.join(chrom_out,"cns.bed")
    cmd = "bedtools intersect -a %s -b %s > %s" % (noncoding_bed_path,best_conserved_bed,cns_bed)
    call_command([cmd],shell=True,env=cmd_env,parent=chr_tracker,tracker_name="Intersect BEDs")

    #slice_maf_by_bed
    info = "Slice multi-alignment file based on identified conserved non-coding regions:"
    header_print(info)
    cns_maf = os.path.join(chrom_out,"cns.maf")
    chrom_seq_maf_handler.bed_intersect(bed           = cns_bed,
                                        path          = cns_maf,
                                        genome_name   = reference,
                                        index_tag     = "original_index",
                                        max_N_ratio   = max_cns_N_ratio,
                                        max_gap_ratio = max_cns_gap_ratio,
                                        min_len       = min_cns_length,
                                        parent        = tracker,
                                        tracker_name  = "Slice MAF entries by CNS BED")

    # #for iteration over genomes regardless of reference
    # all_genomes = config["genomes"]

    # #maf_to_bed
    # info = "Convert per-genome CNS regions to .bed:"
    # header_print(info)
    # chrom['genome_cns_beds_folder'] = os.path.join(chrom_out,"genome_cns_beds")
    # try:
    #     os.makedirs(chrom['genome_cns_beds_folder'])
    # except OSError:
    #     if not os.path.isdir(chrom['genome_cns_beds_folder']):
    #         raise
    # chrom['genome_cns_beds'] = {}
    # cns_maf = Maf(file_name=chrom['cns_maf'])
    # for genome in all_genomes:
    #     chrom['genome_cns_beds'][genome] = os.path.join(chrom['genome_cns_beds_folder'],genome+"_cns_"+chrom_name+".bed")
    #     bed = cns_maf.to_bed(genome_name=genome,index_tag="cns_maf_index")
    #     bed.save_file(chrom['genome_cns_beds'][genome])
    # del cns_maf


    # #$bedtools closest
    # info = "Find closest gene for each CNS region:"
    # header_print(info)
    # chrom['gene_proximity_beds_folder'] = os.path.join(chrom_out,"gene_proximity_beds")
    # try:
    #     os.makedirs(chrom['gene_proximity_beds_folder'])
    # except OSError:
    #     if not os.path.isdir(chrom['gene_proximity_beds_folder']):
    #         raise
    # chrom['gene_proximity_beds'] = {}
    # for genome in all_genomes:
    #     chrom['gene_proximity_beds'][genome] = os.path.join(chrom['gene_proximity_beds_folder'],genome+"_proxim.bed")
    #     cmd = "bedtools closest -D a -a %s -b %s > %s" % \
    #         (chrom['genome_cns_beds'][genome],
    #          config['genome_gene_beds'][genome],
    #          chrom['gene_proximity_beds'][genome])
    #     process = subprocess.Popen(cmd, shell=True)
    #     process.wait()

    # #maf_and_proxim_bed_to_cns
    # info = "Process proximity and maf files into .cns file:"
    # header_print(info)
    # chrom['results'] = os.path.join(chrom_out,"identified_CNSs.cns")
    # cns_proxim_beds = {genome:Bed13(chrom['gene_proximity_beds'][genome]) for genome in all_genomes}
    # Maf(file_name=chrom['cns_maf'])\
    #     .cns_from_proxim_beds(cns_proxim_beds,"cns_maf_index",prefix=chrom_name+".")\
    #     .save_file(chrom['results'])    

def _maf_format(reference):
    def func(entry):
        entry.sequences[0].src = reference+":"+entry.sequences[0].src
        return entry
    return func


def create_genome_beds(out_folder, annotations, reference, coding_features, tracker):
    gb_out = os.path.join(out_folder,"genome_beds")
    make_dir(gb_out)

    #gff3_to_bed
    ref_bed_tracker = tracker.subTracker("Extract reference CDS to .bed",1,estimate=False,style="noProg")
    reference_coding_bed = os.path.join(gb_out,"ref_coding.bed")
    ref_gff_file = fhs.gff3(reference_coding_bed)
    ref_coding_bed_file = ref_gff_file.to_bed(reference_coding_bed,
                                              type_list = coding_features, 
                                              sequence_prefix = reference+":")
    ref_bed_tracker.done()

    #gff3_to_bed
    ref_bed_tracker = tracker.subTracker("Extract genomes' genes to .bed",len(annotations),estimate=False,style="noProg")
    genome_gene_beds = {}
    for genome in annotations:
        genome_gene_beds[genome] = os.path.join(gb_out,genome+"_genes.bed")
        gff_file = fhs.gff3(annotations[genome])
        gff_file.to_bed(genome_gene_beds[genome],
                        type_list=['gene'],
                        genome=genome)
    return reference_coding_bed, genome_gene_beds

def config_identify(config_path): 
    '''Runs the `identify` function but loads arguements from a config file and uses the directory of that file as the working directory. It also saves a file called "identify.results.json" in that directory.'''
    with open(config_path) as config_file:
        config = json.loads(config_file.read())
    original_wd = os.getcwd()
    config_directory = os.path.dirname(os.path.abspath(config_path))
    os.chdir(config_directory)
    identify_results = identify(**config)
    # combine results dict with config and output as JSON
    results = identify_results.update(copy.deepcopy(config))
    results_path = os.path.join(config_directory,"identify.results.json")
    with open(results_path,"w") as results_file:
        json.dump(results,results_file,sort_keys=True,indent=4)
    os.chdir(original_wd)
    
_cl_entry = config_identify #function that should be run on command line entry to this subcommand
def _parser(parser_add_func,name):
    p = parser_add_func(name,description="Aligns a genome to a reference")
    p.add_argument("config_path", help="Absolute(!) path to config file")
    return p