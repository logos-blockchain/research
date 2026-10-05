function y = poisspdf(k, lambda)
  % Poisson pmf with scalar expansion, for Octave without the statistics package.
  [k, lambda] = deal(k + 0 * lambda, lambda + 0 * k);
  y = exp(k .* log(lambda) - lambda - gammaln(k + 1));
  y(lambda == 0 & k == 0) = 1;
  y(lambda == 0 & k > 0) = 0;
end
