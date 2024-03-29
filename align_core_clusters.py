import subprocess
import os
import sys
import pandas as pd
from Bio import AlignIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord


def get_alignment_dict():
    alignment_dict = {}
    for cluster in os.listdir("clusters"):
        with open(os.path.join("clusters", cluster, cluster + "_alignment-gb")) as alignment_file:
            alignment_dict[cluster] = AlignIO.read(alignment_file, "fasta")
    print("alignment dict")
    return alignment_dict


def align(mode):
    alignment_lengths_df = None
    alignment_dict = None
    root = "clusters"
    clusters_num = len(os.listdir(root))
    i = 1
    if mode == "filter":
        alignment_lengths_df = pd.DataFrame(columns=["cluster", "original", "edited"])
        alignment_dict = get_alignment_dict()

    for cluster in os.listdir(root):
        print("cluster: {} start".format(cluster))
        print("cluster num {} of {} start".format(i, clusters_num))
        if mode == "mafft":
            mafft_args = ["mafft", "--auto", str(os.path.join(root, cluster, cluster + ".fasta"))]
            with open(os.path.join(root, cluster, cluster + "_alignment"), "w") as aligned_file:
                subprocess.run(mafft_args, stdout=aligned_file)
        elif mode == "gblocks":
            gblocks_args = "~/Gblocks_0.91b/Gblocks " + str(os.path.join(root, cluster, cluster + "_alignment")) + " -t=d -b5=a"
            with open(os.path.join(root, cluster, cluster + "_alignment_gblocks"), "w") as gblocks_file:
                subprocess.run(gblocks_args, shell=True, stdout=gblocks_file)
        else:  # filter
            lengths = [int(cluster)]
            alignment = alignment_dict[cluster]
            original_length = alignment.get_alignment_length()
            lengths.append(original_length)
            edited_alignment = None
            for col_idx in range(original_length):
                col = alignment[:, col_idx:col_idx + 1]
                col_str = alignment[:, col_idx]
                if not all(c == col_str[0] for c in col_str):
                    if not edited_alignment:
                        edited_alignment = col
                    else:
                        edited_alignment += col
            edited_length = edited_alignment.get_alignment_length()
            lengths.append(edited_length)
            alignment_lengths_df.loc[len(alignment_lengths_df)] = lengths
            strain_idx = 0
            strains_num = len(os.listdir("data"))
            while strain_idx < strains_num:
                if len(edited_alignment) > strain_idx:
                    seq = edited_alignment[strain_idx]
                    seq_strain_idx = int(seq.id.split("|")[0])
                    if strain_idx < seq_strain_idx:
                        for padding_index in range(seq_strain_idx - strain_idx):
                            edited_alignment._records.insert(strain_idx + padding_index, SeqRecord(Seq(edited_length * "-"),
                                                                                       id="{} padding".format(strain_idx + padding_index)))
                        strain_idx += (seq_strain_idx - strain_idx + 1)
                        continue
                    strain_idx += 1
                else:
                    edited_alignment._records.append(SeqRecord(Seq(edited_length * "-"),
                                                               id="{} padding".format(strain_idx)))
                    strain_idx += 1
            with open(os.path.join(root, cluster, cluster + "_alignment_filtered"), "w") as filtered_file:
                AlignIO.write(edited_alignment, filtered_file, "fasta")
        print("cluster: {} done".format(cluster))
        print("cluster num {} of {} done".format(i, clusters_num))
        i += 1
    if mode == "filter":
        alignment_lengths_df.to_csv(os.path.join("tables", "stats_lengths.csv"))
    print("script done")


def main():
    align(str(sys.argv[1]))


if __name__ == "__main__":
    main()
