function lc_points(alpha, D, Alphabet, States, Ks, out)
  % The original LCanalysis proof-of-stake routines, in the order PoSRandomWalk.m calls them, at
  % one point (honest share alpha, delay D in block intervals) for the depths Ks. Appends
  % 'bound,K,value,seconds' to out as each value is computed.
  [Pa, PH, PD, PA, PAD] = PoSSlotPdf(alpha, D, Alphabet);
  St0 = PoWMCWarmupUB(PAD, Alphabet, States);
  for K = Ks
    t0 = tic;
    St2 = PoSMCConfirmUB(K, Pa, PH, PD, PA, St0, Alphabet, States);
    e = PoWMCFinalUB(PAD, St2, Alphabet, States);
    fid = fopen(out, 'a'); fprintf(fid, 'ub,%d,%.17g,%.1f\n', K, e, toc(t0)); fclose(fid);
  end
  St0 = PoWMCWarmupLB(PAD, Alphabet, States);
  for K = Ks
    t0 = tic;
    e = PoSMCConfirmLB(K, Pa, PH, PD, PA, PAD, St0, Alphabet, States);
    fid = fopen(out, 'a'); fprintf(fid, 'lb,%d,%.17g,%.1f\n', K, e, toc(t0)); fclose(fid);
  end
end
