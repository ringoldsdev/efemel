from laygo import Pipeline


class TestLaygo:
  def test_laygo(self):
    p = Pipeline([1, 2, 3]).transform(lambda t: t.map(lambda x: x + 1)).to_list()
    assert p == [2, 3, 4], "Test failed: Output does not match expected result."
