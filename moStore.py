class ctrctMOStore():
    def __init__(self, moDir):

        # self.gbl_vzBrCP = moDir.lookupByClass('vz.BrCP')
        self.gbl_fvRsProv = moDir.lookupByClass('fv.RsProv')
        self.gbl_fvRsCons = moDir.lookupByClass('fv.RsCons')
        self.gbl_vzSubj = moDir.lookupByClass('vz.Subj')
        self.gbl_vzRsSubjFiltAtt = moDir.lookupByClass('vz.RsSubjFiltAtt')
        self.gbl_fvAEPg = moDir.lookupByClass('fv.AEPg')
        self.gbl_fvRsCtx = moDir.lookupByClass('fv.RsCtx')
        self.gbl_fvRsBd = moDir.lookupByClass('fv.RsBd')

