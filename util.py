from scipy.stats import gmean

def geomean(x):
    return gmean(x.dropna())

def resolve_agg(agg):
    """Allow 'geomean' to be used as a string in .agg() calls."""
    if agg == "geomean":
        return geomean
    return agg

def compute_flops(M, K, N, include_bias=True):
    """
    Computes FLOPs for Z = Y + XW
    
    Parameters:
    M (int): Number of rows in X (batch size)
    K (int): Number of columns in X / rows in W (input features)
    N (int): Number of columns in W (output features)
    include_bias (bool): Whether the addition (+Y) is performed
    
    Returns:
    int: Total Floating Point Operations
    """
    # Standard MatMul FLOPs: 2 * M * N * K
    # (M * N * K) multiplications + (M * N * (K - 1)) additions
    matmul_flops = M * N * (2 * K - 1)
    
    # Addition FLOPs: M * N
    bias_flops = (M * N) if include_bias else 0
    
    total_flops = matmul_flops + bias_flops
    
    return total_flops