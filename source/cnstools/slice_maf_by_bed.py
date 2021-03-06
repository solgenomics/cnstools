from filetype_classes import Bed6, Maf
from _utils import get_docstring_info
import sys

def parser(parser_add_func,name):
    p = parser_add_func(name,description=get_docstring_info(run))
    p.add_argument("maf_file", help=get_docstring_info(run,"maf_file"))
    p.add_argument("bed_file", help=get_docstring_info(run,"bed_file"))
    p.add_argument("ref_genome", help=get_docstring_info(run,"ref_genome"))
    p.add_argument("index_tag", help=get_docstring_info(run,"index_tag"))
    p.add_argument("-o", "--out_file", default=None, help=get_docstring_info(run,"out_file"))
    p.add_argument("-n", "--max_N_ratio", default=0.5,type=float, help=get_docstring_info(run,"max_N_ratio"))
    p.add_argument("-g", "--max_gap_ratio", default=0.5,type=float, help=get_docstring_info(run,"max_gap_ratio"))
    p.add_argument("-l", "--min_len", default=0.5,type=int, help=get_docstring_info(run,"min_len"))
    return p

def run(maf_file,bed_file,ref_genome,index_tag,out_file=None,max_N_ratio=0.5,max_gap_ratio=0.5,min_len=15):
    """Takes a maf file and a bed file which has index tags which identify which maf sequence it falls inside
    of and returns a maf file containing only the ranges specified in the bed file. To convert a untagged bed
    file to an appropriate format for this program, the maf can be converted to a bed file using maf_to_bed 
    and then intersected (using bedtools) with the bed file of your choosing.

    :param string maf_file: Path to maf file.
    :param string bed_file: Path to bed file.
    :param string ref_genome: Genome in maf file to base slicing locations on.
    :param string index_tag: Index tag in the bed file which contains the index of the maf region the original bed entry was created from.
    :param string out_file: Path to output (maf file). If not provided, program outputs to stdout.
    :param float max_N_ratio: Maximum ratio (0-1) of unidentified nucleotides in a sliced sequence for it to be returned.
    :param float max_gap_ratio: Maximum ratio (0-1) of gaps in a sliced sequence for it to be returned.
    :param int min_len: Minimum length of a sequence for it to be returned.
    :returns:  `None`
    """  
    bed = Bed6(file_name=bed_file)
    maf = Maf(file_name=maf_file) \
        .slice_with_bed(bed,ref_genome,index_tag,max_N_ratio,max_gap_ratio,min_len)
    if out_file:
        maf.save_file(out_file)
    else:
        sys.stdout.write("\n".join(maf.get_lines())+"\n")
        sys.stdout.flush()