function y = exppdf(x, mu)
  % Exponential pdf with mean mu, for Octave without the statistics package.
  y = exp(-x ./ mu) ./ mu;
  y(x < 0) = 0;
end
