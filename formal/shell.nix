# Dev shell for the Lean proofs: Lean 4 (via elan) and Python (Cryptarchia
# certificate generator, differential tests). The toolchain goes in ELAN_HOME if set,
# else ~/.elan, shared across projects. Use with `nix-shell` or direnv (`use nix`).
# nixpkgs is pinned.
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
  shellHook = ''
    export ELAN_HOME="''${ELAN_HOME:-$HOME/.elan}"
    export PATH="$ELAN_HOME/bin:$PATH"
  '';
}
