"""Generate both assignment PDFs from the current PostgreSQL analysis."""
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted, PageBreak
from query_data import run_queries, QUERIES
from presentation import QUESTIONS, EXPLANATIONS, format_result
import textwrap

ROOT = Path(__file__).parent
STYLES = getSampleStyleSheet()
STYLES['BodyText'].spaceAfter = 10
STYLES['BodyText'].leading = 15
STYLES['Code'].fontSize = 8
STYLES['Code'].leading = 11


def paragraph(text, style='BodyText'):
    return Paragraph(escape(text), STYLES[style])


def build_reports():
    results = run_queries()
    flow = [paragraph('Grad Cafe: SQL analysis', 'Title'),
            paragraph('Module 3 | Wendy Eloe'),
            paragraph('Snapshot: 32,400 Module 2 submissions. Results describe entries, not unique people. '
                      'Scores use a 4-point GPA scale and current GRE component scales. Zero placeholders, '
                      'missing values, and values outside those scales become NULL. Each average excludes '
                      'only its own missing metric. Percentages with no denominator display N/A.')]
    for number, sql in QUERIES.items():
        if number > 1:
            flow.append(PageBreak())
        flow += [paragraph(f'Question {number}', 'Heading1'), paragraph(QUESTIONS[number]),
                 paragraph('Result: ' + format_result(number, results[number], results), 'Heading2'),
                 paragraph(EXPLANATIONS[number])]
        if number == 9:
            flow.append(paragraph('Both counts are 30 in this snapshot, giving a difference of +0. '
                                  'The normalization did not change the total number of matching entries. '
                                  'Equal counts alone do not prove identical membership or accurate names. '
                                  'In other snapshots, expanded acronyms, corrected spellings, or mistaken '
                                  'LLM standardizations could add or remove matches.'))
        flow.append(paragraph('Executable SQL', 'Heading2'))
        wrapped = '\n'.join('\n'.join(textwrap.wrap(line, width=88, replace_whitespace=False))
                            for line in sql.splitlines())
        flow.append(Preformatted(wrapped + ';', STYLES['Code']))
        if number == 9:
            flow.append(paragraph('The original-field count uses the Question 8 SQL. The signed difference is the Question 9 result minus the Question 8 result.'))
    SimpleDocTemplate(str(ROOT / 'query_results.pdf')).build(flow)
    gpa = format_result(3, results[3], results)
    reflection = [
        'Grad Cafe is a voluntary collection of anonymous submissions, not a random sample of graduate '
        'applicants. People who know about the site, participate in online admissions discussions, and '
        'choose to disclose their outcomes may differ from those who never post. Applicants with unusually '
        'positive, negative, or surprising outcomes may have more reason to submit a result. Programs, '
        'universities, countries, and degree types can therefore be overrepresented or absent, and one '
        'person can post several applications. In this snapshot, 47.23% of Fall 2025 entries are acceptances; '
        'this is the percentage of these recorded entries, not a university acceptance rate or a prediction '
        'for an individual applicant. The Fall 2025 subset is also small compared with Fall 2026 because '
        'the saved pages emphasize recent submissions. Comparing those terms without accounting for '
        'collection coverage and decision timing would confound reporting behavior with admissions outcomes.',
        'Missing and inconsistent information further limits interpretation. GPA averages include only '
        'entries with usable scores under the documented cleaning policy and therefore represent '
        'that reporting subset. Applicants with stronger scores may be more willing to disclose them, and '
        'test-optional programs may attract applicants who report no GRE score at all. The observed score '
        f'summary is {gpa}. These averages do not establish the averages of all graduate applicants. '
        'The source contains zero placeholders and some GRE values resembling combined totals; treating '
        'these as component scores would substantially distort the result. Excluding incompatible scales '
        'avoids that distortion but can disproportionately exclude international GPA formats and cannot '
        'recover the missing information. Anonymous entries cannot be independently verified, source URLs '
        'prevent duplicate records rather than repeated people, and inconsistent names or LLM normalization '
        'can change university matching. The equal original and LLM counts of 30 are therefore a consistency '
        'check, not evidence that every classification or self-reported result is correct.'
    ]
    SimpleDocTemplate(str(ROOT / 'limitations.pdf')).build(
        [paragraph('Limitations of self-reported admissions data', 'Title'), Spacer(1, 12)] +
        [paragraph(p) for p in reflection])
    print('Created query_results.pdf and limitations.pdf')

if __name__ == '__main__':
    build_reports()
