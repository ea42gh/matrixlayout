from matrixlayout.formatting import make_decorator


def test_text_bg_decorator_uses_block_with_size():
    dec = make_decorator(text_bg="yellow!35", text_color="black")
    out = dec("1")
    assert r"\Block[draw=black,fill=yellow!35]{1-1}{1}" in out
