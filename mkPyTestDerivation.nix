{
  lib,
  pkgs,
}:
{
  pname,
  suffix ? "test",
  version,
  pythonPkg ? pkgs.python3,
  buildPhaseUvCommand,
  installPhaseCommand ? "mkdir -p $out",
  ...
}:
  pkgs.stdenv.mkDerivation {
    pname = "${pname}-${suffix}";
    version = version;
    nativeBuildInputs = [
      pythonPkg
      pkgs.uv
    ];
    src = ./.;
    buildPhase = ''
      runHook preBuild
      python --version
      uv --version
      ${buildPhaseUvCommand}
      runHook postBuild
    '';
    configurePhase = ''
      runHook preConfigure
      # For UV's cache
      export XDG_CACHE_HOME="$TMPDIR/xdg-cache"
      runHook postConfigure
    '';
    installPhase = ''
      runHook preInstall
      ${installPhaseCommand}
      runHook postInstall
    '';
  }
