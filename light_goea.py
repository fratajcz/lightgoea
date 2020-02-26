import numpy as np
import pandas as pd
from scipy.stats import rankdata

def log_factorial(n):
    return np.log(np.arange(1,n+1)).sum()
def log_binomial(n,k):
    return log_factorial(n) - (log_factorial(k) + log_factorial(n-k))

def GOEA(target_genes,GENE_SETS,goterms=None,fdr_thresh=0.25,p_thresh=1e-3): 
    """Performs GO term Enrichment Analysis using the hypergeometric distribution.
    
    Parameters
    ----------
    target_genes - array-like
        List of target genes from which to find enriched GO terms.
    GENE_SETS - dictionary
        Dictionary where the keys are GO terms and the values are lists of genes associated with each GO term.
        Ex: {'GO:0000001': ['GENE_A','GENE_B'],
             'GO:0000002': ['GENE_A','GENE_C','GENE_D']}
        Make sure to include all available genes that have GO terms in your dataset.
    goterms - array-list, optional, default None
        If provided, only these GO terms will be tested.
    fdr_thresh - float, optional, default 0.25
        Filter out GO terms with FDR q value greater than this threshold.
    p_thresh - float, optional, default 1e-3
        Filter out GO terms with p value greater than this threshold.
        
    Returns:
    -------
    enriched_goterms - pandas.DataFrame
        A Pandas DataFrame of enriched GO terms with FDR q values, p values, and associated genes provided.
    """    
    
    all_genes = np.unique(np.concatenate(list(GENE_SETS.values())))
    all_genes = np.array(all_genes)
    
    if goterms is None:
        goterms = np.unique(list(GENE_SETS.keys()))
    else:
        goterms = goterms[np.in1d(goterms,np.unique(list(GENE_SETS.keys())))]
    
    _,ix = np.unique(target_genes,return_index=True)
    target_genes=target_genes[np.sort(ix)]
    target_genes = target_genes[np.in1d(target_genes,all_genes)]
    N = all_genes.size

    probs=[]
    probs_genes=[]
    counter=0
    
    for goterm in goterms:
        if counter%1000==0:
            print(counter)
        counter+=1
        gene_set = GENE_SETS[goterm]
        B = gene_set.size
        gene_set_in_target = gene_set[np.in1d(gene_set,target_genes)]
        b = gene_set_in_target.size        
        if b != 0:
            n = target_genes.size
            num_iter = min(n,B)
            rng = np.arange(b,num_iter+1)
            probs.append(sum([np.exp(log_binomial(n,i)+log_binomial(N-n,B-i) - log_binomial(N,B)) for i in rng]))
        else:
            probs.append(1.0)
        probs_genes.append(gene_set_in_target)
    probs = np.array(probs)    
    probs_genes = np.array(probs_genes)
    fdr_q_probs = probs.size*probs / rankdata(probs,method='ordinal')
    filt = np.logical_and(fdr_q_probs<fdr_thresh,probs<p_thresh)
    enriched_goterms = goterms[filt]
    p_values = probs[filt]
    fdr_q_probs = fdr_q_probs[filt]    
    probs_genes=probs_genes[filt]
    gns = []
    for i in probs_genes:
        gns.append(';'.join(i))
    gns = np.array(gns)
    enriched_goterms = pd.DataFrame(data=fdr_q_probs,index=enriched_goterms,columns=['fdr_q_value'])
    enriched_goterms['p_value'] = p_values
    enriched_goterms['genes'] = gns
    enriched_goterms = enriched_goterms.sort_values('p_value')   
    return enriched_goterms