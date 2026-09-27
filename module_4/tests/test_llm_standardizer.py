"""Test the copied standardizer with fake inference and no model download."""
import importlib.util
import json
from pathlib import Path
import runpy
import sys
from types import ModuleType
from unittest.mock import Mock

from flask import Flask
import pytest

pytestmark = pytest.mark.analysis
SOURCE = Path(__file__).resolve().parents[1] / 'src' / 'llm_hosting' / 'app.py'


@pytest.fixture
def standardizer(monkeypatch):
    hub = ModuleType('huggingface_hub')
    hub.hf_hub_download = Mock(return_value='fake-model.gguf')
    llama = ModuleType('llama_cpp')
    llama.Llama = Mock()
    llama.Llama.return_value.create_chat_completion.return_value = {
        'choices': [{'message': {'content': '{}'}}]}
    monkeypatch.setitem(sys.modules, 'huggingface_hub', hub)
    monkeypatch.setitem(sys.modules, 'llama_cpp', llama)
    spec = importlib.util.spec_from_file_location('test_standardizer', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_model_initialization_is_cached(standardizer):
    first = standardizer._load_llm()
    assert standardizer._load_llm() is first
    standardizer.hf_hub_download.assert_called_once()
    standardizer.Llama.assert_called_once()


def test_missing_canonical_file(standardizer, tmp_path):
    assert standardizer._read_lines(str(tmp_path / 'missing.txt')) == []


@pytest.mark.parametrize('value, school, expected', [
    (' CS ', ' Example University ', ('CS', 'Example University')),
    ('CS at Example University', None, ('CS', 'Example University')),
    ('CS, specialized', None, ('CS, specialized', '')),
    ('CS', None, ('CS', '')),
])
def test_legacy_and_separate_names(standardizer, value, school, expected):
    assert standardizer._split_fallback(value, school) == expected


def test_canonical_apostrophes_and_ambiguity(standardizer):
    assert standardizer._canonical_name('queens', ["Queen's"]) == "Queen's"
    assert standardizer._canonical_name('queens', ["Queen's", 'Queens’']) == 'queens'
    assert standardizer._canonical_name('physics', ['Physics']) == 'Physics'


@pytest.mark.parametrize('left, right, expected', [
    ('math', 'meth', True), ('maths', 'math', True), ('math', 'maths', True),
    ('math', 'mathematics', False), ('math', 'math', False),
])
def test_one_character_corrections(standardizer, left, right, expected):
    assert standardizer._one_edit_apart(left, right) is expected


@pytest.mark.parametrize('source, proposed, expected', [
    ('Physicx', 'Physics', 'Physics'),
    ('Physics', 'Applied Physics', 'Physics'),
    ('Physics', 'Chemistry', 'Physics'),
    ('Unknown subject', 'Physics subject', 'Unknown subject'),
])
def test_program_corrections_preserve_meaning(standardizer, monkeypatch, source, proposed, expected):
    monkeypatch.setattr(standardizer, 'CANON_PROGS', ['Physics', 'Chemistry'])
    assert standardizer._validated_program(source, proposed) == expected


@pytest.mark.parametrize('name, expected', [
    ('Example University (EU)', 'Example University'),
    ('Unlisted Institute (UI)', 'Unlisted Institute'),
    ('Example University (123)', 'Example University (123)'),
    ('Example University (ZZ)', 'Example University (ZZ)'),
    ('Example University (EU/OU)', 'Example University (EU/OU)'),
    ('Unrelated College (EU)', 'Unrelated College (EU)'),
    ('Example University', 'Example University'),
])
def test_parenthetical_acronyms(standardizer, monkeypatch, name, expected):
    monkeypatch.setattr(standardizer, 'CANON_UNIS', ['Example University', 'Other University'])
    assert standardizer._expand_parenthetical_acronyms(name) == expected


@pytest.mark.parametrize('source, proposed, expected', [
    ('', 'Example University', 'Unknown'),
    ('Example University', 'Other University', 'Example University'),
    ('EU', 'Example University', 'Example University'),
    ('ZZ', 'Example University', 'ZZ'),
    ('Exampl University', 'Example University', 'Example University'),
    ('Unrelated College', 'Example University', 'Unrelated College'),
    ('Unrelated College', 'Unknown College', 'Unrelated College'),
    ('CUNY Branch', 'Example University', 'City University of New York Branch'),
    ('McG', 'Example University', 'McGill University'),
])
def test_university_corrections_require_evidence(standardizer, monkeypatch, source, proposed, expected):
    monkeypatch.setattr(standardizer, 'CANON_UNIS', ['Example University', 'Other University'])
    assert standardizer._validated_university(source, proposed) == expected


@pytest.mark.parametrize('content', [
    'not JSON', '{}', '[]',
    '{"standardized_program": 42, "standardized_university": null}',
    'Here: {"standardized_program": "Physics", "standardized_university": "McGill University"}',
])
def test_model_output_validation(standardizer, content):
    model = standardizer._load_llm()
    model.create_chat_completion.return_value = {'choices': [{'message': {'content': content}}]}
    result = standardizer._call_llm('Physics', 'McG')
    assert result == {'standardized_program': 'Physics', 'standardized_university': 'McGill University'}
    messages = model.create_chat_completion.call_args.kwargs['messages']
    assert json.loads(messages[-1]['content']) == {'program': 'Physics', 'school': 'McG'}


@pytest.mark.parametrize('row, expected', [
    ({'Program': 'CS', 'University': 'U'}, ('CS', 'U')),
    ({'program': 'CS', 'school': 'U'}, ('CS', 'U')),
    ({'program': 'CS'}, ('CS', None)),
])
def test_input_field_names(standardizer, row, expected):
    assert standardizer._row_names(row) == expected


def test_standardizer_routes(standardizer):
    client = standardizer.app.test_client()
    assert client.get('/').json == {'ok': True}
    assert client.post('/standardize', json={'bad': 'input'}).json == {'rows': []}
    response = client.post('/standardize', json={'rows': [{'Program': 'Physics', 'University': 'McG'}]})
    assert response.json['rows'][0]['llm-generated-university'] == 'McGill University'
    assert client.post('/standardize', json=[]).json == {'rows': []}


@pytest.mark.parametrize('mode', ['json', 'jsonl', 'append', 'stdout'])
def test_cli_output_formats(standardizer, tmp_path, capsys, mode):
    source = tmp_path / 'input.json'
    source.write_text(json.dumps([{'Program': 'Physics', 'University': 'McG'}]))
    destination = tmp_path / 'out.jsonl'
    if mode == 'append':
        destination.write_text('{"existing": true}\n')
    standardizer._cli_process_file(str(source),
        str(destination) if mode in ('jsonl', 'append') else None,
        mode == 'append', mode == 'stdout')
    if mode == 'stdout':
        rows = json.loads(capsys.readouterr().out)
    elif mode in ('jsonl', 'append'):
        rows = [json.loads(line) for line in destination.read_text().splitlines()]
        if mode == 'append':
            assert rows[0] == {'existing': True}
    else:
        rows = json.loads(Path(str(source) + '.normalized.json').read_text())
    assert rows[-1]['llm-generated-program'] == 'Physics'


def test_append_requires_jsonl(standardizer):
    with pytest.raises(ValueError, match='requires'):
        standardizer._cli_process_file('input.json', 'out.json', True, False)


def test_cli_entrypoint_file(standardizer, monkeypatch, tmp_path):
    source = tmp_path / 'input.json'
    source.write_text('[{"Program": "Physics"}]')
    monkeypatch.setattr(sys, 'argv', ['app.py', '--file', str(source)])
    runpy.run_path(str(SOURCE), run_name='__main__')
    rows = json.loads(Path(str(source) + '.normalized.json').read_text())
    assert rows[0]['llm-generated-university'] == 'Unknown'


def test_cli_entrypoint_server(standardizer, monkeypatch):
    run = Mock()
    monkeypatch.setattr(Flask, 'run', run)
    monkeypatch.setenv('PORT', '8010')
    monkeypatch.setattr(sys, 'argv', ['app.py', '--serve'])
    runpy.run_path(str(SOURCE), run_name='__main__')
    run.assert_called_once_with(host='0.0.0.0', port=8010, debug=False)
