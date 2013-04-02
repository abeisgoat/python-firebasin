verbose = False
def debug(*args):
    '''Print out data if we're in verbose mode'''
    if verbose:
        print args
