# Dev shell for the formal specification: Lean 4 (via elan) and Python (certificate
# generator, differential tests). Use `nix-shell` from this directory.
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
  # Keep the Lean toolchain inside this directory (formal/.elan), not ~/.elan.
  shellHook = ''
    export ELAN_HOME="$PWD/.elan"
    export PATH="$ELAN_HOME/bin:$PATH"
  '';
}
