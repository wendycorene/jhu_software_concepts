"""Verify labels and percentage formatting on the rendered analysis page."""

from decimal import Decimal
import re
from unittest.mock import Mock

from bs4 import BeautifulSoup
import pytest

import app as app_module


pytestmark = pytest.mark.analysis


@pytest.fixture
def render_analysis(monkeypatch):
    """Render real templates and formatting with supplied query results."""
    manager = Mock(state='idle', message='Ready.')
    manager.running.return_value = False
    application = app_module.create_app(manager=manager)
    application.config['TESTING'] = True

    def render(results):
        monkeypatch.setattr(app_module, 'run_queries', lambda: results)
        response = application.test_client().get('/analysis')
        assert response.status_code == 200
        page = BeautifulSoup(response.data, 'html.parser')
        assert page.select_one('[role="alert"]') is None
        return page

    return render


def test_every_analysis_item_has_an_answer_label(render_analysis):
    results = {
        1: [(42,)],
        2: [(39.284,)],
        3: [(3.75, 160, 155, 4.5)],
        4: [(3.8,)],
        5: [(60.126,)],
        6: [(3.9,)],
        7: [(8,)],
        8: [(10,)],
        9: [(12,)],
        10: [('Computer Science', 165.5, 20)],
        11: [('Example University', 7)],
    }
    page = render_analysis(results)
    cards = page.select('.grid article')
    assert len(cards) == 11
    for card in cards:
        answers = card.select('.answer')
        assert len(answers) == 1
        label, separator, value = answers[0].get_text(strip=True).partition('Answer: ')
        assert label == ''
        assert separator == 'Answer: '
        assert value.strip()


@pytest.mark.parametrize('question', [2, 5])
@pytest.mark.parametrize('value, expected', [
    (39.284, '39.28%'),
    (39.286, '39.29%'),
    (7.5, '7.50%'),
    (0, '0.00%'),
    (100, '100.00%'),
    (Decimal('99.999'), '100.00%'),
])
def test_percentages_have_two_decimals(render_analysis, question, value, expected):
    page = render_analysis({question: [(value,)]})
    answer = page.select_one('.answer').get_text(strip=True)
    assert answer == f'Answer: {expected}'
    assert re.fullmatch(r'Answer: \d+\.\d{2}%', answer)


@pytest.mark.parametrize('question', [2, 5])
def test_missing_percentage_is_not_reported_as_zero(render_analysis, question):
    page = render_analysis({question: [(None,)]})
    assert page.select_one('.answer').get_text(strip=True) == 'Answer: N/A'
