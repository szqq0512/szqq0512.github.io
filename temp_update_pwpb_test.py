import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('temp_update_pwpb', Path('f:/OneDrive/文档/笔记/temp_update_pwpb.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_batch_suffix_mapping():
    assert mod.batch_to_suffix('第一批') == '一'
    assert mod.batch_to_suffix('第八批') == '八'


def test_batch_label_normalization():
    assert mod.normalize_batch_name('一') == '第一批'
    assert mod.normalize_batch_name('第八批') == '第八批'
