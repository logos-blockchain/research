# Dev shell for the Lean proofs: Lean 4 (via elan) and Python (Cryptarchia
# certificate generator, differential tests). Keeps the toolchain in formal/.elan
# rather than ~/.elan. Use with `nix-shell` or direnv (`use nix`). nixpkgs is pinned.
let
  nixpkgs = fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/34ca302a9572963c02e385c056be37c85ff51b77.tar.gz";
    sha256 = "sha256-ym4BG18Pu2awiJIehla1Lo9xiB2QYRcCzW3SB74gEBY=";
  };
  pkgs = import nixpkgs { };
  python = pkgs.python3.withPackages (ps: with ps; [ numpy scipy ]);
in
pkgs.mkShell {
  packages = [ pkgs.elan pkgs.git pkgs.curl python ];
  # `toString` gives the absolute path without copying it into the store.
  shellHook = ''
    export ELAN_HOME="${toString ./.}/.elan"
    export PATH="$ELAN_HOME/bin:$PATH"
  '';
}
