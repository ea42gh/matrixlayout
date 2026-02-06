import os
import sys

from matrixlayout.ge import render_ge_svg


def main() -> int:
    outdir = os.environ.get("MATRIXLAYOUT_SMOKE_OUT", "/tmp/la/smoke/matrixlayout")
    os.makedirs(outdir, exist_ok=True)
    print("matrixlayout smoke render ->", outdir)
    print("python:", sys.version.split()[0])
    try:
        import matrixlayout

        print("matrixlayout:", getattr(matrixlayout, "__version__", "unknown"))
    except Exception as exc:
        print("matrixlayout: import failed:", exc)

    matrices = [[None, [[1, 2], [3, 4]]], [[[1, 0], [0, 1]], [[1, 2], [3, 4]]]]
    svg = render_ge_svg(matrices=matrices, output_dir=outdir)
    print("svg length:", len(svg))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
