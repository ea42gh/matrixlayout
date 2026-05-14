import os
import sys
import tempfile
from pathlib import Path

from matrixlayout.backsubst import backsubst_svg
from matrixlayout.ge import render_ge_svg


RENDER_OPTS = {"toolchain_name": "pdftex_dvisvgm", "crop": "tight", "padding": (2, 2, 2, 2)}


def main() -> int:
    default_outdir = Path(tempfile.gettempdir()) / "la" / "smoke" / "matrixlayout"
    outdir = os.environ.get("MATRIXLAYOUT_SMOKE_OUT", str(default_outdir))
    os.makedirs(outdir, exist_ok=True)
    print("matrixlayout smoke render ->", outdir)
    print("python:", sys.version.split()[0])
    try:
        import matrixlayout

        print("matrixlayout:", getattr(matrixlayout, "__version__", "unknown"))
    except Exception as exc:
        print("matrixlayout: import failed:", exc)

    matrices = [[None, [[1, 2], [3, 4]]], [[[1, 0], [0, 1]], [[1, 2], [3, 4]]]]
    ge_svg = render_ge_svg(matrices=matrices, output_dir=outdir, **RENDER_OPTS)
    print("ge svg length:", len(ge_svg))

    backsubst = backsubst_svg(
        system_txt=r"$x + 2y = 5,\quad y = 1$",
        cascade_txt=[r"$x + 2(1) = 5$", r"$x = 3$"],
        solution_txt=r"$(x,y) = (3,1)$",
        output_dir=outdir,
        **RENDER_OPTS,
    )
    print("backsubst svg length:", len(backsubst))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
