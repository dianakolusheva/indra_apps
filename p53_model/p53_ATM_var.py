# exported from PySB model 'p53_ATM_var'

from pysb import Model, Monomer, Parameter, Expression, Compartment, Rule, Observable, Initial, MatchOnce, Annotation, ANY, WILD

Model()

Monomer(u'HIPK2')
Monomer(u'MDM2')
Monomer(u'ATM', [u'phospho'], {u'phospho': [u'u', u'p']})
Monomer(u'TP53', [u'ub', u'activity'], {u'activity': [u'inactive', u'active'], u'ub': [u'n', u'y']})
Monomer(u'PPM1D', [u'activity'], {u'activity': [u'inactive', u'active']})

Parameter(u'kf_aa_phosphorylation_1', 5e-06)
Parameter(u'kf_pa_dephosphorylation_1', 0.0001)
Parameter(u'kf_mt_ubiquitination_1', 1e-06)
Parameter(u'kf_at_act_1', 1e-06)
Parameter(u'kf_tp_act_1', 1e-06)
Parameter(u'kf_pt_act_1', 1e-05)
Parameter(u'kf_hp_act_1', 1e-06)
Parameter(u'kf_m_deg_1', 0.8)
Parameter(u'kf_t_deg_1', 2e-05)
Parameter(u'kf_t_synth_1', 0.002)
Parameter(u'kf_tm_synth_1', 0.2)
Parameter(u'HIPK2_0', 100.0)
Parameter(u'MDM2_0', 0)
Parameter(u'ATM_0', 100.0)
Parameter(u'TP53_0', 100.0)
Parameter(u'PPM1D_0', 100.0)
Parameter(u'ATMa_0', 1.0)

Observable('p53_active', TP53(activity=u'active'))
Observable('atm_active', ATM(phospho=u'p'))

Rule(u'ATM_phosphorylation_ATM_phospho', ATM(phospho=(u'p', WILD)) + ATM(phospho=u'u') >> ATM(phospho=(u'p', WILD)) + ATM(phospho=u'p'), kf_aa_phosphorylation_1)
Rule(u'PPM1D_dephosphorylation_ATM_phospho', PPM1D(activity=u'active') + ATM(phospho=u'p') >> PPM1D(activity=u'active') + ATM(phospho=u'u'), kf_pa_dephosphorylation_1)
Rule(u'MDM2_ubiquitination_TP53_ub', MDM2() + TP53(ub=u'n') >> MDM2() + TP53(ub=u'y'), kf_mt_ubiquitination_1)
Rule(u'ATM_activates_TP53_activity', ATM(phospho=(u'p', WILD)) + TP53(activity=u'inactive') >> ATM(phospho=(u'p', WILD)) + TP53(activity=u'active'), kf_at_act_1)
Rule(u'TP53_activates_PPM1D_activity', TP53(activity=u'active') + PPM1D(activity=u'inactive') >> TP53(activity=u'active') + PPM1D(activity=u'active'), kf_tp_act_1)
Rule(u'PPM1D_deactivates_TP53_activity', PPM1D(activity=u'active') + TP53(activity=u'active') >> PPM1D(activity=u'active') + TP53(activity=u'inactive'), kf_pt_act_1)
Rule(u'HIPK2_deactivates_PPM1D_activity', HIPK2() + PPM1D(activity=u'active') >> HIPK2() + PPM1D(activity=u'inactive'), kf_hp_act_1)
Rule(u'MDM2_degraded', MDM2() >> None, kf_m_deg_1)
Rule(u'TP53_ub_degraded', TP53(ub=(u'y', WILD)) >> None, kf_t_deg_1)
Rule(u'TP53_synthesized', None >> TP53(ub=u'n', activity=u'inactive'), kf_t_synth_1)
Rule(u'TP53_synthesizes_MDM2', TP53(activity=u'active') >> MDM2() + TP53(activity=u'active'), kf_tm_synth_1)

Initial(HIPK2(), HIPK2_0)
Initial(MDM2(), MDM2_0)
Initial(ATM(phospho=u'u'), ATM_0)
Initial(TP53(ub=u'n', activity=u'inactive'), TP53_0)
Initial(PPM1D(activity=u'inactive'), PPM1D_0)
Initial(ATM(phospho=u'p'), ATMa_0)

Annotation(HIPK2, u'http://identifiers.org/uniprot/Q9H2X6', u'is')
Annotation(HIPK2, u'http://identifiers.org/hgnc/HGNC:14402', u'is')
Annotation(MDM2, u'http://identifiers.org/uniprot/Q00987', u'is')
Annotation(MDM2, u'http://identifiers.org/hgnc/HGNC:6973', u'is')
Annotation(ATM, u'http://identifiers.org/uniprot/Q13315', u'is')
Annotation(ATM, u'http://identifiers.org/hgnc/HGNC:795', u'is')
Annotation(TP53, u'http://identifiers.org/hgnc/HGNC:11998', u'is')
Annotation(TP53, u'http://identifiers.org/uniprot/P04637', u'is')
Annotation(PPM1D, u'http://identifiers.org/hgnc/HGNC:9277', u'is')
Annotation(PPM1D, u'http://identifiers.org/uniprot/O15297', u'is')
Annotation(ATM_phosphorylation_ATM_phospho, u'ATM', u'rule_has_subject')
Annotation(ATM_phosphorylation_ATM_phospho, u'ATM', u'rule_has_object')
Annotation(PPM1D_dephosphorylation_ATM_phospho, u'PPM1D', u'rule_has_subject')
Annotation(PPM1D_dephosphorylation_ATM_phospho, u'ATM', u'rule_has_object')
Annotation(MDM2_ubiquitination_TP53_ub, u'MDM2', u'rule_has_subject')
Annotation(MDM2_ubiquitination_TP53_ub, u'TP53', u'rule_has_object')
Annotation(ATM_activates_TP53_activity, u'ATM', u'rule_has_subject')
Annotation(ATM_activates_TP53_activity, u'TP53', u'rule_has_object')
Annotation(TP53_activates_PPM1D_activity, u'TP53', u'rule_has_subject')
Annotation(TP53_activates_PPM1D_activity, u'PPM1D', u'rule_has_object')
Annotation(PPM1D_deactivates_TP53_activity, u'PPM1D', u'rule_has_subject')
Annotation(PPM1D_deactivates_TP53_activity, u'TP53', u'rule_has_object')
Annotation(HIPK2_deactivates_PPM1D_activity, u'HIPK2', u'rule_has_subject')
Annotation(HIPK2_deactivates_PPM1D_activity, u'PPM1D', u'rule_has_object')

