function lc_lower(alpha, D, Alphabet, States, Ks, steps, out)
  % The original LCanalysis lower bound at one point, followed for `steps` phases. At 80 phases it
  % calls PoSMCConfirmLB unchanged; otherwise PoSMCConfirmLBSteps, the copy that
  % scripts/octave_reference.sh derives from it with the phase count as an argument. Appends
  % 'lb<steps>,K,value,seconds' to out as each value is computed.
  [Pa, PH, PD, PA, PAD] = PoSSlotPdf(alpha, D, Alphabet);
  St0 = PoWMCWarmupLB(PAD, Alphabet, States);
  for K = Ks
    t0 = tic;
    if steps == 80
      e = PoSMCConfirmLB(K, Pa, PH, PD, PA, PAD, St0, Alphabet, States);
    else
      e = PoSMCConfirmLBSteps(steps, K, Pa, PH, PD, PA, PAD, St0, Alphabet, States);
    end
    fid = fopen(out, 'a'); fprintf(fid, 'lb%d,%d,%.17g,%.1f\n', steps, K, e, toc(t0)); fclose(fid);
  end
end
