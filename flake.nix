{
  description = "Python environment";

  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = {
    nixpkgs,
    flake-utils,
    ...
  }:
    flake-utils.lib.eachDefaultSystem
    (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs.python312Packages; [
            pyopengl
            pyopengl-accelerate
            pygame-ce
            numba
            opensimplex
            numpy
            noise
          ];
        };
      }
    );
}
