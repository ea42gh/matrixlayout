import os
import sys
import tempfile
from pathlib import Path

from matrixlayout.backsubst import backsubst_svg
from matrixlayout.eigproblem import render_eig_svg
from matrixlayout.ge import render_ge_svg
from matrixlayout.qr import render_qr_svg


RENDER_OPTS = {"toolchain_name": "pdftex_dvisvgm", "crop": "tight", "padding": (2, 2, 2, 2)}


def _check_svg(name: str, svg: str) -> None:
    if not isinstance(svg, str) or "<svg" not in svg:
        raise AssertionError(f"{name} did not produce SVG output")
    print(f"{name} svg length:", len(svg))


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
    _check_svg("ge", ge_svg)

    backsubst = backsubst_svg(
        system_txt=r"$x + 2y = 5,\quad y = 1$",
        cascade_txt=[r"$x + 2(1) = 5$", r"$x = 3$"],
        solution_txt=r"$(x,y) = (3,1)$",
        output_dir=outdir,
        **RENDER_OPTS,
    )
    _check_svg("backsubst", backsubst)

    qr_matrices = [
        [None, None, [[1, 2], [3, 4]], [[1, 0], [0, 1]]],
        [None, [[1, 0], [0, 1]], [[1, 2], [3, 4]], [[1, 0], [0, 1]]],
    ]
    qr_svg = render_qr_svg(matrices=qr_matrices, array_names=False, output_dir=outdir, **RENDER_OPTS)
    _check_svg("qr", qr_svg)

    eig_spec = {
        "lambda": [2, 3],
        "ma": [1, 1],
        "evecs": [
            [[1, 0]],
            [[0, 1]],
        ],
    }
    eig_svg = render_eig_svg(eig_spec, case="S", output_dir=outdir, **RENDER_OPTS)
    _check_svg("eig", eig_svg)

    svd_spec = {
        "lambda": [4, 1],
        "ma": [1, 1],
        "sigma": [2, 1],
        "evecs": [
            [[1, 0]],
            [[0, 1]],
        ],
        "qvecs": [
            [[1, 0]],
            [[0, 1]],
        ],
        "uvecs": [
            [[1, 0, 0]],
            [[0, 1, 0]],
            [[0, 0, 1]],
        ],
        "sz": (3, 2),
    }
    svd_svg = render_eig_svg(svd_spec, case="SVD", output_dir=outdir, **RENDER_OPTS)
    _check_svg("svd", svd_svg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
